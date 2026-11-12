"""Create a host policy for the bundled debug=false configuration verifier."""
import argparse
import json
from pathlib import Path
import sys
PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.guard import file_digest

parser = argparse.ArgumentParser()
parser.add_argument('--target', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
script = str(ROOT / 'examples/guard/verify_config.py')
policy = {'version': 1, 'operations': {'write#config': {
    'target': str(Path(args.target).resolve()),
    'argv': [PYTHON, '-I', script],
    'pins': {PYTHON: file_digest(PYTHON), script: file_digest(script)},
    'timeout': 5}}}
with Path(args.out).open('x', encoding='utf-8') as stream:
    json.dump(policy, stream, indent=2)

