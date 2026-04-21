from airflow import DAG
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.providers.amazon.aws.operators.athena import AthenaOperator
from airflow.providers.amazon.aws.operators.glue_crawler import GlueCrawlerOperator
from airflow.providers.amazon.aws.operators.s3 import S3DeleteObjectsOperator
from datetime import datetime, timedelta

from constants import DS_ANA_BRONZE, DS_INMET_BRONZE, DS_IBGE_BRONZE


default_args = {
    'owner': 'vinicius',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='br_climate_silver_refinery',
    default_args=default_args,
    schedule=[DS_ANA_BRONZE, DS_INMET_BRONZE, DS_IBGE_BRONZE],
    start_date=datetime(2026, 4, 1),
    catchup=False
) as dag:
    
    clean_silver_folder = S3DeleteObjectsOperator(
    task_id="clean_silver_folder",
    bucket="climate-platform-silver-vinicius",
    prefix="silver/dim_estacoes/",
    aws_conn_id="aws_default",
)

    drop_dim_estacoes = AthenaOperator(
    task_id='drop_dim_estacoes',
    query="DROP TABLE IF EXISTS climate_platform_silver.dim_estacoes;",
    database='climate_platform_silver',   
    output_location='s3://climate-platform-athena-results-vinicius/queries/',
    aws_conn_id='aws_default'
)
    
    create_dim_estacoes = AthenaOperator(
        task_id='create_dim_estacoes',
        query="""
            CREATE TABLE climate_platform_silver.dim_estacoes
        WITH (
        format = 'PARQUET',
        external_location = 's3://climate-platform-silver-vinicius/silver/dim_estacoes/'
        ) AS
        SELECT 
            CAST(a.codigo AS VARCHAR) as estacao_id,
            a.nome as estacao_nome,
            'ANA' as fonte,
            CAST(a.tipoestacao AS VARCHAR) as tipo_estacao_id,
            TRY_CAST(a.latitude AS DOUBLE) as lat,   -- Forçando DOUBLE
            TRY_CAST(a.longitude AS DOUBLE) as lon, -- Forçando DOUBLE
            CAST(i.codigo_ibge AS VARCHAR) as codigo_ibge,
            i.nome_municipio,
            i.uf_sigla,
            i.regiao_nome
        FROM "climate_platform_bronze"."source_ana" a
        JOIN "climate_platform_bronze"."source_ibge" i 
            ON CAST(a.municipiocodigo AS VARCHAR) = CAST(i.codigo_ibge AS VARCHAR)

        UNION ALL

        SELECT 
            CAST(inm.cd_estacao AS VARCHAR) as estacao_id,
            inm.dc_nome as estacao_nome,
            'INMET' as fonte,
            NULL as tipo_estacao_id,
            TRY_CAST(REPLACE(inm.vl_latitude, ',', '.') AS DOUBLE) as lat,  -- Limpa vírgula se houver
            TRY_CAST(REPLACE(inm.vl_longitude, ',', '.') AS DOUBLE) as lon, -- Limpa vírgula se houver
            CAST(i.codigo_ibge AS VARCHAR) as codigo_ibge,
            i.nome_municipio,
            i.uf_sigla,
            i.regiao_nome
        FROM "climate_platform_bronze"."source_inmet" inm
        JOIN "climate_platform_bronze"."source_ibge" i 
            ON inm.dc_nome = i.nome_municipio_search;
        """,
        database='climate_platform_silver',
        output_location='s3://climate-platform-athena-results-vinicius/queries/',
        aws_conn_id='aws_default' 
    )


    trigger_silver_crawler = GlueCrawlerOperator(
        task_id='trigger_silver_crawler',
        config={'Name': 'silver_data_crawler'}
    )

    clean_silver_folder >> drop_dim_estacoes >> create_dim_estacoes >> trigger_silver_crawler