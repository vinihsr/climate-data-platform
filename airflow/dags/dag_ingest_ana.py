from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator

sys.path.append('/opt/airflow/')
from scripts.extract_ana import download_ana_data

default_args = {
    'owner': 'vinicius',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG (
    'br_climate_ingest_ana', 
    default_args=default_args,
    description='Ingestão de dados brutos do ana para S3 Bronze',
    schedule_interval='@daily',
    catchup=False,
    tags=['bronze', 'ana'],
) as dag:
    
    ingest_task = PythonOperator(
        task_id='ingest_ana_to_bronze',
        python_callable=download_ana_data,
        op_kwargs={'region': 'S'} 
    )

    trigger_ana_crawler = GlueCrawlerOperator(
        task_id="trigger_ana_crawler",
        config={"Name": "ana_bronze_crawler"}, 
        aws_conn_id="aws_default",   
        poll_interval=30,             
        wait_for_completion=True,    
        dag=dag,         
    )

    ingest_task >> trigger_ana_crawler