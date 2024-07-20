from datetime import datetime, timedelta
import psycopg2
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
import logging


# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Define the DAG
dag = DAG(
    'test_postgres_connection_psycopg2',
    default_args=default_args,
    description='Test DAG to connect to Postgres using psycopg2, read table, and log rows',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

def query_postgres():
    conn = None
    cursor = None
    try:
        logging.info("Setting up database connection")
        db_conn = BaseHook.get_connection("ts-db")
        
        # Create connection string
        connection_str = f"dbname='{db_conn.schema}' user='{db_conn.login}' password='{db_conn.password}' host='{db_conn.host}' port='{db_conn.port}'"

        # Connect to PostgreSQL
        conn = psycopg2.connect(connection_str, connect_timeout=30)
        cursor = conn.cursor()
        logging.info("Database connection established")

        # Execute query to fetch data
        query = "SELECT * FROM labelled.data LIMIT 10;"
        logging.info(f"Executing query: {query}")
        cursor.execute(query)
        records = cursor.fetchall()
        logging.info(f"Query executed successfully, fetched records: {records}")

        # Convert to DataFrame
        df = pd.DataFrame(records, columns=[desc[0] for desc in cursor.description])
        logging.info(f"Data fetched: \n{df}")

        # Execute query to count total rows
        total_rows_query = "SELECT COUNT(*) FROM labelled.data;"
        logging.info(f"Executing query to count total rows: {total_rows_query}")
        cursor.execute(total_rows_query)
        total_rows = cursor.fetchone()[0]
        logging.info(f"Total number of rows: {total_rows}")

    except psycopg2.OperationalError as op_err:
        logging.error(f"Operational error: {op_err}")
        raise
    except psycopg2.Error as db_err:
        logging.error(f"Database error: {db_err}")
        raise
    except MemoryError as mem_err:
        logging.error(f"Memory error: {mem_err}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logging.info("Database connection closed")

query_postgres_task = PythonOperator(
    task_id='query_postgres',
    python_callable=query_postgres,
    execution_timeout=timedelta(minutes=5),
    dag=dag,
)

query_postgres_task