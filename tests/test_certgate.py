"""Host-side DPCC deployment gate: certificate binding and negative paths."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.certgate import verify
from skillwren.guard import Controller, Denied, file_digest
from skillwren.selection import select


ARTIFACTS = {'compact': b'compact-artifact-v1', 'full': b'full-artifact-v1'}


def regime():
    return {'task_family': 'audit', 'context_band': 'small', 'language': 'en',
            'risk_tier': 'standard'}


def structure():
    return [{'step': 'audit', 'allowed_privileges': ['read:project'],
             'required_privileges': ['read:project'], 'retained_privileges': ['read:project'],
             'required_dependencies': ['checker'], 'retained_nodes': [],
             'resolved_dependencies': ['checker']}]


def observations(n, loss=0.1):
    return [{'id': str(i), 'status': 'completed', 'loss': loss,
             'violations': {'safety': False}} for i in range(n)]


def study(n=1000):
    digests = {name: hashlib.sha256(blob).hexdigest() for name, blob in ARTIFACTS.items()}
    return {'schema_version': 2, 'study_id': 'gate-unit-test',
            'regime': regime(), 'tier': 'op',
            'assumptions': {'fixed_candidates': True, 'fixed_sample_size': True,
                            'iid_within_cell': True},
            'delta': 0.05, 'loss_max': 1.0, 'loss_unit': 'u', 'samples_per_cell': n,
            'requirements': {'safety': 0.5},
            'cells': {'h': {'model': 'm', 'group': 'g'}},
            'candidates': {
                name: {'artifact_sha256': digests[name], 'structure': structure(),
                       'fallback_rank': rank, 'inv_verified': True,
                       'cfg_sha256': 'c' * 64,
                       'samples': {'h': observations(n, loss)}}
                for name, rank, loss in [('compact', 1, 0.1), ('full', 2, 0.3)]}}


def gate(report, study, cfg='c' * 64, monitor=True, policy=True, artifacts=None,
         reg=None, study_sha256=None):
    return verify(report, artifacts if artifacts is not None else dict(ARTIFACTS),
                  reg if reg is not None else regime(), cfg, monitor, policy,
                  study=study, study_sha256=study_sha256)


class CertgateTests(unittest.TestCase):
    def test_fully_bound_certificate_allows(self):
        data = study()
        result = gate(select(data), data)
        self.assertEqual(result['verdict'], 'allow')
        self.assertEqual(result['selected'], 'compact')
        self.assertEqual(result['action'], 'recommend')
        self.assertEqual(result['reasons'], [])
        self.assertEqual(result['checked']['chain'], ['compact', 'full'])

    def test_altered_artifact_denies(self):
        poisoned = dict(ARTIFACTS, compact=b'compact-artifact-EVIL')
        data = study()
        result = gate(select(data), data, artifacts=poisoned)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('artifact:mismatch:compact', result['reasons'])

    def test_missing_artifact_denies(self):
        data = study()
        result = gate(select(data), data, artifacts={'compact': ARTIFACTS['compact']})
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('artifact:missing:full', result['reasons'])

    def test_regime_mismatch_denies(self):
        reg = regime()
        reg['risk_tier'] = 'critical'
        data = study()
        result = gate(select(data), data, reg=reg)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('regime:mismatch', result['reasons'])

    def test_config_mismatch_and_unbound_deny(self):
        data = study()
        result = gate(select(data), data, cfg='d' * 64)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('cfg:unbound-or-mismatch', result['reasons'])
        data = study()
        del data['candidates']['compact']['cfg_sha256']
        del data['candidates']['full']['cfg_sha256']
        result = gate(select(data), data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('cfg:unbound-or-mismatch', result['reasons'])

    def test_revoked_evidence_denies(self):
        data = study()
        report = select(data)
        report['selected'] = 'full'
        result = gate(report, data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('selected:inconsistent', result['reasons'])
        data = study()
        report = select(data)
        report['candidates']['compact']['status'] = 'inadmissible'
        result = gate(report, data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('selected:not-admissible', result['reasons'])

    def test_broken_fallback_link_denies(self):
        data = study()
        report = select(data)
        report['candidates']['compact']['certificate']['fallback_next'] = 'ghost'
        result = gate(report, data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('fallback:unknown:ghost', result['reasons'])

    def test_stale_fallback_certificate_denies(self):
        data = study()
        report = select(data)
        report['candidates']['full']['certificate']['regime'] = dict(regime(), language='fr')
        result = gate(report, data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('fallback:regime:full', result['reasons'])
        data = study()
        report = select(data)
        report['candidates']['full']['certificate']['cfg_sha256'] = 'd' * 64
        result = gate(report, data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('fallback:cfg:full', result['reasons'])

    def test_monitor_and_policy_gates_deny(self):
        data = study()
        result = gate(select(data), data, monitor=False)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('monitor:not-passing', result['reasons'])
        data = study()
        result = gate(select(data), data, policy=False)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('policy:not-allowing', result['reasons'])

    def test_unrecorded_hash_with_supplied_bytes_denies(self):
        data = study()
        report = select(data)
        self.assertNotIn('input_sha256', report)
        result = gate(report, data, study_sha256='c' * 64)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('study:unbound', result['reasons'])

    def test_invalid_inputs_fail_closed(self):
        data = study()
        report = select(data)
        with self.assertRaises(ValueError):
            gate('nope', data)
        with self.assertRaises(ValueError):
            gate(report, data, cfg='zz')
        with self.assertRaises(ValueError):
            gate(report, data, reg={})

    def test_coordinated_report_rewrite_denied_without_matching_study(self):
        data = study()
        report = select(data)
        report['selected'] = 'full'
        report['candidates']['full']['objective_mean'] = 0.01
        report['candidates']['compact']['objective_mean'] = 0.99
        result = gate(report, data)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('report:inauthentic', result['reasons'])

    def test_missing_or_invalid_study_denies(self):
        data = study()
        report = select(data)
        result = gate(report, None)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('study:missing', result['reasons'])
        broken = dict(data)
        broken['requirements'] = {}
        result = gate(report, broken)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('study:invalid', result['reasons'])

    def test_study_bytes_must_match_report_input_hash(self):
        data = study()
        report = dict(select(data))
        report['input_sha256'] = 'e' * 64
        result = gate(report, data, study_sha256='f' * 64)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('study:unbound', result['reasons'])
        raw = json.dumps(data, sort_keys=True).encode()
        report['input_sha256'] = hashlib.sha256(raw).hexdigest()
        result = gate(report, data, study_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['verdict'], 'allow')

    def test_verified_refusal_refuses_never_allows(self):
        data = study(5)
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256':
                           hashlib.sha256(b'refuse').hexdigest(),
                           'inv_verified': True, 'refusal_only': True, 'terminal_cost': 0.5}
        report = select(data)
        result = verify(report, {'refuse-only': b'refuse'}, regime(), 'c' * 64, True, True,
                        study=data)
        self.assertEqual(result['verdict'], 'refuse')
        self.assertEqual(result['action'], 'refuse')
        poisoned = verify(report, {'refuse-only': b'tampered'}, regime(), 'c' * 64,
                          True, True, study=data)
        self.assertEqual(poisoned['verdict'], 'deny')
        self.assertIn('artifact:mismatch:refuse-only', poisoned['reasons'])


class CertgateCLITests(unittest.TestCase):
    def invoke(self, report, study_data, artifacts, args, tamper_study=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            std = root / 'study.json'
            std.write_bytes(json.dumps(study_data, sort_keys=True).encode())
            report = dict(report)
            report['input_sha256'] = hashlib.sha256(std.read_bytes()).hexdigest()
            if tamper_study:
                with open(std, 'ab') as handle:
                    handle.write(b' ')
            rep = root / 'report.json'
            rep.write_text(json.dumps(report), encoding='utf-8')
            adir = root / 'artifacts'
            adir.mkdir()
            for name, blob in artifacts.items():
                (adir / name).write_bytes(blob)
            cmd = [sys.executable, str(ROOT / 'scripts/skillwren.py'), 'certgate', str(rep),
                   '--study', str(std), '--artifacts', str(adir),
                   '--regime', json.dumps(regime()), '--cfg', 'c' * 64] + args
            return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_allow_refuse_and_deny_exits(self):
        data = study()
        report = select(data)
        allowed = self.invoke(report, data, ARTIFACTS, ['--monitor-pass', '--policy-allows'])
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(json.loads(allowed.stdout)['verdict'], 'allow')
        denied = self.invoke(report, data, ARTIFACTS, [])
        self.assertEqual(denied.returncode, 1)
        self.assertEqual(json.loads(denied.stdout)['verdict'], 'deny')
        data = study(5)
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256':
                           hashlib.sha256(b'refuse').hexdigest(),
                           'inv_verified': True, 'refusal_only': True, 'terminal_cost': 0.5}
        refused = self.invoke(select(data), data, {'refuse-only': b'refuse'},
                              ['--monitor-pass', '--policy-allows'])
        self.assertEqual(refused.returncode, 3, refused.stderr)
        self.assertEqual(json.loads(refused.stdout)['verdict'], 'refuse')

    def test_cli_tampered_study_file_denies(self):
        data = study()
        report = select(data)
        mismatched = self.invoke(report, data, ARTIFACTS,
                                 ['--monitor-pass', '--policy-allows'],
                                 tamper_study=True)
        self.assertEqual(mismatched.returncode, 1)
        self.assertIn('study:unbound', json.loads(mismatched.stdout)['reasons'])

    def test_cli_invalid_input_is_exit_2(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bad = root / 'report.json'
            bad.write_text('{', encoding='utf-8')
            std = root / 'study.json'
            std.write_text('{}', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts/skillwren.py'), 'certgate', str(bad),
                 '--study', str(std), '--artifacts', str(root),
                 '--regime', '{}', '--cfg', 'c' * 64],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('skillwren certgate:', result.stderr)


PYTHON = str(Path(sys.executable).resolve())


class GuardDpccTests(unittest.TestCase):
    COMPACT = b'{"debug": false, "skill": "concise-v2"}'
    FULL = b'{"debug": false, "skill": "full-v1"}'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.artifacts = {'compact': self.COMPACT, 'full': self.FULL}
        self.digests = {name: hashlib.sha256(blob).hexdigest()
                        for name, blob in self.artifacts.items()}
        self.study_data = self.make_study()
        self.report = select(self.study_data)
        self.study_file = self.root / 'study.json'
        self.study_file.write_bytes(json.dumps(self.study_data, sort_keys=True).encode())
        self.report['input_sha256'] = hashlib.sha256(
            self.study_file.read_bytes()).hexdigest()
        self.report_file = self.root / 'report.json'
        self.report_file.write_text(json.dumps(self.report), encoding='utf-8')
        self.adir = self.root / 'artifacts'
        self.adir.mkdir()
        for name, blob in self.artifacts.items():
            (self.adir / name).write_bytes(blob)
        self.target = self.root / 'deployed.json'
        self.monitor_script = str(self.root / 'verify_monitor.py')
        Path(self.monitor_script).write_bytes(
            (ROOT / 'examples/guard/verify_monitor.py').read_bytes())
        self.write_script = str(ROOT / 'examples/guard/verify_config.py')
        self.policy = self.make_policy()
        self.guard = Controller(self.policy)

    def make_study(self, n=50):
        return {'schema_version': 2, 'study_id': 'gate-guard-test',
                'regime': regime(), 'tier': 'op',
                'assumptions': {'fixed_candidates': True, 'fixed_sample_size': True,
                                'iid_within_cell': True},
                'delta': 0.05, 'loss_max': 1.0, 'loss_unit': 'u', 'samples_per_cell': n,
                'requirements': {'safety': 0.5},
                'cells': {'h': {'model': 'm', 'group': 'g'}},
                'candidates': {
                    name: {'artifact_sha256': self.digests[name], 'structure': structure(),
                           'fallback_rank': rank, 'inv_verified': True,
                           'cfg_sha256': 'c' * 64,
                           'samples': {'h': observations(n, loss)}}
                    for name, rank, loss in [('compact', 1, 0.1), ('full', 2, 0.3)]}}

    def make_policy(self, **override):
        dpcc = {'report': str(self.report_file), 'study': str(self.study_file),
                'artifacts': str(self.adir), 'regime': regime(), 'cfg': 'c' * 64,
                'monitor': 'check#monitor'}
        dpcc.update(override)
        return {'version': 1, 'operations': {
            'check#monitor': {
                'argv': [PYTHON, self.monitor_script],
                'pins': {PYTHON: file_digest(PYTHON),
                         self.monitor_script: file_digest(self.monitor_script)},
                'timeout': 5},
            'deploy#artifact': {
                'target': str(self.target),
                'argv': [PYTHON, '-I', self.write_script],
                'pins': {PYTHON: file_digest(PYTHON),
                         self.write_script: file_digest(self.write_script)},
                'timeout': 5, 'dpcc': dpcc}}}

    def run_monitor(self, guard=None):
        guard = guard or self.guard
        guard.handle({'action': 'verify', 'operation': 'check#monitor',
                      'content': '{"ping": true}'})

    def verify_write(self, guard=None, content=None):
        guard = guard or self.guard
        guard.handle({'action': 'verify', 'operation': 'deploy#artifact',
                      'content': (content or self.COMPACT).decode()})

    def write(self, guard=None, content=None):
        guard = guard or self.guard
        return guard.handle({'action': 'write', 'operation': 'deploy#artifact',
                             'content': (content or self.COMPACT).decode()})

    def test_certified_write_deploys_exact_artifact(self):
        self.run_monitor()
        self.verify_write()
        result = self.write()
        self.assertEqual(result['written'], 'deploy#artifact')
        self.assertEqual(self.target.read_bytes(), self.COMPACT)

    def test_uncertified_content_denied_despite_verification(self):
        other = b'{"debug": false, "skill": "other"}'
        self.run_monitor()
        self.verify_write(content=other)
        with self.assertRaisesRegex(Denied, 'not the certified artifact'):
            self.write(content=other)
        self.assertFalse(self.target.exists())

    def test_monitor_must_pass_first(self):
        self.verify_write()
        with self.assertRaisesRegex(Denied, 'dpcc monitor has not passed'):
            self.write()

    def test_tampered_report_denies_write(self):
        tampered = dict(self.report)
        tampered['selected'] = 'full'
        self.report_file.write_text(json.dumps(tampered), encoding='utf-8')
        self.run_monitor()
        self.verify_write()
        with self.assertRaisesRegex(Denied, 'dpcc gate denied'):
            self.write()

    def test_tampered_artifact_denies_write(self):
        (self.adir / 'compact').write_bytes(b'{"debug": false, "skill": "EVIL"}')
        self.run_monitor()
        self.verify_write()
        with self.assertRaisesRegex(Denied, 'dpcc gate denied'):
            self.write()

    def test_regime_mismatch_denies_write(self):
        bad = dict(regime(), language='fr')
        self.guard = Controller(self.make_policy(regime=bad))
        self.run_monitor()
        self.verify_write()
        with self.assertRaisesRegex(Denied, 'dpcc gate denied'):
            self.write()

    def test_refusal_report_denies_write(self):
        data = self.make_study(n=5)
        for candidate in data['candidates'].values():
            candidate['samples']['h'] = []
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256':
                           hashlib.sha256(b'refuse').hexdigest(),
                           'inv_verified': True, 'refusal_only': True,
                           'terminal_cost': 0.5}
        report = select(data)
        self.assertEqual(report['status'], 'refusal')
        report['input_sha256'] = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()).hexdigest()
        (self.root / 'study.json').write_bytes(json.dumps(data, sort_keys=True).encode())
        self.report_file.write_text(json.dumps(report), encoding='utf-8')
        (self.adir / 'refuse-only').write_bytes(b'refuse')
        self.run_monitor()
        self.verify_write(content=b'{"debug": false}')
        with self.assertRaisesRegex(Denied, 'dpcc gate denied'):
            self.write(content=b'{"debug": false}')

    def test_evidence_store_tampering_denies_write(self):
        report = dict(self.report)
        raw = self.study_file.read_bytes()
        report['input_sha256'] = hashlib.sha256(raw).hexdigest()
        self.report_file.write_text(json.dumps(report), encoding='utf-8')
        self.study_file.write_bytes(raw + b' ')
        self.run_monitor()
        self.verify_write()
        with self.assertRaisesRegex(Denied, 'dpcc gate denied'):
            self.write()

    def test_missing_evidence_denies_write(self):
        (self.adir / 'full').unlink()
        self.run_monitor()
        self.verify_write()
        with self.assertRaisesRegex(Denied, 'dpcc gate denied'):
            self.write()

    def test_tampered_monitor_denies_write(self):
        self.run_monitor()
        self.verify_write()
        (self.root / 'verify_monitor.py').write_bytes(b'import sys; sys.exit(1)\n')
        with self.assertRaisesRegex(Denied, 'verifier'):
            self.write()

    def test_snapshot_confirmation_denies_changed_evidence(self):
        self.run_monitor()
        self.verify_write()
        op = self.guard.operations['deploy#artifact']
        snapshot = self.guard._enforce_dpcc(op, self.COMPACT)
        self.guard._confirm_dpcc_snapshot(op, self.COMPACT, snapshot)
        (self.adir / 'full').write_bytes(b'{"debug": false, "skill": "CHANGED"}')
        with self.assertRaisesRegex(Denied, 'changed before commit'):
            self.guard._confirm_dpcc_snapshot(op, self.COMPACT, snapshot)

    def test_dpcc_binding_validated_at_policy_load(self):
        for mutate in (lambda d: d.pop('cfg'), lambda d: d.update(monitor='deploy#artifact'),
                       lambda d: d.update(regime='everywhere'),
                       lambda d: d.update(report='relative/path.json')):
            dpcc = {'report': str(self.report_file), 'study': str(self.study_file),
                    'artifacts': str(self.adir), 'regime': regime(), 'cfg': 'c' * 64,
                    'monitor': 'check#monitor'}
            mutate(dpcc)
            policy = dict(self.policy)
            policy['operations'] = dict(self.policy['operations'])
            policy['operations']['deploy#artifact'] = dict(
                self.policy['operations']['deploy#artifact'], dpcc=dpcc)
            with self.subTest(dpcc=dpcc), self.assertRaises(Denied):
                Controller(policy)


if __name__ == '__main__':
    unittest.main()
