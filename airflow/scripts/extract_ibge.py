import os 
import boto3
import pandas as pd
import requests 
from datetime import datetime, timezone
from botocore.exceptions import ClientError

def download_ibge_data():
    bucket_name = os.getenv("BRONZE_BUCKET")
    s3_client = boto3.client("s3")
    
    partition_path = "ibge/current"
    file_name = "ibge_data.parquet"
    s3_key = f"{partition_path}/{file_name}"

    try:
        metadata = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        last_modified = metadata['LastModified']
        age_days = (datetime.now(timezone.utc) - last_modified).days
        
        if age_days < 30:
            print(f"Skipping IBGE Extraction: Cache is current. File is only {age_days} days old.")
            return 0  
        print(f"IBGE file is {age_days} days old. Refreshing lookup data...")
        
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("IBGE lookup file not found on S3. Fetching initial reference dataset...")
        else:
            raise e

    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    print("Requesting lookup tables from IBGE API...")
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

        local_path = f"/tmp/{file_name}"
        df.to_parquet(local_path, index=False)
        
        print(f"Uploading fresh IBGE table snapshot to S3: {s3_key}")
        s3_client.upload_file(local_path, bucket_name, s3_key)
        
        if os.path.exists(local_path):
            os.remove(local_path)
            
        return 1  
    else:
        raise Exception(f"IBGE API returned status code {response.status_code}")