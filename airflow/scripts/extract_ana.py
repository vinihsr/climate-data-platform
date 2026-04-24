import requests
import pandas as pd
import re
import os
import boto3
import io 
from datetime import datetime

def download_ana_data(execution_date=None):
    bucket_name = os.getenv("BRONZE_BUCKET")
    
    if execution_date:
        if isinstance(execution_date, str):
            now = datetime.strptime(execution_date, '%Y-%m-%d')
        else:
            now = execution_date
    else:
        now = datetime.now()

    url = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroInventario"
    
    params = {
        'codEstDE': '', 'codEstAte': '', 'tpEst': '', 'nmEst': '', 'nmRio': '',
        'codBacia': '', 'codSubBacia': '', 'codUF': '', 'nmMunicipio': '',
        'nmEstado': '', 'responsavel': '', 'operadora': '', 'telemetrica': '',
        'tipoEstacao': '', 'sgResp': '', 'sgOper': ''
    }
    
    print(f"Iniciando download ANA para data de referência: {now.strftime('%Y-%m-%d')}")
    response = requests.get(url, params=params, timeout=120)
    
    if response.status_code == 200:
        xml_data = re.sub(r'\sxmlns="[^"]+"', '', response.text, count=1)
        
        try:
            df = pd.read_xml(io.StringIO(xml_data), xpath=".//Table", parser="etree")
            
            print(f"Sucesso Total! {len(df)} estações encontradas.")

            df.columns = [col.lower() for col in df.columns]
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
            df['codigo'] = pd.to_numeric(df['codigo'], errors='coerce').fillna(0).astype(int)

            year = now.year
            month = now.strftime('%m')
            day = now.strftime('%d')
            
            partition_path = f"source=ana/year={year}/month={month}/day={day}"
            file_name = f"ana_raw_{now.strftime('%Y%m%d')}.parquet"
            local_path = f"/tmp/{file_name}"

            df.to_parquet(local_path, index=False)

            s3_client = boto3.client("s3")
            s3_key = f"{partition_path}/{file_name}"
            
            print(f"Fazendo upload para: {bucket_name}/{s3_key}")
            s3_client.upload_file(local_path, bucket_name, s3_key)
            
            os.remove(local_path)
            
            return s3_key

        except Exception as e:
            print(f"Erro no processamento dos dados: {e}")
            raise
    else:
        print(f"Erro no Servidor ANA: {response.status_code}")
        raise Exception(f"ANA API returned {response.status_code}")