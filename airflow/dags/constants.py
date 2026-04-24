from airflow.datasets import Dataset

# Matching the standardized source=name pattern
DS_ANA_BRONZE = Dataset("s3://climate-platform-bronze-vinicius/source=ana/")
DS_INMET_BRONZE = Dataset("s3://climate-platform-bronze-vinicius/source=inmet/")
DS_IBGE_BRONZE = Dataset("s3://climate-platform-bronze-vinicius/source=ibge/")