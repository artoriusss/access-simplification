import subprocess
import os, json, time

from api.inference.utils.paths import INPUT_FILE

if __name__ == '__main__':
    sentence_pairs = []

    while True:
        complex_sentence = os.getenv('COMPLEX_SENTENCE')  # Read from environment variable

        if not complex_sentence:
            print("No complex sentence provided. Exiting.")
            break

        with open(INPUT_FILE, 'w') as infile:
            infile.write(complex_sentence)
        print('Working on it...')

        command = ['python', 'scripts/generate.py']

        with open(INPUT_FILE, 'r') as infile:
            result = subprocess.run(command, stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        if result.stdout:
            simplified_sentence = result.stdout.strip()
            print('Simplified sentence:', simplified_sentence)
            sentence_pair = {'original': complex_sentence, 'simple': simplified_sentence}
            sentence_pairs.append(sentence_pair)
            os.remove(INPUT_FILE)

        if os.getenv('CONTINUE') == 'n':  # Read from environment variable
            break

    if sentence_pairs:
        print('Writing sentence pairs to file...')
        # write_sentence_pairs(sentence_pairs)
        for pair in sentence_pairs:
            print(pair)