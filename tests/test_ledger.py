import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren import ledger

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.flow = ROOT / 'tests/fixtures/fragments/skill/flows/build-fixed.md'
        self.run, self.path, self.rules = ledger.start(self.flow, self.directory)
        self.first = self.rules[0]['first']
        self.then = self.rules[0]['then']

    def test_failed_command_does_not_satisfy_order(self):
        ledger.exec_step(self.path, self.first, [sys.executable, '-c', 'raise SystemExit(3)'])
        ledger.note_step(self.path, self.then)
        self.assertFalse(ledger.check(self.path)['ok'])

    def test_successful_command_is_evidence(self):
        ledger.exec_step(self.path, self.first, [sys.executable, '-c', 'print(42)'])
        ledger.note_step(self.path, self.then)
        self.assertTrue(ledger.check(self.path, require_evidence=True)['ok'])

    def test_self_report_rejected_in_strict_mode(self):
        ledger.note_step(self.path, self.first)
        ledger.note_step(self.path, self.then)
        self.assertTrue(ledger.check(self.path)['ok'])
        self.assertFalse(ledger.check(self.path, require_evidence=True)['ok'])

    def test_tampering_detected(self):
        ledger.note_step(self.path, self.first)
        records = ledger.load(self.path)
        records[-1]['step'] = 'altered'
        self.path.write_text('\n'.join(json.dumps(r) for r in records), encoding='utf-8')
        self.assertFalse(ledger.check(self.path)['ok'])

    def test_cli_preserves_child_flags_after_separator(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
        child = [sys.executable, '-c', 'import sys; print(sys.argv[1:])', '--step', 'child value', '--', '-x']
        proc = subprocess.run([sys.executable, '-m', 'skillwren', 'ledger', 'exec', self.run,
            '--step', self.first, '--dir', str(self.directory), '--', *child],
            env=env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(ledger.load(self.path)[-1]['argv'], child)
        self.assertIn('child value', proc.stdout)

    def test_missing_command_is_usage_error(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.exec_step(self.path, self.first, [])

    def test_unscoped_run_never_claims_complete(self):
        report = ledger.check(self.path)
        self.assertIsNone(report['execution_complete'])
        self.assertEqual(report['completeness'], 'unassessed')
        self.assertEqual(report['outcome'], 'unassessed')

    def test_valid_checks_pass_while_completeness_unassessed(self):
        ledger.exec_step(self.path, self.first, [sys.executable, '-c', 'pass'])
        report = ledger.check(self.path)
        self.assertTrue(report['valid'])
        self.assertTrue(report['ok'])
        self.assertEqual(report['completeness'], 'unassessed')

    def test_completeness_states(self):
        _, path, _ = ledger.start(self.flow, self.directory, required=['security'])
        ledger.exec_step(path, 'security', [sys.executable, '-c', 'pass'])
        report = ledger.check(path)
        self.assertTrue(report['valid'])
        self.assertTrue(report['execution_complete'])
        self.assertEqual(report['completeness'], 'complete')
        self.assertEqual(report['outcome'], 'complete')

    def test_required_milestone_is_exact_and_must_succeed(self):
        _, path, _ = ledger.start(self.flow, self.directory, required=['security'])
        ledger.note_step(path, 'security notes')
        self.assertFalse(ledger.check(path)['execution_complete'])
        ledger.exec_step(path, 'security', [sys.executable, '-c', 'raise SystemExit(1)'])
        self.assertFalse(ledger.check(path)['execution_complete'])
        ledger.exec_step(path, 'security', [sys.executable, '-c', 'pass'])
        self.assertTrue(ledger.check(path)['execution_complete'])

class CommandPolicyTests(unittest.TestCase):
    def test_shell_and_git_option_bypasses_are_not_exempt(self):
        from skillwren.conform import undeclared_commands
        attacks = ['git status; echo bad', 'git diff && echo bad',
                   'git status\necho bad', 'git diff --output=target',
                   'git diff --ext-diff', 'git status $(echo bad)', 'git statusx']
        self.assertEqual(undeclared_commands(attacks, False), attacks)
        self.assertEqual(undeclared_commands(['git status --short', 'git diff --stat'], False), [])
