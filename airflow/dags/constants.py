from airflow.datasets import Dataset

DS_ANA_BRONZE = Dataset("s3://climate-platform-bronze/ana/")
DS_INMET_BRONZE = Dataset("s3://climate-platform-bronze/inmet/")
DS_IBGE_BRONZE = Dataset("s3://climate-platform-bronze/ibge/")