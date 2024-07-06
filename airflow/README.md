## Airflow DAG Pipeline

This directory contains the setup of an Apache Airflow DAG pipeline designed to manage new training data for a text simplification project. The pipeline performs the following operations:

### 1. Database Query
- **Description:** Queries a PostgreSQL database to fetch rows from the table with annotated complex-simple sentence pairs.
- **Purpose:** Fetches text records for training purposes.
- **Storage:** The results are temporarily stored using Airflow's XCom for downstream tasks.

### 2. Extract the Last Version of the Dataset
- **Description:** Connects to Google Cloud Storage (GCS) and identifies the latest version of the dataset based on a prefix (e.g., `wikilarge_`).
- **Action:** Downloads the latest dataset files to a local temporary directory.

### 3. Extend Dataset
- **Description:** Appends the new records fetched from the PostgreSQL database to the training dataset files.
- **Logging:** Logs the number of records in each dataset file both before and after extending them.

### 4. Upload Extended Dataset
- **Description:** Creates a unique prefix for the new version of the dataset using the current Unix timestamp (e.g., `wikilarge_1720265148`).
- **Action:** Uploads the extended dataset files back to GCS under the new prefix.

### 5. Delete Processed Records
- **Description:** Deletes the records that were fetched from the database to prevent duplicate processing in future runs.
