# Use the official Apache Airflow image
FROM apache/airflow:2.5.1

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow

# Switch to root user temporarily to create directories and set permissions
USER root
RUN mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins ${AIRFLOW_HOME}/configs

# Copy the necessary files
COPY dags/ ${AIRFLOW_HOME}/dags/
COPY configs/ ${AIRFLOW_HOME}/configs/
COPY plugins/ ${AIRFLOW_HOME}/plugins/
COPY requirements.txt ${AIRFLOW_HOME}/requirements.txt
COPY README.md ${AIRFLOW_HOME}/README.md
COPY airflow-scheme.png ${AIRFLOW_HOME}/airflow-scheme.png
COPY entrypoint.sh /entrypoint.sh

# Make the entrypoint script executable
RUN chmod +x /entrypoint.sh

# Switch to the airflow user to install Python dependencies
USER airflow
RUN pip install --no-cache-dir -r ${AIRFLOW_HOME}/requirements.txt

# Set the entry point to our script
ENTRYPOINT ["/entrypoint.sh"]

# Default command to run the webserver
CMD ["airflow", "webserver"]