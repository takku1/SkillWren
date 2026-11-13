"""Approval gate and draft plumbing tests (scripted adapter, no model)."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.validator.approval import approve, check

PAIRS = ROOT / 'docs/current/research/nl-fidelity'
ADAPTER = [PYTHON, str(ROOT / 'tests/fixtures/draft/echo_adapter.py')]


class ApproveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.flow = self.root / 'flow.md'
        shutil.copy(PAIRS / '01-flow.md', self.flow)
        self.policy = self.root / 'policy.json'
        self.policy.write_text(json.dumps(
            {"version": 1, "operations": {"write#config": {}}}))
        self.dir = self.root / 'approvals'

    def test_approve_records_digest_and_coverage(self):
        record = approve(self.flow, True, 'reviewer', self.policy, self.dir)
        self.assertEqual(record['by'], 'reviewer')
        self.assertIn('config', record['enforceable'])
        self.assertEqual(record['covered'].get('config'), 'write#config')
        self.assertIn('check', record['uncovered'])

    def test_check_passes_then_fails_after_edit(self):
        approve(self.flow, True, 'reviewer', None, self.dir)
        self.assertTrue(check(self.flow, self.dir)['approved'])
        with self.flow.open('a', encoding='utf-8') as stream:
            stream.write('\n# substantive edit\n')
        report = check(self.flow, self.dir)
        self.assertFalse(report['approved'])
        self.assertIn('changed', report['reason'])

    def test_check_without_approval_is_not_approval(self):
        self.assertFalse(check(self.flow, self.dir)['approved'])

    def test_cli_requires_approver(self):
        proc = subprocess.run(
            [PYTHON, str(ROOT / 'scripts/skillwren.py'), 'approve',
             str(self.flow), '--fragment', '--dir', str(self.dir)],
            text=True, capture_output=True)
        self.assertEqual(proc.returncode, 2, proc.stdout)


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_draft(self, *args):
        return subprocess.run(
            [PYTHON, str(ROOT / 'scripts/skillwren.py'), 'draft', *args],
            text=True, capture_output=True)

    def test_scripted_adapter_produces_proposal(self):
        intent = self.root / 'intent.md'
        intent.write_text('Summarize the request.')
        out = self.root / 'proposal.md'
        proc = self.run_draft('--intent-file', str(intent), '--adapter',
                              json.dumps(ADAPTER), '--out', str(out))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('return notes as notes', out.read_text())
        self.assertIn('unresolved questions', proc.stderr)
        self.assertIn('Not approved', proc.stderr)

    def test_bad_adapter_json_fails(self):
        intent = self.root / 'intent.md'
        intent.write_text('Summarize the request.')
        proc = self.run_draft('--intent-file', str(intent), '--adapter',
                              json.dumps([PYTHON, '-c', 'print(42)']))
        self.assertEqual(proc.returncode, 2, proc.stderr)

    def test_adapter_without_flow_fails(self):
        intent = self.root / 'intent.md'
        intent.write_text('Summarize the request.')
        proc = self.run_draft('--intent-file', str(intent), '--adapter',
                              json.dumps([PYTHON, '-c',
                                          'print("{}")']))
        self.assertEqual(proc.returncode, 2, proc.stderr)


if __name__ == '__main__':
    unittest.main()
