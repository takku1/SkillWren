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


def gate(report, cfg='c' * 64, monitor=True, policy=True, artifacts=None, reg=None):
    return verify(report, artifacts if artifacts is not None else dict(ARTIFACTS),
                  reg if reg is not None else regime(), cfg, monitor, policy)


class CertgateTests(unittest.TestCase):
    def test_fully_bound_certificate_allows(self):
        result = gate(select(study()))
        self.assertEqual(result['verdict'], 'allow')
        self.assertEqual(result['selected'], 'compact')
        self.assertEqual(result['action'], 'recommend')
        self.assertEqual(result['reasons'], [])
        self.assertEqual(result['checked']['chain'], ['compact', 'full'])

    def test_altered_artifact_denies(self):
        poisoned = dict(ARTIFACTS, compact=b'compact-artifact-EVIL')
        result = gate(select(study()), artifacts=poisoned)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('artifact:mismatch:compact', result['reasons'])

    def test_missing_artifact_denies(self):
        result = gate(select(study()), artifacts={'compact': ARTIFACTS['compact']})
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('artifact:missing:full', result['reasons'])

    def test_regime_mismatch_denies(self):
        reg = regime()
        reg['risk_tier'] = 'critical'
        result = gate(select(study()), reg=reg)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('regime:mismatch', result['reasons'])

    def test_config_mismatch_and_unbound_deny(self):
        result = gate(select(study()), cfg='d' * 64)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('cfg:unbound-or-mismatch', result['reasons'])
        data = study()
        del data['candidates']['compact']['cfg_sha256']
        del data['candidates']['full']['cfg_sha256']
        result = gate(select(data))
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('cfg:unbound-or-mismatch', result['reasons'])

    def test_revoked_evidence_denies(self):
        report = select(study())
        report['selected'] = 'full'
        result = gate(report)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('selected:inconsistent', result['reasons'])
        report = select(study())
        report['candidates']['compact']['status'] = 'inadmissible'
        result = gate(report)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('selected:not-admissible', result['reasons'])

    def test_broken_fallback_link_denies(self):
        report = select(study())
        report['candidates']['compact']['certificate']['fallback_next'] = 'ghost'
        result = gate(report)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('fallback:unknown:ghost', result['reasons'])

    def test_monitor_and_policy_gates_deny(self):
        result = gate(select(study()), monitor=False)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('monitor:not-passing', result['reasons'])
        result = gate(select(study()), policy=False)
        self.assertEqual(result['verdict'], 'deny')
        self.assertIn('policy:not-allowing', result['reasons'])

    def test_invalid_inputs_fail_closed(self):
        report = select(study())
        with self.assertRaises(ValueError):
            gate('nope')
        with self.assertRaises(ValueError):
            gate(report, cfg='zz')
        with self.assertRaises(ValueError):
            gate(report, reg={})

    def test_verified_refusal_refuses_never_allows(self):
        data = study(5)
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256':
                           hashlib.sha256(b'refuse').hexdigest(),
                           'inv_verified': True, 'refusal_only': True, 'terminal_cost': 0.5}
        report = select(data)
        result = verify(report, {'refuse-only': b'refuse'}, regime(), 'c' * 64, True, True)
        self.assertEqual(result['verdict'], 'refuse')
        self.assertEqual(result['action'], 'refuse')
        poisoned = verify(report, {'refuse-only': b'tampered'}, regime(), 'c' * 64,
                          True, True)
        self.assertEqual(poisoned['verdict'], 'deny')
        self.assertIn('artifact:mismatch:refuse-only', poisoned['reasons'])


class CertgateCLITests(unittest.TestCase):
    def invoke(self, report, artifacts, args):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rep = root / 'report.json'
            rep.write_text(json.dumps(report), encoding='utf-8')
            adir = root / 'artifacts'
            adir.mkdir()
            for name, blob in artifacts.items():
                (adir / name).write_bytes(blob)
            cmd = [sys.executable, str(ROOT / 'scripts/skillwren.py'), 'certgate', str(rep),
                   '--artifacts', str(adir), '--regime', json.dumps(regime()),
                   '--cfg', 'c' * 64] + args
            return subprocess.run(cmd, capture_output=True, text=True)

    def test_cli_allow_refuse_and_deny_exits(self):
        report = select(study())
        allowed = self.invoke(report, ARTIFACTS, ['--monitor-pass', '--policy-allows'])
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(json.loads(allowed.stdout)['verdict'], 'allow')
        denied = self.invoke(report, ARTIFACTS, [])
        self.assertEqual(denied.returncode, 1)
        self.assertEqual(json.loads(denied.stdout)['verdict'], 'deny')
        data = study(5)
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256':
                           hashlib.sha256(b'refuse').hexdigest(),
                           'inv_verified': True, 'refusal_only': True, 'terminal_cost': 0.5}
        refused = self.invoke(select(data), {'refuse-only': b'refuse'},
                              ['--monitor-pass', '--policy-allows'])
        self.assertEqual(refused.returncode, 0, refused.stderr)
        self.assertEqual(json.loads(refused.stdout)['verdict'], 'refuse')

    def test_cli_invalid_input_is_exit_2(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bad = root / 'report.json'
            bad.write_text('{', encoding='utf-8')
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts/skillwren.py'), 'certgate', str(bad),
                 '--artifacts', str(root), '--regime', '{}', '--cfg', 'c' * 64],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('skillwren certgate:', result.stderr)


if __name__ == '__main__':
    unittest.main()
