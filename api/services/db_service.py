import os
import json
import time
from psycopg2 import sql

from db.connect import connect, commit_and_close
from inference.utils.paths import INPUT_FILE, UNLABELED_DIR, LABELED_DIR

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
        raise

def write_sentence_pairs(sentence_pairs, labeled=False):
    target_dir = UNLABELED_DIR if not labeled else LABELED_DIR
    schema = 'unlabeled' if not labeled else 'labelled'
    for pair in sentence_pairs:
        pair['simple'] = pair['simple'].rstrip('\n')
        pair['original'] = pair['original'].rstrip('\n')

    try:
        insert_pairs(sentence_pairs, schema=schema)
        print('Sentence pairs have been written to DB.')
    except Exception as e:
        print('Error inserting pairs:', e)
        timestamp = int(time.time())
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, f'simplified_{timestamp}.json')
        with open(path, 'w') as outfile:
            json.dump(sentence_pairs, outfile, indent=4)
        print(f'Wrote to simplify/unlabelled/simplified_{timestamp}.json')