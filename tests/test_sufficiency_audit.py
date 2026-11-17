"""Execution errors must not become evidence of behavioral failure."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sufficiency_audit import execution_error
import sufficiency_lab


class SufficiencyAuditTests(unittest.TestCase):
    def test_success_subtype_does_not_override_api_error(self):
        event = {'type': 'result', 'subtype': 'success', 'is_error': True,
                 'terminal_reason': 'api_error', 'api_error': 'usage_limit_reached'}
        self.assertEqual(execution_error([event]), 'usage_limit_reached')

    def test_completed_behavioral_failure_is_valid(self):
        self.assertIsNone(execution_error([
            {'type': 'result', 'subtype': 'success', 'is_error': False,
             'terminal_reason': 'completed'}]))

    def test_missing_result_is_incomplete(self):
        self.assertEqual(execution_error([]), 'missing_result')

    def test_budget_exhaustion_is_incomplete(self):
        self.assertEqual(execution_error([
            {'type': 'result', 'subtype': 'error_max_budget_usd'}]),
            'error_max_budget_usd')

    def test_resume_reuses_completed_attempt_and_stops_on_error(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'runs' / 'full-haiku-0'
            out.mkdir(parents=True)
            (out / 'SKILL.md').write_text(sufficiency_lab.variant_text(
                set(sufficiency_lab.ORDER)), encoding='utf-8')
            (out / 'record.json').write_text(json.dumps({'run': out.name}), encoding='utf-8')
            (out / 'transcript.jsonl').write_text(json.dumps(
                {'type': 'result', 'subtype': 'success', 'is_error': False}), encoding='utf-8')
            argv = ['sufficiency_lab.py', '--source', folder, '--out', folder,
                    '--variants', 'full', '--models', 'haiku', '--reps', '3', '--resume']
            with patch.object(sys, 'argv', argv), patch.object(
                    sufficiency_lab, 'run_one', return_value={
                        'execution_error': 'usage_limit_reached'}) as run:
                with self.assertRaisesRegex(SystemExit, 'usage_limit_reached'):
                    sufficiency_lab.main()
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[-1], 1)
            self.assertFalse(list(Path(folder).glob('results-*.json')))
