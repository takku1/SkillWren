"""Top-level CLI help exits zero; unknown commands still fail."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    env = {'PATH': os.environ['PATH'], 'PYTHONPATH': str(ROOT / 'src')}
    if os.environ.get('SYSTEMROOT'):
        env['SYSTEMROOT'] = os.environ['SYSTEMROOT']
    return subprocess.run(
        [PYTHON, '-m', 'skillwren', *args],
        capture_output=True, text=True, cwd=str(ROOT), env=env)


class HelpTests(unittest.TestCase):
    def test_top_level_help_exits_zero(self):
        proc = run('--help')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('explain-workflow', proc.stdout)

    def test_check_help_exits_zero(self):
        proc = run('check', '--help')
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_unknown_command_still_fails(self):
        proc = run('frobnicate')
        self.assertEqual(proc.returncode, 2)


if __name__ == '__main__':
    unittest.main()
