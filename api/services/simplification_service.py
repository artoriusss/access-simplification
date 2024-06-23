import logging
import subprocess
import os
import json
import time

from psycopg2 import sql
from db.connect import connect, commit_and_close
from inference.utils.paths import INPUT_FILE

logger = logging.getLogger(__name__)

def simplify_sentence(complex_sentence):
    logger.debug(f"Simplifying sentence: {complex_sentence}")
    with open(INPUT_FILE, 'w') as infile:
        infile.write(complex_sentence)

    logger.debug(f"Running command: ['python', 'scripts/generate.py'] in {os.getcwd()}")

    command = ['python', 'scripts/generate.py']
    with open(INPUT_FILE, 'r') as infile:
        result = subprocess.run(command, stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if result.returncode != 0:
        logger.error(f"Subprocess returned an error: {result.returncode}")
        logger.error(f"Subprocess stderr: {result.stderr}")
        logger.error(f"Subprocess stdout: {result.stdout}")

    simplified_sentence = result.stdout.strip()
    logger.debug(f"Simplified Sentence: {simplified_sentence}")

    if os.path.exists(INPUT_FILE):
        os.remove(INPUT_FILE)

    return simplified_sentence