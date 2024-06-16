import subprocess
import os
import json
import time
from psycopg2 import sql

from db.connect import connect, commit_and_close
from inference.utils.paths import INPUT_FILE

def simplify_sentence(complex_sentence):
    with open(INPUT_FILE, 'w') as infile:
        infile.write(complex_sentence)

    print(f"Running command: ['python', 'scripts/generate.py'] in {os.getcwd()}")

    command = ['python', 'scripts/generate.py']
    with open(INPUT_FILE, 'r') as infile:
        result = subprocess.run(command, stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode != 0:
        print(f"Subprocess returned an error: {result.returncode}")

    simplified_sentence = result.stdout.strip()
    #print(f"Simplified Sentence: {simplified_sentence}")

    if os.path.exists(INPUT_FILE):
        os.remove(INPUT_FILE)

    return simplified_sentence