import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

def connect():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cur = conn.cursor()
    return conn, cur

def commit_and_close(connection, cursor):
    connection.commit()
    cursor.close()
    connection.close()

def query(schema='unlabeled'):
    connection, cursor = connect()
    select_query = sql.SQL("SELECT * FROM {}.data").format(sql.Identifier(schema))
    cursor.execute(select_query)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({'id': row[0], 'original': row[1], 'simplified': row[2]})
    return result