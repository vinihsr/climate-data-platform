from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys

sys.path.append('/opt/airflow/')
from scripts.extract_ibge import download_ibge_data

default_args = {
    'owner': 'vinicius',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG (
    'br_climate_ingest_ibge', 
    default_args=default_args,
    description='Ingestão de dados brutos do ibge para S3 Bronze',
    schedule_interval='@daily',
    catchup=False,
    tags=['bronze', 'ibge'],
) as dag:
    
    ingest_task = PythonOperator(
        task_id='ingest_ibge_to_bronze',
        python_callable=download_ibge_data,
        op_kwargs={'region': 'S'} 
    )