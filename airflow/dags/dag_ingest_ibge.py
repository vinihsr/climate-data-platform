from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator
from constants import DS_IBGE_BRONZE
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

    trigger_ibge_crawler = GlueCrawlerOperator(
        task_id="trigger_ibge_crawler",
        config={"Name": "ibge_bronze_crawler"}, 
        aws_conn_id="aws_default",  
        poll_interval=30,             
        wait_for_completion=True,     
        dag=dag,          
    )

    trigger_ibge_crawler.out_datasets = [DS_IBGE_BRONZE]

    ingest_task >> trigger_ibge_crawler