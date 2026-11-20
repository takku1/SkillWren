"""Workflow-bound guard: approval and order rules as write preconditions."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.guard import Controller, Denied, file_digest
from skillwren.validator.approval import approve

FLOW = ROOT / 'examples/host-demo/dep-audit/flow.md'
VERIFIER = ROOT / 'docs/current/research/lifecycle/a-manual/tools/verify_report.py'
CLEAN = json.dumps({'banned': [], 'licenses': {'MIT': True}, 'verdict': 'clean'})
BLOCKED = json.dumps({'banned': ['requests==1.0.0'], 'licenses': {}, 'verdict': 'blocked'})


class WorkflowGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.flow = self.root / 'flow.md'
        text = FLOW.read_text(encoding='utf-8').replace(
            'order:\n  verify#deps before write#report',
            'order:\n  verify#deps before write#report\n'
            '  exec dependency check before write#report')
        self.flow.write_bytes(text.encode('utf-8'))
        self.approvals = self.root / 'approvals'
        approve(self.flow, True, 'host-admin', None, self.approvals)
        verifier = self.root / 'verify.py'
        shutil.copy2(VERIFIER, verifier)
        self.target = self.root / 'REPORT.md'
        pins = {PYTHON: file_digest(PYTHON), str(verifier): file_digest(verifier)}
        argv = [PYTHON, '-I', str(verifier)]
        self.policy = {'version': 1, 'workflow': {
            'flow': str(self.flow), 'flow_sha256': file_digest(self.flow),
            'approvals': str(self.approvals)},
            'operations': {
                'verify#deps': {'argv': argv, 'pins': dict(pins), 'timeout': 5},
                'write#report': {'target': str(self.target), 'argv': argv,
                                 'pins': dict(pins), 'timeout': 5}}}

    def req(self, action, operation, content=CLEAN):
        return {'action': action, 'operation': operation, 'content': content}

    def test_write_needs_the_order_rule_prerequisite(self):
        guard = Controller(self.policy)
        guard.handle(self.req('verify', 'write#report'))
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req('write', 'write#report'))
        self.assertIn('verify#deps before write#report', str(caught.exception))
        self.assertFalse(self.target.exists())
        guard.handle(self.req('verify', 'verify#deps'))
        guard.handle(self.req('verify', 'write#report'))
        guard.handle(self.req('write', 'write#report'))
        self.assertEqual(self.target.read_text(), CLEAN)

    def test_failed_check_revokes_earlier_success(self):
        guard = Controller(self.policy)
        guard.handle(self.req('verify', 'verify#deps'))
        with self.assertRaises(Denied):
            guard.handle(self.req('verify', 'verify#deps', BLOCKED))
        guard.handle(self.req('verify', 'write#report'))
        with self.assertRaises(Denied):
            guard.handle(self.req('write', 'write#report'))

    def test_check_operations_cannot_write(self):
        guard = Controller(self.policy)
        with self.assertRaises(Denied):
            guard.handle(self.req('write', 'verify#deps'))

    def test_unapproved_or_changed_flow_refused(self):
        (self.approvals / 'flow.approvals.jsonl').unlink()
        with self.assertRaises(Denied) as caught:
            Controller(self.policy)
        self.assertIn('not approved', str(caught.exception))
        approve(self.flow, True, 'host-admin', None, self.approvals)
        guard = Controller(self.policy)
        guard.handle(self.req('verify', 'verify#deps'))
        guard.handle(self.req('verify', 'write#report'))
        with self.flow.open('a', encoding='utf-8') as stream:
            stream.write('\n<!-- edited after the guard started -->\n')
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req('write', 'write#report'))
        self.assertIn('workflow file changed', str(caught.exception))

    def test_status_lists_enforced_and_unenforced_rules(self):
        status = Controller(self.policy).handle({'action': 'status'})
        self.assertEqual(status['enforced_rules'], ['verify#deps before write#report'])
        self.assertEqual(status['unenforced_rules'],
                         ['exec dependency check before write#report'])

    def with_order(self, *lines):
        text = self.flow.read_text(encoding='utf-8').replace(
            'order:\n  verify#deps before write#report\n'
            '  exec dependency check before write#report',
            'order:\n' + '\n'.join('  ' + line for line in lines))
        self.flow.write_bytes(text.encode('utf-8'))
        approve(self.flow, True, 'host-admin', None, self.approvals)
        self.policy['workflow']['flow_sha256'] = file_digest(self.flow)
        return Controller(self.policy)

    def test_exclusion_between_operations_is_enforced(self):
        """SPEC 23: once A has run, B is refused (the field's runtime refusal,
        now named by the rule instead of discovered)."""
        guard = self.with_order('verify#deps before write#report',
                                'never write#report before verify#deps',
                                'never write#notes before verify#deps')
        status = guard.handle({'action': 'status'})
        self.assertIn('never write#report before verify#deps', status['enforced_rules'])
        self.assertEqual(status['unenforced_rules'], ['never write#notes before verify#deps'])
        guard.handle(self.req('verify', 'verify#deps'))
        guard.handle(self.req('verify', 'write#report'))
        guard.handle(self.req('write', 'write#report'))
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req('verify', 'verify#deps'))
        self.assertIn('write#report already ran', str(caught.exception))

    def test_failed_check_counts_as_run_for_exclusions(self):
        guard = self.with_order('never verify#deps before write#report')
        with self.assertRaises(Denied):
            guard.handle(self.req('verify', 'verify#deps', BLOCKED))
        guard.handle(self.req('verify', 'write#report'))
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req('write', 'write#report'))
        self.assertIn('never verify#deps before write#report', str(caught.exception))
        self.assertFalse(self.target.exists())

    def test_exclusion_allows_the_later_step_first(self):
        guard = self.with_order('never verify#deps before write#report')
        guard.handle(self.req('verify', 'write#report'))
        guard.handle(self.req('write', 'write#report'))
        guard.handle(self.req('verify', 'verify#deps'))
        self.assertTrue(self.target.exists())

    def test_workflow_shape_validated(self):
        self.policy['workflow']['flow'] = 'flow.md'
        with self.assertRaises(Denied):
            Controller(self.policy)
        del self.policy['workflow']['flow']
        with self.assertRaises(Denied):
            Controller(self.policy)

    def test_policy_without_workflow_is_unchanged(self):
        del self.policy['workflow']
        guard = Controller(self.policy)
        guard.handle(self.req('verify', 'write#report'))
        guard.handle(self.req('write', 'write#report'))
        self.assertTrue(self.target.exists())


if __name__ == '__main__':
    unittest.main()
