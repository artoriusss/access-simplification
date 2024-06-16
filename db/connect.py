import psycopg2
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