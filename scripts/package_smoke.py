"""Verify the wheel in a fresh environment outside the checkout."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import venv

parser = argparse.ArgumentParser()
parser.add_argument('wheel')
args = parser.parse_args()
wheel = str(Path(args.wheel).resolve())
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    venv.create(root / 'env', with_pip=True)
    python = root / 'env' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    subprocess.run([str(python), '-m', 'pip', 'install', '--no-index', '--no-deps', wheel], check=True)
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    subprocess.run([str(python), '-I', '-c',
        'import skillwren; from skillwren.guard import Controller; from skillwren.sandbox import run; print(skillwren.__file__)'],
        cwd=root, env=env, check=True)
    for command in ('ledger', 'guard', 'sandbox'):
        subprocess.run([str(python), '-I', '-m', 'skillwren', command, '--help'],
                       cwd=root, env=env, check=True, stdout=subprocess.DEVNULL)
print('Installed-wheel import and CLI smoke checks passed')
