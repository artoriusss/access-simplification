import os
import psycopg2
from google.cloud import storage

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.hooks.base import BaseHook
from airflow.providers.google.cloud.hooks.gcs import GCSHook

from datetime import datetime, timedelta
import logging
import time

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'extend_dataset',
    default_args=default_args,
    description='DAG to extend dataset by querying Postgres using psycopg2 and log rows',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

def query_db(ti):
    conn = None
    cursor = None
    try:
        logging.info("Setting up database connection")
        db_conn = BaseHook.get_connection("ts-db")
    
        connection_str = f"dbname='{db_conn.schema}' user='{db_conn.login}' password='{db_conn.password}' host='{db_conn.host}' port='{db_conn.port}'"

        conn = psycopg2.connect(connection_str, connect_timeout=30)
        cursor = conn.cursor()
        logging.info("Database connection established")

        query = "SELECT id, original, simplified FROM labelled.data"
        logging.info(f"Executing query: {query}")
        cursor.execute(query)
        records = cursor.fetchall()
        logging.info(f"Query executed successfully, fetched {len(records)} records.")

        result = [{"id": record[0], "original": record[1], "simple": record[2]} for record in records]
        ti.xcom_push(key='record_count', value=len(result))
        ti.xcom_push(key='records', value=result)
        
        return result

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Database connection closed")
        

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

def extend_dataset(**kwargs):
    ti = kwargs['ti']
    records = ti.xcom_pull(task_ids='query_db', key='records')
    latest_prefix = ti.xcom_pull(task_ids='extract_latest_dataset')

    dataset_files = {
        'train_complex': f'/tmp/{latest_prefix}/wikilarge.train.complex',
        'train_simple': f'/tmp/{latest_prefix}/wikilarge.train.simple',
        'valid_complex': f'/tmp/{latest_prefix}/wikilarge.valid.complex',
        'valid_simple': f'/tmp/{latest_prefix}/wikilarge.valid.simple',
        'test_complex': f'/tmp/{latest_prefix}/wikilarge.test.complex',
        'test_simple': f'/tmp/{latest_prefix}/wikilarge.test.simple',
    }

    def get_file_line_count(file_path):
        with open(file_path, 'r') as f:
            return sum(1 for _ in f)

    logging.info("Dataset files BEFORE extending:")
    for file_name, file_path in dataset_files.items():
        line_count = get_file_line_count(file_path)
        logging.info(f"{file_name}: {line_count} records")

    with open(dataset_files['train_complex'], 'a') as complex_file, open(dataset_files['train_simple'], 'a') as simple_file:
        for record in records:
            complex_file.write(record['original'] + '\n')
            simple_file.write(record['simple'] + '\n')

    logging.info("\nDataset files AFTER extending:")
    for file_name, file_path in dataset_files.items():
        line_count = get_file_line_count(file_path)
        logging.info(f"{file_name}: {line_count} records")


def upload_extended_dataset(**kwargs):
    ti = kwargs['ti']
    latest_prefix = ti.xcom_pull(task_ids='extract_latest_dataset')
    new_prefix = f"wikilarge_{int(time.time())}"
    dataset_files = {
        'train_complex': f'/tmp/{latest_prefix}/wikilarge.train.complex',
        'train_simple': f'/tmp/{latest_prefix}/wikilarge.train.simple',
        'valid_complex': f'/tmp/{latest_prefix}/wikilarge.valid.complex',
        'valid_simple': f'/tmp/{latest_prefix}/wikilarge.valid.simple',
        'test_complex': f'/tmp/{latest_prefix}/wikilarge.test.complex',
        'test_simple': f'/tmp/{latest_prefix}/wikilarge.test.simple',
    }

    client = storage.Client()
    bucket = client.get_bucket('ts-dataset')

    for file_name, file_path in dataset_files.items():
        blob = bucket.blob(f"{new_prefix}/{os.path.basename(file_path)}")
        blob.upload_from_filename(file_path)
        logging.info(f"Uploaded {file_path} to {blob.public_url}")

    return new_prefix

def delete_processed_records(**kwargs):
    ti = kwargs['ti']
    records = ti.xcom_pull(task_ids='query_db', key='records')
    ids = [record['id'] for record in records]

    conn = None
    cursor = None
    try:
        logging.info("Setting up database connection")
        db_conn = BaseHook.get_connection("ts-db")
    
        connection_str = f"dbname='{db_conn.schema}' user='{db_conn.login}' password='{db_conn.password}' host='{db_conn.host}' port='{db_conn.port}'"

        conn = psycopg2.connect(connection_str, connect_timeout=30)
        cursor = conn.cursor()
        logging.info("Database connection established")

        delete_query = f"DELETE FROM labelled.data WHERE id = ANY(%s)"
        logging.info(f"Executing query: {delete_query}")
        cursor.execute(delete_query, (ids,))
        conn.commit()
        logging.info(f"Deleted {cursor.rowcount} records from the database.")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Database connection closed")

def check_records(**kwargs):
    ti = kwargs['ti']
    record_count = ti.xcom_pull(task_ids='query_db', key='record_count')
    if record_count > 0:
        return 'extract_latest_dataset'
    else:
        return 'no_records'

with dag:
    
    query_db_task = PythonOperator(
        task_id='query_db',
        python_callable=query_db,
        provide_context=True,
        execution_timeout=timedelta(minutes=5),
    )

    branching_task = BranchPythonOperator(
        task_id='check_records',
        python_callable=check_records,
        provide_context=True,
    )

    no_records_task = PythonOperator(
        task_id='no_records',
        python_callable=lambda: logging.info("No records found in the database."),
    )

    extract_latest_dataset_task = PythonOperator(
        task_id='extract_latest_dataset',
        python_callable=extract_latest_dataset,
        provide_context=True,
    )
    
    extend_dataset_task = PythonOperator(
        task_id='extend_dataset',
        python_callable=extend_dataset,
        provide_context=True,
    )

    upload_extended_dataset_task = PythonOperator(
        task_id='upload_extended_dataset',
        python_callable=upload_extended_dataset,
        provide_context=True,
    )

    delete_processed_records_task = PythonOperator(
        task_id='delete_processed_records',
        python_callable=delete_processed_records,
        provide_context=True,
    )

    query_db_task >> branching_task
    branching_task >> [extract_latest_dataset_task, no_records_task]
    extract_latest_dataset_task >> extend_dataset_task >> upload_extended_dataset_task >> delete_processed_records_task