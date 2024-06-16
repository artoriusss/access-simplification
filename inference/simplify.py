import subprocess
import os, json, time

from inference.utils.utils import write_sentence_pairs

if __name__ == '__main__':
    sentence_pairs = []

    while True:
        complex_sentence = input('Enter the complex sentence: ')

        if not complex_sentence:
            break

        input_file = 'inference/temp/original.txt'

        with open(input_file, 'w') as infile:
            infile.write(complex_sentence)
        print('Working on it...')

        command = ['python', 'scripts/generate.py']

        with open(input_file, 'r') as infile:
            result = subprocess.run(command, stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        if result.stdout:
            simplified_sentence = result.stdout
            print('Simplified sentence:', simplified_sentence)
            sentence_pair = {'original': complex_sentence, 'simple': simplified_sentence}
            sentence_pairs.append(sentence_pair)
            os.remove(input_file)

        if input('Do you want to continue? (y/n): ') == 'n':
            break

    if sentence_pairs:
        write_sentence_pairs(sentence_pairs)