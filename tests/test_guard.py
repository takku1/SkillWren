import json
from pathlib import Path
import sys
import tempfile
import unittest

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.guard import Controller, Denied, file_digest
from skillwren.audit import AuditStore, AuditError

class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.target = self.root / 'sensitive.json'
        script = str(ROOT / 'examples/guard/verify_config.py')
        self.policy = {'version': 1, 'operations': {'write#config': {
            'target': str(self.target), 'argv': [PYTHON, '-I', script],
            'pins': {PYTHON: file_digest(PYTHON), script: file_digest(script)},
            'timeout': 5}}}
        self.guard = Controller(self.policy)
        self.content = '{"debug": false}'

    def request(self, action, content=None):
        return {'action': action, 'operation': 'write#config',
                'content': self.content if content is None else content}

    def test_real_write_requires_verification(self):
        with self.assertRaises(Denied):
            self.guard.handle(self.request('write'))
        self.assertFalse(self.target.exists())
        self.guard.handle(self.request('verify'))
        self.guard.handle(self.request('write'))
        self.assertEqual(self.target.read_text(), self.content)
        with self.assertRaises(Denied):
            self.guard.handle(self.request('write'))

    def test_noop_write_still_consumes_approval(self):
        self.target.write_text(self.content)
        self.guard.handle(self.request('verify'))
        self.guard.handle(self.request('write'))
        with self.assertRaises(Denied):
            self.guard.handle(self.request('write'))

    def test_reject_invalid_candidate_and_revoke_old_evidence(self):
        self.guard.handle(self.request('verify'))
        with self.assertRaises(Denied):
            self.guard.handle(self.request('verify', '{"debug": true}'))
        with self.assertRaises(Denied):
            self.guard.handle(self.request('write'))

    def test_stale_target_and_content(self):
        self.guard.handle(self.request('verify'))
        self.target.write_text('changed')
        with self.assertRaises(Denied):
            self.guard.handle(self.request('write'))
        self.guard.handle(self.request('verify'))
        with self.assertRaises(Denied):
            self.guard.handle(self.request('write', '{"debug":false}'))

    def test_restart_and_arbitrary_commands_fail_closed(self):
        self.guard.handle(self.request('verify'))
        with self.assertRaises(Denied):
            Controller(self.policy).handle(self.request('write'))
        request = self.request('verify')
        request['argv'] = [PYTHON, '-c', 'print(42)']
        with self.assertRaises(Denied):
            self.guard.handle(request)

    def test_altered_verifier_pin(self):
        self.policy['operations']['write#config']['pins'][PYTHON] = 'wrong'
        with self.assertRaises(Denied):
            Controller(self.policy)

    def test_irrelevant_success_does_not_verify(self):
        script = self.root / 'irrelevant.py'
        script.write_text('print(42)')
        op = self.policy['operations']['write#config']
        op['argv'] = [PYTHON, '-I', str(script)]
        op['pins'][str(script)] = file_digest(script)
        guard = Controller(self.policy)
        with self.assertRaises(Denied):
            guard.handle(self.request('verify'))

class AuditTests(unittest.TestCase):
    def test_truncation_and_reseal_rejected_against_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log, checkpoint = root / 'events', root / 'anchor'
            store = AuditStore(log, checkpoint)
            store.append({'type': 'start'})
            store.append({'type': 'complete'})
            original = log.read_text()
            log.write_text(original.splitlines()[0] + '\n')
            with self.assertRaises(AuditError):
                AuditStore(log, checkpoint)
            log.write_text(original)
            self.assertEqual(len(AuditStore(log, checkpoint).records), 2)
            from skillwren.ledger import _seal
            a = _seal({'seq': 0, 'type': 'forged'}, None)
            b = _seal({'seq': 1, 'type': 'complete'}, a['hash'])
            log.write_text(json.dumps(a) + '\n' + json.dumps(b) + '\n')
            with self.assertRaises(AuditError):
                AuditStore(log, checkpoint)

class TypedOrderingTests(unittest.TestCase):
    def test_exact_identity_survives_prose_change(self):
        from skillwren.validator.ordering import matches
        self.assertTrue(matches('verify#security', 'verify #security completely revised prose'))
        self.assertFalse(matches('verify#security', 'verify #security-notes check'))
        self.assertFalse(matches('verify#security', 'write #security check'))

    def test_typed_rule_runs_through_real_cfg(self):
        from skillwren.validator import validate_fragment
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'flow.md'
            text = '''```contract
order:
  verify#security before write#config
```
```logic
main:
  verify #security approved configuration
    otherwise:
      abort with "Rejected"
  write #config configuration with target
  return configuration as configuration
```
'''
            file.write_text(text)
            errors, _ = validate_fragment(str(file))
            self.assertFalse([e for e in errors if e.rule == 'P1'], errors)
            file.write_text(text.replace('verify #security', 'verify #security-notes'))
            errors, _ = validate_fragment(str(file))
            self.assertTrue([e for e in errors if e.rule == 'P1'])
            file.write_text(text.replace('write #config', 'write #security'))
            errors, _ = validate_fragment(str(file))
            self.assertTrue([e for e in errors if e.rule == 'P2'])

class GuardProcessTests(unittest.TestCase):
    def test_cli_records_denial_and_success_without_content(self):
        import subprocess
        import os
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = str(ROOT / 'examples/guard/verify_config.py')
            policy = {'version': 1, 'operations': {'write#config': {
                'target': str(root / 'target'), 'argv': [PYTHON, '-I', script],
                'pins': {PYTHON: file_digest(PYTHON), script: file_digest(script)}, 'timeout': 5}}}
            path = root / 'policy.json'
            path.write_text(json.dumps(policy))
            requests = [{'action': action, 'operation': 'write#config', 'content': '{"debug":false}'}
                        for action in ['write', 'verify', 'write']]
            proc = subprocess.run([PYTHON, str(ROOT / 'scripts/skillwren.py'), 'guard',
                str(path), '--audit', str(root / 'log'), '--checkpoint', str(root / 'checkpoint')],
                input='\n'.join(map(json.dumps, requests)) + '\n', text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual([json.loads(x)['ok'] for x in proc.stdout.splitlines()], [False, True, True])
            store = AuditStore(root / 'log', root / 'checkpoint')
            self.assertEqual(store.records[-1]['type'], 'stop')
            self.assertNotIn('debug', (root / 'log').read_text())

class SandboxTests(unittest.TestCase):
    def test_unpinned_image_refused_before_docker(self):
        from skillwren.sandbox import run
        with self.assertRaises(ValueError):
            run('python:latest', '.', ['python', '-V'])

class BenchmarkTests(unittest.TestCase):
    def test_scripted_attack_and_legitimate_grading(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('runtime_benchmark', ROOT / 'scripts/benchmark_runtime.py')
        benchmark = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(benchmark)
        unguarded = benchmark.run_trial('A', 'skip', 42)
        self.assertEqual(unguarded['unauthorized_writes'], 1)
        self.assertTrue(unguarded['task_completed'])
        for scenario in benchmark.SCENARIOS:
            guarded = benchmark.run_trial('C', scenario, 42)
            self.assertEqual(guarded['unauthorized_writes'], 0, scenario)
            self.assertEqual(guarded['false_blocks'], 0, scenario)
            self.assertEqual(guarded['kind'], 'scripted-mechanism')

