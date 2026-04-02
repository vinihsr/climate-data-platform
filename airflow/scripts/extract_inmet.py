import os 
import boto3
import pandas as pd
import requests 
from datetime import datetime

def download_inmet_data(region="S"):
    bucket_name = os.getenv("BRONZE_BUCKET")

    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://apitempo.inmet.gov.br/estacoes/T"
    
    print(f"Buscando dados INMET para data: {url.count}...")
    response = requests.get(url, timeout=30)
    
    if response.status_code != 200:
        print(f"Erro na API: {response.status_code} - {response.text}")
        print("Usando dado de fallback para validar pipeline...")
        df = pd.DataFrame({"msg": ["API INMET indisponível"], "data": [today]})
    else:
        data = response.json()
        df = pd.DataFrame(data)

    now = datetime.now()
    partition_path = f"source=inmet/year={now.year}/month={now.strftime('%m')}"
    file_name = f"inmet_{region}_{now.strftime('%Y%m%d_%H%M%S')}.parquet"

    local_path = f"/tmp/{file_name}"
    df.to_parquet(local_path, index=False)

    s3_client = boto3.client("s3")
    s3_key = f"bronze/{partition_path}/{file_name}"

    print(f"fazendo upload {bucket_name}/{s3_key}")
    s3_client.upload_file(local_path, bucket_name, s3_key)
    os.remove(local_path)
    return s3_key