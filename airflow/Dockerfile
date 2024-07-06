FROM apache/airflow:2.5.1

USER root
RUN apt-get update && apt-get install -y \
    python3-pip \
    libpq-dev \
    gcc \
    build-essential

USER airflow
RUN pip install --no-cache-dir \
    pandas \
    apache-airflow-providers-google \
    google-cloud-storage

RUN pip install --no-cache-dir --no-binary :all: psycopg2

COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt
RUN mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins