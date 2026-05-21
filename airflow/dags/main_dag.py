import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
import boto3
import time

sys.path.append('/opt/airflow/')
from constants import DS_ANA_BRONZE, DS_IBGE_BRONZE, DS_INMET_BRONZE
from scripts.extract_ana import download_ana_data
from scripts.extract_csv_inmet import upload_inmet_data
from scripts.extract_ibge import download_ibge_data


def trigger_and_wait_for_crawler():
    crawler_names = [
        "ana_bronze_crawler",
        "inmet_bronze_crawler",
        "ibge_bronze_crawler"
    ]
    glue_client = boto3.client('glue')

    for name in crawler_names:
        print(f"Starting AWS Glue Crawler: {name}")
        try:
            glue_client.start_crawler(Name=name)
        except glue_client.exceptions.CrawlerRunningException:
            print(f"Notice: Crawler {name} is already active.")

        while True:
            response = glue_client.get_crawler(Name=name)
            status = response['Crawler']['State']
            print(f"Crawler '{name}' State: {status}")
            
            if status == 'READY':
                print(f"Crawler '{name}' has completed successfully!")
                break
                
            time.sleep(15)


def verify_mutations(ti):
    inmet_status = ti.xcom_pull(task_ids='ingest_inmet_to_bronze') or 0
    ibge_status = ti.xcom_pull(task_ids='ingest_ibge_to_bronze') or 0
    ana_status = ti.xcom_pull(task_ids='ingest_ana_to_bronze') or 0

    total_mutations = inmet_status + ibge_status + ana_status
    print(f"Diagnostic - Combined data lake delta tracking value: {total_mutations}")
    return total_mutations > 0


default_args = {
    'owner': 'vinicius',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'br_climate_bronze_ingest', 
    default_args=default_args,
    description='Ingestão de dados brutos para S3 Bronze com Gatekeeper inteligente',
    schedule_interval='@daily',
    catchup=False,
    tags=['bronze'],
) as dag:
    
    ingest_task_ana = PythonOperator(
        task_id='ingest_ana_to_bronze',
        python_callable=download_ana_data,
        op_kwargs={'execution_date': "{{ ds }}"}    
    )

    ingest_task_inmet = PythonOperator(
        task_id='ingest_inmet_to_bronze',
        python_callable=upload_inmet_data,
        op_kwargs={'execution_date': "{{ ds }}"}    
    )

    ingest_task_ibge = PythonOperator(
        task_id='ingest_ibge_to_bronze',
        python_callable=download_ibge_data,
        op_kwargs={'execution_date': "{{ ds }}"}    
    )

    gatekeeper_task = ShortCircuitOperator(
        task_id='check_lake_updates',
        python_callable=verify_mutations
    )

    trigger_bronze_crawler = PythonOperator(
        task_id="trigger_bronze_crawler",
        python_callable=trigger_and_wait_for_crawler
    )

    trigger_bronze_crawler.out_datasets = [DS_ANA_BRONZE, DS_INMET_BRONZE, DS_IBGE_BRONZE]

    [ingest_task_ana, ingest_task_inmet, ingest_task_ibge] >> gatekeeper_task >> trigger_bronze_crawler