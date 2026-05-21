import os
import glob
import boto3
import pandas as pd
import time

def upload_inmet_data():
    bucket_name = os.getenv("BRONZE_BUCKET")
    input_folder = "2025"
    s3_client = boto3.client("s3")
    set_of_s3_keys = set()
    uploaded_any = 0  

    print("Indexing complete S3 Data Lake state...")
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix='inmet/')
    
    try:
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    set_of_s3_keys.add(obj['Key'])
        print(f"Data Lake Discovery Complete: Cached {len(set_of_s3_keys)} file signatures from S3.")
    except Exception as e:
        print(f"Warning during S3 indexing layout check: {str(e)}. Proceeding with fallback map.")
    
    csv_files = glob.glob(os.path.join(input_folder, "*.CSV")) + glob.glob(os.path.join(input_folder, "*.csv"))
    
    for input_file in csv_files:
        try:
            station_id = os.path.basename(input_file).split('_')[3]
            expected_keys = [f"inmet/year=2025/month={str(m).zfill(2)}/inmet_{station_id}_data.parquet" for m in range(1, 13)]
            
            if all(key in set_of_s3_keys for key in expected_keys):
                print(f"Skipping Station {station_id}: All 2025 monthly partitions already exist on S3.")
                continue  
            
            print(f"Processing missing data partitions for Station: {station_id}")
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
                partition_path = f"inmet/year={year}/month={month}"
                file_name = f"inmet_{station_id}_data.parquet"
                s3_key = f"{partition_path}/{file_name}"
                
                local_path = f"/tmp/inmet_{station_id}_{year}_{month}.parquet"

                if s3_key not in set_of_s3_keys:
                    print(f"Uploading missing partition: {s3_key}")
                    
                    group.to_parquet(local_path, index=False)
                    
                    time.sleep(0.1)
                    
                    s3_client.upload_file(local_path, bucket_name, s3_key)
                    
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        
                    uploaded_any = 1  
                else:
                    print(f"Partition already exists on S3: {s3_key}")
                
        except Exception as e:
            print(f"Erro critical ao processar {input_file}: {str(e)}")

    return uploaded_any

if __name__ == "__main__":
    upload_inmet_data()