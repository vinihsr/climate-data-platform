import os
import glob
import boto3
import pandas as pd

def upload_inmet_data():
    bucket_name = os.getenv("BRONZE_BUCKET")
    input_folder = "2025"
    s3_client = boto3.client("s3")
    
    csv_files = glob.glob(os.path.join(input_folder, "*.CSV")) + glob.glob(os.path.join(input_folder, "*.csv"))
    
    for input_file in csv_files:
        try:
            df = pd.read_csv(input_file, sep=';', encoding='latin-1', skiprows=8, decimal=',')
            
            raw_columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
            cleaned_columns = (
                raw_columns.str.lower()
                .str.replace(r'[^a-z0-9_]', '_', regex=True)
                .str.replace(r'_{2,}', '_', regex=True)
                .str.strip('_')
            )
            df.columns = cleaned_columns
            
            unnamed_cols = [col for col in df.columns if 'unnamed' in col or col == 'extra' or col == '']
            if unnamed_cols:
                df = df.drop(columns=unnamed_cols)
                
            station_id = os.path.basename(input_file).split('_')[3]
            df['cd_estacao'] = station_id
            
            date_col = df.columns[0]
            df['parsed_date'] = pd.to_datetime(df[date_col].str.replace('/', '-'))
            df['year'] = df['parsed_date'].dt.year
            df['month'] = df['parsed_date'].dt.strftime('%m')
            df = df.drop(columns=['parsed_date'])
            
            protected_cols = ['data', 'hora', 'hora_utc', 'cd_estacao', 'year', 'month']
            for col in df.columns:
                if not any(p_col in col for p_col in protected_cols):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            for (year, month), group in df.groupby(['year', 'month']):
                # Explicit table folder layer first, followed by clean Hive partition formatting
                partition_path = f"inmet/year={year}/month={month}"
                file_name = f"inmet_{station_id}_data.parquet"
                local_path = f"/tmp/{file_name}"
                
                group.to_parquet(local_path, index=False)
                
                s3_key = f"{partition_path}/{file_name}"
                s3_client.upload_file(local_path, bucket_name, s3_key)
                os.remove(local_path)
                
        except Exception as e:
            print(f"Erro ao processar {input_file}: {str(e)}")