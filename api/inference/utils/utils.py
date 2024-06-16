import json
import os
import time
from psycopg2 import sql

from db.connect import connect, commit_and_close
from inference.utils.paths import UNLABELED_DIR

def insert_pairs(sentence_pairs, schema='unlabeled'):
    conn, cur = connect()
    
    try:
        for pair in sentence_pairs:
            insert_query = sql.SQL(
                "INSERT INTO {}.data (original, simplified) VALUES (%s, %s)"
            ).format(sql.Identifier(schema))
            cur.execute(insert_query, (pair['original'], pair['simple']))
        
        commit_and_close(conn, cur)
        print("Data inserted successfully")

    except Exception as e:
        print(f"Error inserting pairs: {e}")
        if conn:
            conn.rollback()
        commit_and_close(conn, cur)
        raise  # Re-raise the exception to handle it in `write_sentence_pairs`

def write_sentence_pairs(sentence_pairs):
    for pair in sentence_pairs:
        pair['simple'] = pair['simple'].rstrip('\n')
        pair['original'] = pair['original'].rstrip('\n')

    try:
        insert_pairs(sentence_pairs)
        print('Sentence pairs have been written to DB.')

    except Exception as e:
        print('Error inserting pairs:', e)
        print('Writing to local directory...')
        timestamp = int(time.time())
        os.makedirs(UNLABELED_DIR, exist_ok=True)
        path = os.path.join(UNLABELED_DIR, f'simplified_{timestamp}.json')
        with open(path, 'w') as outfile:
            json.dump(sentence_pairs, outfile, indent=4)
        print(f'Wrote to simplify/unlabelled/simplified_{timestamp}.json')