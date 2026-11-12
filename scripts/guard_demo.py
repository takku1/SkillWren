"""Demonstrate a denied write, bound verification, allowed write and replay denial."""
import json
from pathlib import Path
import sys
import tempfile

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.guard import Controller, Denied, file_digest


def run():
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'sensitive.json'
        verifier = str(ROOT / 'examples/guard/verify_config.py')
        policy = {'version': 1, 'operations': {'write#config': {
            'target': str(target), 'argv': [PYTHON, '-I', verifier],
            'pins': {PYTHON: file_digest(PYTHON), verifier: file_digest(verifier)},
            'timeout': 5}}}
        controller = Controller(policy)
        request = {'action': 'write', 'operation': 'write#config', 'content': '{"debug": false}'}
        try:
            controller.handle(request)
            raise AssertionError('unverified write accepted')
        except Denied:
            assert not target.exists()
        controller.handle(dict(request, action='verify'))
        controller.handle(request)
        assert target.read_text() == request['content']
        try:
            controller.handle(request)
            raise AssertionError('replay accepted')
        except Denied:
            pass
        print(json.dumps({'unverified_write': 'denied', 'verified_write': 'written',
                          'replay': 'denied', 'isolation': 'not tested by this demo'}))

if __name__ == '__main__':
    run()

