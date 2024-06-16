from pathlib import Path

SIMPLIFY_DIR = Path(__file__).resolve().parent.parent
UNLABELED_DIR = SIMPLIFY_DIR / 'unlabelled'
LABELED_DIR = SIMPLIFY_DIR / 'labelled'
INPUT_FILE = SIMPLIFY_DIR / 'temp/original.txt'