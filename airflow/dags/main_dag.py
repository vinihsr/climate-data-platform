from airflow import DAG
from airflow.models.baseoperator import cross_downstream
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator
from constants import DS_ANA_BRONZE
from constants import DS_IBGE_BRONZE
from constants import DS_INMET_BRONZE
sys.path.append('/opt/airflow/')
from scripts.extract_ana import download_ana_data
from scripts.extract_csv_inmet import upload_inmet_data
from scripts.extract_ibge import download_ibge_data


default_args = {
    'owner': 'vinicius',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG (
    'br_climate_ingest', 
    default_args=default_args,
    description='Ingestão de dados brutos para S3 Bronze',
    schedule_interval='@daily',
    catchup=False,
    tags=['bronze'],
) as dag:
    
    ingest_task_ana = PythonOperator(
        task_id='ingest_ana_to_bronze',
        python_callable=download_ana_data,
        op_kwargs={'execution_date': "{{ ds }}"}    
    )

    trigger_ana_crawler = GlueCrawlerOperator(
        task_id="trigger_ana_crawler",
        config={"Name": "ana_bronze_crawler"}, 
        aws_conn_id="aws_default",   
        poll_interval=30,             
        wait_for_completion=True,    
        dag=dag,         
    )

    ingest_task_inmet = PythonOperator(
        task_id='ingest_inmet_to_bronze',
        python_callable=upload_inmet_data,
        op_kwargs={'execution_date': "{{ ds }}"}    
    )

    trigger_inmet_crawler = GlueCrawlerOperator(
        task_id="trigger_inmet_crawler",
        config={"Name": "inmet_bronze_crawler"},
        aws_conn_id="aws_default",
        poll_interval=30,            
        wait_for_completion=True,    
        dag=dag,
    )

    ingest_task_ibge = PythonOperator(
        task_id='ingest_ibge_to_bronze',
        python_callable=download_ibge_data,
        op_kwargs={'execution_date': "{{ ds }}"}    
    )

    trigger_ibge_crawler = GlueCrawlerOperator(
        task_id="trigger_ibge_crawler",
        config={"Name": "ibge_bronze_crawler"}, 
        aws_conn_id="aws_default",  
        poll_interval=30,             
        wait_for_completion=True,     
        dag=dag,          
    )

    trigger_ana_crawler.out_datasets = [DS_ANA_BRONZE]
    trigger_inmet_crawler.out_datasets = [DS_INMET_BRONZE]
    trigger_ibge_crawler.out_datasets = [DS_IBGE_BRONZE]

    cross_downstream(
        [ingest_task_ana, ingest_task_inmet, ingest_task_ibge],
        [trigger_ana_crawler, trigger_inmet_crawler, trigger_ibge_crawler]
    )