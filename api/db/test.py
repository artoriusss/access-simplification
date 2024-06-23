import psycopg2
from dotenv import load_dotenv
import os
from psycopg2 import sql

from connect import connect

load_dotenv()

def test_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        print(f"Connection established to {os.getenv('DB_NAME')} ({os.getenv('DB_HOST')})")
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"Connected to - {db_version}")
        print("Connection established successfully")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

def select_all_pairs(schema='unlabeled'):
    try:
        connection, cursor = connect()

        select_query = sql.SQL("SELECT * FROM {}.data").format(sql.Identifier(schema))
        cursor.execute(select_query)
        rows = cursor.fetchall()

        for row in rows:
            print(f"Original: {row[1]} \nSimplified: {row[2]}")
            print("------------\n")

    except Exception as e:
        print(f"Error selecting pairs: {e}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()

def main():
    test_connection()
    select_all_pairs()

if __name__ == '__main__':
    main()