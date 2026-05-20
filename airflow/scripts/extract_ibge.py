import os 
import boto3
import pandas as pd
import requests 

def download_ibge_data():
    bucket_name = os.getenv("BRONZE_BUCKET")
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    response = requests.get(url, timeout=30)

    if response.status_code == 200:
        data = response.json()
        df_raw = pd.json_normalize(data)

        df = df_raw[[
            'id', 'nome', 'microrregiao.mesorregiao.UF.sigla', 
            'microrregiao.mesorregiao.UF.nome', 'microrregiao.mesorregiao.UF.regiao.nome'
        ]].rename(columns={
            'id': 'codigo_ibge', 'nome': 'nome_municipio',
            'microrregiao.mesorregiao.UF.sigla': 'uf_sigla',
            'microrregiao.mesorregiao.UF.nome': 'uf_nome',
            'microrregiao.mesorregiao.UF.regiao.nome': 'regiao_nome'
        })

        df['nome_municipio_search'] = df['nome_municipio'].str.upper().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

        partition_path = f"ibge/current"
        file_name = f"ibge_data.parquet"
        local_path = f"/tmp/{file_name}"

        df.to_parquet(local_path, index=False)
        
        s3_client = boto3.client("s3")
        s3_key = f"{partition_path}/{file_name}"
        
        s3_client.upload_file(local_path, bucket_name, s3_key)
        os.remove(local_path)
        return s3_key