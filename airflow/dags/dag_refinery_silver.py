from airflow import DAG
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
    catchup=False,
    tags=['silver', 'transformation']
) as dag:
    
    clean_silver_folder = S3DeleteObjectsOperator(
        task_id="clean_silver_folder",
        bucket="climate-platform-silver-vinicius",
        prefix="dim_estacoes/",
        aws_conn_id="aws_default",
    )

    drop_dim_estacoes = AthenaOperator(
        task_id='drop_dim_estacoes',
        query="DROP TABLE IF EXISTS climate_platform_silver.dim_estacoes;",
        database='climate_platform_silver',   
        output_location='s3://climate-platform-athena-results-vinicius/results/',
        aws_conn_id='aws_default'
    )
    
    create_dim_estacoes = AthenaOperator(
        task_id='create_dim_estacoes',
        query="""
        CREATE TABLE climate_platform_silver.dim_estacoes
        AS
        WITH 
        ibge_cleaned AS (
            SELECT DISTINCT
                SUBSTR(TRIM(CAST(codigo_ibge AS VARCHAR)), 1, 6) as join_key,
                codigo_ibge,
                nome_municipio,
                nome_municipio_search,
                uf_sigla,
                regiao_nome
            FROM "climate_platform_bronze"."source_ibge"
        ),
        ana_prepared AS (
            SELECT 
                CAST(codigo AS VARCHAR) as estacao_id,
                nome as estacao_nome,
                'ANA' as fonte,
                CAST(tipoestacao AS VARCHAR) as tipo_estacao_id,
                TRY_CAST(latitude AS DOUBLE) as lat,
                TRY_CAST(longitude AS DOUBLE) as lon,
                SUBSTR(TRIM(CAST(municipiocodigo AS VARCHAR)), 1, 6) as join_key
            FROM "climate_platform_bronze"."source_ana"
        ),
        inmet_prepared AS (
            SELECT 
                CAST(cd_estacao AS VARCHAR) as estacao_id,
                dc_nome as estacao_nome,
                'INMET' as fonte,
                NULL as tipo_estacao_id,
                TRY_CAST(vl_latitude AS DOUBLE) as lat,
                TRY_CAST(vl_longitude AS DOUBLE) as lon,
                TRIM(UPPER(dc_nome)) as join_key_name
            FROM "climate_platform_bronze"."source_inmet"
        )
        SELECT 
            a.estacao_id, a.estacao_nome, a.fonte, a.tipo_estacao_id, a.lat, a.lon,
            i.codigo_ibge, i.nome_municipio, i.uf_sigla, i.regiao_nome
        FROM ana_prepared a
        JOIN ibge_cleaned i ON a.join_key = i.join_key

        UNION ALL

        SELECT 
            inm.estacao_id, inm.estacao_nome, inm.fonte, inm.tipo_estacao_id, inm.lat, inm.lon,
            i.codigo_ibge, i.nome_municipio, i.uf_sigla, i.regiao_nome
        FROM inmet_prepared inm
        JOIN ibge_cleaned i ON inm.join_key_name = TRIM(UPPER(i.nome_municipio_search))
        """,
        database='climate_platform_silver',
        output_location='s3://climate-platform-athena-results-vinicius/results/',
        workgroup='climate_workgroup_vinicius',
        aws_conn_id='aws_default' 
    )

    trigger_silver_crawler = GlueCrawlerOperator(
        task_id='trigger_silver_crawler',
        config={'Name': 'dim_estacoes_silver_crawler'},
        aws_conn_id='aws_default',
        wait_for_completion=True
    )

    clean_silver_folder >> drop_dim_estacoes >> create_dim_estacoes >> trigger_silver_crawler