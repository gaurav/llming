import sys
from pathlib import Path

# vlmddiff.py sits one directory up and is a plain script, not an installed package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
