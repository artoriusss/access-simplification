#!/bin/bash
# Initialize the database if not already initialized
if [ ! -f /opt/airflow/airflow.db ]; then
    airflow db init
    touch /opt/airflow/airflow.db
fi

# Start the scheduler in the background
airflow scheduler &

# Start the webserver
exec airflow webserver