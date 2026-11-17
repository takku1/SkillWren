"""`skillwren policy`: pinned, workflow-bound policies generated from a flow."""
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
from skillwren.guard import Controller, Denied
from skillwren.validator.approval import approve

FLOW = ROOT / 'examples/host-demo/dep-audit/flow.md'
VERIFIER = ROOT / 'docs/current/research/lifecycle/a-manual/tools/verify_report.py'
CLEAN = json.dumps({'banned': [], 'licenses': {}, 'verdict': 'clean'})


class PolicyGenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copy2(FLOW, self.root / 'flow.md')
        (self.root / 'checks').mkdir()
        shutil.copy2(VERIFIER, self.root / 'checks' / 'verify.py')
        (self.root / 'out').mkdir()
        self.map = self.root / 'map.json'
        self.map.write_text(json.dumps({
            'verify#deps': {'verifier': [PYTHON, '-I', 'checks/verify.py']},
            'write#report': {'verifier': [PYTHON, '-I', 'checks/verify.py'],
                             'target': 'out/REPORT.md'}}))
        self.approvals = self.root / 'approvals'

    def run_policy(self, *extra):
        return subprocess.run(
            [PYTHON, str(ROOT / 'scripts/skillwren.py'), 'policy', str(self.root / 'flow.md'),
             '--approvals', str(self.approvals), '--map', str(self.map),
             '--out', str(self.root / 'policy.json'), *extra],
            capture_output=True, text=True)

    def test_unapproved_flow_yields_no_policy(self):
        proc = self.run_policy()
        self.assertEqual(proc.returncode, 2)
        self.assertIn('not approved', proc.stderr)
        self.assertFalse((self.root / 'policy.json').exists())

    def test_generated_policy_pins_everything_and_enforces_order(self):
        approve(self.root / 'flow.md', True, 'admin', None, self.approvals)
        proc = self.run_policy()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report['enforced_rules'], ['verify#deps before write#report'])
        self.assertEqual(report['unmapped_steps'], [])
        policy = json.loads((self.root / 'policy.json').read_text())
        script = str((self.root / 'checks' / 'verify.py').resolve())
        for op in policy['operations'].values():
            self.assertIn(script, op['pins'])
            self.assertIn(op['argv'][0], op['pins'])
        guard = Controller(policy)
        request = {'action': 'verify', 'operation': 'write#report', 'content': CLEAN}
        guard.handle(request)
        with self.assertRaises(Denied):
            guard.handle(dict(request, action='write'))
        guard.handle({'action': 'verify', 'operation': 'verify#deps', 'content': CLEAN})
        guard.handle(request)
        guard.handle(dict(request, action='write'))
        self.assertTrue((self.root / 'out' / 'REPORT.md').exists())

    def test_unmapped_typed_steps_are_reported(self):
        approve(self.root / 'flow.md', True, 'admin', None, self.approvals)
        self.map.write_text(json.dumps({'write#report': {
            'verifier': [PYTHON, '-I', 'checks/verify.py'], 'target': 'out/REPORT.md'}}))
        proc = self.run_policy()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report['unmapped_steps'], ['deps'])
        self.assertEqual(report['unenforced_rules'], ['verify#deps before write#report'])
        self.assertIn('stay unguarded', proc.stderr)

    def test_existing_policy_never_overwritten(self):
        approve(self.root / 'flow.md', True, 'admin', None, self.approvals)
        (self.root / 'policy.json').write_text('{}')
        self.assertEqual(self.run_policy().returncode, 2)
        self.assertEqual((self.root / 'policy.json').read_text(), '{}')


if __name__ == '__main__':
    unittest.main()
