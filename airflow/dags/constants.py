from airflow.datasets import Dataset

DS_ANA_BRONZE = Dataset("s3://climate-platform-bronze-vinicius/ana/")
DS_INMET_BRONZE = Dataset("s3://climate-platform-bronze-vinicius/inmet/")
DS_IBGE_BRONZE = Dataset("s3://climate-platform-bronze-vinicius/ibge/")