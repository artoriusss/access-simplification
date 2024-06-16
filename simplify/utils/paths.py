from pathlib import Path

SIMPLIFY_DIR = Path(__file__).resolve().parent.parent
UNLABELED_DIR = SIMPLIFY_DIR / 'unlabelled'
INPUT_FILE = SIMPLIFY_DIR / 'temp/original.txt'

print(SIMPLIFY_DIR)
print(UNLABELED_DIR)
print(INPUT_FILE)