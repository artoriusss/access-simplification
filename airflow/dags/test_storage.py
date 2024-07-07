from datetime import datetime, timedelta
import os
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
from google.cloud import storage
import logging

# Define your arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'test_gcs_hook',
    default_args=default_args,
    description='Extract latest WikiLarge dataset from GCP, count records, and log the counts',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

def extract_latest_dataset(**kwargs):
    try:
        gcs_hook = GCSHook(gcp_conn_id='ts-storage')
        bucket_name = 'ts-dataset'
        prefix = 'wikilarge_'

        logging.info("Connecting to GCS")
        client = storage.Client()
        bucket = client.get_bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=prefix))
        
        if not blobs:
            raise ValueError("No datasets found in the bucket.")

        latest_blob = max(blobs, key=lambda b: b.updated)
        latest_prefix = latest_blob.name.split('/')[0]
        logging.info(f"Latest prefix: {latest_prefix}")
        
        for blob in bucket.list_blobs(prefix=latest_prefix):
            local_path = os.path.join('/tmp', blob.name)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob.download_to_filename(local_path)
            logging.info(f"Downloaded {blob.name} to {local_path}")

        return latest_prefix
    except Exception as e:
        logging.error(f"Failed to extract latest dataset: {e}")
        raise

def count_records(ti):
    try:
        latest_prefix = ti.xcom_pull(task_ids='extract_latest_dataset')
        logging.info(f"Pulled latest prefix: {latest_prefix}")

        dataset_files = [
            f'/tmp/{latest_prefix}/wikilarge.train.complex',
            f'/tmp/{latest_prefix}/wikilarge.train.simple',
            f'/tmp/{latest_prefix}/wikilarge.valid.complex',
            f'/tmp/{latest_prefix}/wikilarge.valid.simple',
            f'/tmp/{latest_prefix}/wikilarge.test.complex',
            f'/tmp/{latest_prefix}/wikilarge.test.simple'
        ]

        for file_path in dataset_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    logging.info(f"{os.path.basename(file_path)}: {len(lines)} records")
            else:
                logging.warning(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"Failed to count records: {e}")
        raise

extract_latest_dataset_task = PythonOperator(
    task_id='extract_latest_dataset',
    python_callable=extract_latest_dataset,
    provide_context=True,
    dag=dag,
)

count_records_task = PythonOperator(
    task_id='count_records',
    python_callable=count_records,
    provide_context=True,
    dag=dag,
)

extract_latest_dataset_task >> count_records_task