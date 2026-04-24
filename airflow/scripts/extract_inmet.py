import os 
import boto3
import pandas as pd
import requests 
from datetime import datetime, timedelta
from airflow.exceptions import AirflowFailException

def download_inmet_data(execution_date=None):
    bucket_name = os.getenv("BRONZE_BUCKET")
    
    if execution_date:
        date_obj = datetime.strptime(execution_date, '%Y-%m-%d') if isinstance(execution_date, str) else execution_date
    else:
        date_obj = datetime.now()

    target_date_obj = date_obj - timedelta(days=1)
    target_date = target_date_obj.strftime('%Y-%m-%d')
    
    url = "https://apitempo.inmet.gov.br/estacoes/T" 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"--- Tentando Rota de Estações INMET: {target_date} ---")
    
    try:
        response = requests.get(url, headers=headers, timeout=60)
        
        if response.status_code != 200:
            raise AirflowFailException(f"INMET API fora do ar: Status {response.status_code}")
            
        try:
            data = response.json()
        except Exception:
            print(f"Erro ao decodificar JSON. Conteúdo recebido: {response.text[:100]}")
            raise AirflowFailException("A API retornou HTML/Texto em vez de JSON. Possível bloqueio ou 404.")

        df = pd.DataFrame(data)
        
        df.columns = [col.lower().replace('.', '_') for col in df.columns]
        
        if df.empty:
            raise AirflowFailException("DataFrame vazio retornado pela API.")

        print(f"✅ Sucesso! {len(df)} estações capturadas.")

        # S3 Logic
        partition_path = f"source=inmet/year={target_date_obj.year}/month={target_date_obj.strftime('%m')}/day={target_date_obj.strftime('%d')}"
        file_name = f"inmet_stations_{target_date.replace('-', '')}.parquet"
        local_path = f"/tmp/{file_name}"
        s3_key = f"{partition_path}/{file_name}"

        df.to_parquet(local_path, index=False)
        
        s3_client = boto3.client("s3")
        s3_client.upload_file(local_path, bucket_name, s3_key)
        
        os.remove(local_path)
        return s3_key

    except Exception as e:
        print(f"❌ Falha crítica: {e}")
        raise AirflowFailException(e)