"""Analytic checks and real CLI paths for fixed-study empirical selection."""
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.selection import confidence_radius, empirical_cvar, select, structural_check


def structure():
    return [{'step': 'audit', 'allowed_privileges': ['read:project'],
             'required_privileges': ['read:project'], 'retained_privileges': ['read:project'],
             'required_dependencies': ['checker'], 'retained_nodes': [],
             'resolved_dependencies': ['checker']}]


def observations(n, loss=0.1):
    return [{'id': str(i), 'status': 'completed', 'loss': loss,
             'violations': {'safety': False}} for i in range(n)]


def regime():
    return {'task_family': 'audit', 'context_band': 'small', 'language': 'en',
            'risk_tier': 'standard'}


def study(n=1000, tier='op'):
    return {'schema_version': 2, 'study_id': 'synthetic-unit-test',
            'regime': regime(), 'tier': tier,
            'assumptions': {'fixed_candidates': True, 'fixed_sample_size': True,
                            'iid_within_cell': True},
            'delta': 0.05, 'loss_max': 1.0, 'loss_unit': 'normalized_operational_cost',
            'samples_per_cell': n,
            'requirements': {'safety': 0.1},
            'cells': {'h': {'model': 'test-model', 'group': 'test-group'}},
            'candidates': {
                name: {'artifact_sha256': digest * 64, 'structure': structure(),
                       'fallback_rank': rank, 'inv_verified': True,
                       'samples': {'h': observations(n, loss)}}
                for name, digest, loss, rank in
                [('compact', 'a', 0.1, 1), ('full', 'b', 0.3, 2)]}}


class SelectionTests(unittest.TestCase):
    def test_cheapest_certified_candidate_and_uniform_allocation(self):
        result = select(study())
        self.assertEqual(result['selected'], 'compact')
        self.assertEqual(result['confidence']['comparisons'], 4)
        self.assertEqual(result['confidence']['per_bound_delta'], 0.05 / 4)
        self.assertAlmostEqual(confidence_radius(1000, 0.0125), math.sqrt(math.log(160)/2000))
        self.assertEqual(result['scope']['decision_deficiency'], 'not certified')

    def test_rare_event_evidence_cannot_be_invented_from_five_successes(self):
        result = select(study(5))
        self.assertIsNone(result['selected'])
        self.assertEqual(result['action'], 'abstain')
        self.assertEqual(result['status'], 'no_certified_candidate')
        self.assertEqual(result['candidates']['compact']['status'], 'uncertified')

    def test_requirement_failure_excludes_cheap_candidate(self):
        data = study()
        for sample in data['candidates']['compact']['samples']['h']:
            sample['violations']['safety'] = True
        self.assertEqual(select(data)['selected'], 'full')

    def test_missing_cell_and_execution_error_do_not_get_filtered_bounds(self):
        for variant in ('missing', 'error'):
            with self.subTest(variant=variant):
                data = study()
                candidate = data['candidates']['compact']
                if variant == 'missing':
                    candidate['samples'] = {}
                else:
                    candidate['samples']['h'][0] = {
                        'id': '0', 'status': 'execution_error', 'reason': 'usage_limit_reached'}
                result = select(data)
                self.assertEqual(result['selected'], 'full')
                self.assertIsNone(result['candidates']['compact']['cells']['h']['bounds'])
                self.assertIsNone(result['candidates']['compact']['objective_upper'])
                if variant == 'error':
                    self.assertEqual(result['candidates']['compact']['cells']['h']['execution_errors'],
                                     [{'id': '0', 'reason': 'usage_limit_reached'}])

    def test_each_structural_invariant_rejects(self):
        mutations = [('retained_privileges', ['read:project', 'write:project'], 'authority_amplified'),
                     ('retained_privileges', [], 'required_authority_lost'),
                     ('resolved_dependencies', [], 'dependency_unresolved')]
        for field, value, invariant in mutations:
            with self.subTest(invariant=invariant):
                data = study()
                data['candidates']['compact']['structure'][0][field] = value
                result = select(data)
                self.assertEqual(result['selected'], 'full')
                report = result['candidates']['compact']
                self.assertEqual(report['status'], 'structurally_rejected')
                self.assertIn(invariant, [f['invariant'] for f in report['structure']['failures']])
                self.assertEqual(result['confidence']['comparisons'], 4)

    def test_missing_structural_evidence_is_uncertified(self):
        data = study()
        del data['candidates']['compact']['structure']
        self.assertEqual(select(data)['candidates']['compact']['status'], 'uncertified')

    def test_dependency_may_be_retained_instead_of_resolved(self):
        steps = structure()
        steps[0]['retained_nodes'] = ['checker']
        steps[0]['resolved_dependencies'] = []
        self.assertEqual(structural_check(steps)['status'], 'passed_declared_sets')

    def test_worst_cell_objective_not_pooled_average(self):
        data = study()
        data['cells']['other'] = {'model': 'other-model', 'group': 'test-group'}
        data['candidates']['compact']['samples']['other'] = observations(1000, 0.9)
        data['candidates']['full']['samples']['other'] = observations(1000, 0.3)
        self.assertEqual(select(data)['selected'], 'full')

    def test_requirement_in_one_cell_is_enough_to_block(self):
        data = study()
        data['cells']['other'] = {'model': 'other-model', 'group': 'test-group'}
        for name, candidate in data['candidates'].items():
            candidate['samples']['other'] = observations(1000, 0.1)
            if name == 'compact':
                for sample in candidate['samples']['other']:
                    sample['violations']['safety'] = True
        self.assertEqual(select(data)['selected'], 'full')

    def test_tail_fractional_mass_matches_variational_definition(self):
        losses = [0, 1, 3]
        nu = 0.5
        expected = min(z + sum(max(x-z, 0) for x in losses)/(3*(1-nu)) for z in losses)
        self.assertAlmostEqual(empirical_cvar(losses, nu), expected)
        self.assertAlmostEqual(expected, 7/3)
        self.assertEqual(empirical_cvar([1, 1, 1], 0.999), 1)
        self.assertEqual(empirical_cvar([0, 0, 1], 0.99), 1)

    def test_tail_constraint_and_allocation_are_enforced(self):
        data = study(10000)
        data['tail'] = {'nu': 0.5, 'budget': 0.4}
        losses = data['candidates']['compact']['samples']['h']
        for i, sample in enumerate(losses):
            sample['loss'] = 1 if i < 1000 else 0  # mean .1, CVaR at .5 is .2
        result = select(data)
        self.assertEqual(result['confidence']['comparisons'], 6)
        self.assertEqual(result['selected'], 'compact')
        data['tail']['budget'] = 0.25
        # compact passes while full (.3 constant) fails, regardless of full's lower variance.
        self.assertEqual(select(data)['selected'], 'compact')
        data['tail']['budget'] = 0.1
        self.assertIsNone(select(data)['selected'])
        data['tail'] = {'nu': 0.9, 'budget': 0.7}
        # The lower-mean candidate now fails its heavy tail; constant .3 remains eligible.
        self.assertEqual(select(data)['selected'], 'full')

    def test_extreme_tail_bound_clamps_to_known_loss_range(self):
        data = study()
        data['tail'] = {'nu': 0.9999, 'budget': 1}
        result = select(data)
        bound = result['candidates']['compact']['cells']['h']['bounds']['tail']
        self.assertEqual(bound['upper'], 1)
        self.assertLessEqual(bound['radius'], 1)

    def test_ties_are_stable_and_input_is_not_mutated(self):
        data = study()
        data['candidates']['full']['samples'] = copy.deepcopy(data['candidates']['compact']['samples'])
        before = copy.deepcopy(data)
        self.assertEqual(select(data)['selected'], 'compact')
        self.assertEqual(data, before)

    def test_threshold_equality_is_accepted(self):
        data = study()
        data['requirements']['safety'] = confidence_radius(1000, .05/4)
        self.assertEqual(select(data)['selected'], 'compact')

    def test_invalid_sampling_assumptions_are_not_certificates(self):
        for assumption in ('fixed_candidates', 'fixed_sample_size', 'iid_within_cell'):
            data = study(1)
            data['assumptions'][assumption] = False
            with self.assertRaises(ValueError):
                select(data)

    def test_missing_cross_product_pair_is_invalid(self):
        data = study(1)
        data['cells']['other'] = {'model': 'other-model', 'group': 'other-group'}
        with self.assertRaisesRegex(ValueError, 'Cartesian product'):
            select(data)

    def test_invalid_observations_and_unknown_metrics_fail_closed(self):
        mutations = [lambda s: s.update(loss=float('nan')),
                     lambda s: s.update(loss=float('inf')),
                     lambda s: s.update(loss=-1), lambda s: s.update(loss=1.01),
                     lambda s: s.update(loss=True), lambda s: s.update(violations={}),
                     lambda s: s.update(violations={'safety': 0}),
                     lambda s: s.update(violations={'safety': False, 'unknown': False}),
                     lambda s: s.update(status='unknown')]
        for mutate in mutations:
            data = study(1)
            mutate(data['candidates']['compact']['samples']['h'][0])
            with self.subTest(data=data), self.assertRaises(ValueError):
                select(data)

    def test_duplicate_observations_unknown_cells_and_extra_samples_are_invalid(self):
        for case in ('duplicate', 'unknown_cell', 'extra'):
            data = study(2)
            candidate = data['candidates']['compact']
            if case == 'duplicate':
                candidate['samples']['h'][1]['id'] = '0'
            elif case == 'unknown_cell':
                candidate['samples']['undeclared'] = []
            else:
                candidate['samples']['h'].append(candidate['samples']['h'][0])
            with self.subTest(case=case), self.assertRaises(ValueError):
                select(data)

    def test_invalid_study_parameters(self):
        for key, value in [('delta', 0), ('delta', 1), ('delta', True), ('loss_max', 0),
                           ('loss_max', float('inf')), ('samples_per_cell', True),
                           ('samples_per_cell', 0), ('schema_version', True),
                           ('schema_version', 1),
                           ('tier', 'experimental'), ('tier', ''), ('tier', None),
                           ('regime', {}), ('regime', None),
                           ('candidates', {}), ('cells', {}), ('requirements', {}),
                           ('loss_unit', ''), ('loss_unit', None)]:
            data = study(1)
            data[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                select(data)

    def test_invalid_regime_fields_and_ranks_fail_closed(self):
        data = study(1)
        data['regime']['language'] = ''
        with self.assertRaises(ValueError):
            select(data)
        for bad in (0, True, 1.5, '1'):
            data = study(1)
            data['candidates']['compact']['fallback_rank'] = bad
            with self.subTest(rank=bad), self.assertRaises(ValueError):
                select(data)
        data = study(1)
        data['candidates']['compact']['fallback_rank'] = 2
        with self.assertRaisesRegex(ValueError, 'duplicate fallback_rank'):
            select(data)

    def test_tie_prefers_lower_fallback_rank_over_name(self):
        data = study()
        data['candidates']['full']['samples'] = copy.deepcopy(data['candidates']['compact']['samples'])
        data['candidates']['full']['fallback_rank'] = 1
        data['candidates']['compact']['fallback_rank'] = 2
        result = select(data)
        self.assertEqual(result['selected'], 'full')
        self.assertEqual(result['deployment_order'], ['full', 'compact'])
        self.assertEqual(result['candidates']['full']['certificate']['fallback_next'], 'compact')
        self.assertEqual(result['candidates']['compact']['certificate']['fallback_next'], 'abstain')

    def test_certificate_binds_scope_thresholds_and_confidence(self):
        result = select(study())
        self.assertEqual(result['tier'], 'op')
        self.assertEqual(result['regime'], regime())
        self.assertEqual(result['deployment_order'], ['compact', 'full'])
        certificate = result['candidates']['compact']['certificate']
        self.assertEqual(certificate['candidate'], 'compact')
        self.assertTrue(certificate['admissible'])
        self.assertEqual(certificate['regime'], regime())
        self.assertEqual(certificate['thresholds']['requirements'], {'safety': 0.1})
        self.assertIn('per_bound_delta', certificate['confidence'])
        uncertified = select(study(5))['candidates']['compact']
        self.assertEqual(uncertified['status'], 'uncertified')
        self.assertNotIn('certificate', uncertified)

    def test_ds_tier_checks_attested_deficiency(self):
        data = study(tier='ds')
        self.assertEqual(select(data)['status'], 'no_certified_candidate')
        self.assertIn('deficiency:unattested',
                      select(data)['candidates']['compact']['reasons'])
        compact = data['candidates']['compact']
        compact['deficiency'] = {'upper': 0.05, 'threshold': 0.1}
        data['candidates']['full']['deficiency'] = {'upper': 0.05, 'threshold': 0.1}
        result = select(data)
        self.assertEqual(result['selected'], 'compact')
        self.assertEqual(result['confidence']['comparisons'], 6)
        self.assertEqual(result['scope']['decision_deficiency'],
                         'evaluator-attested, not independently certified')
        compact['deficiency'] = {'upper': 0.2, 'threshold': 0.1}
        result = select(data)
        self.assertEqual(result['selected'], 'full')
        self.assertIn('deficiency:upper_exceeds_threshold',
                      result['candidates']['compact']['reasons'])

    def test_op_tier_rejects_deficiency_attestation(self):
        data = study()
        data['candidates']['compact']['deficiency'] = {'upper': 0.0, 'threshold': 0.1}
        with self.assertRaisesRegex(ValueError, 'requires tier ds'):
            select(data)

    def test_missing_or_false_invariant_attestation_is_uncertified(self):
        data = study()
        del data['candidates']['compact']['inv_verified']
        result = select(data)
        self.assertEqual(result['selected'], 'full')
        self.assertIn('router:unverified',
                      result['candidates']['compact']['reasons'])
        data['candidates']['compact']['inv_verified'] = False
        result = select(data)
        self.assertIn('router:unverified',
                      result['candidates']['compact']['reasons'])
        data['candidates']['compact']['inv_verified'] = 1
        with self.assertRaises(ValueError):
            select(data)

    def test_bad_cfg_digest_fails_closed(self):
        data = study()
        data['candidates']['compact']['cfg_sha256'] = 'z' * 64
        with self.assertRaises(ValueError):
            select(data)
        data['candidates']['compact']['cfg_sha256'] = 'c' * 64
        certificate = select(data)['candidates']['compact']['certificate']
        self.assertEqual(certificate['cfg_sha256'], 'c' * 64)

    def refusal_study(self):
        data = study(5)
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256': 'd' * 64,
                           'inv_verified': True, 'refusal_only': True,
                           'terminal_cost': 0.5}
        return data

    def test_verified_refusal_is_selected_when_nothing_is_admissible(self):
        result = select(self.refusal_study())
        self.assertEqual(result['status'], 'refusal')
        self.assertEqual(result['selected'], 'refuse-only')
        self.assertEqual(result['action'], 'refuse')
        self.assertEqual(result['deployment_order'], [])
        self.assertEqual(result['refusal']['terminal_cost'], 0.5)
        self.assertIn('not asserted', result['refusal']['note'])
        # No bounds are claimed on the refusal router, so it costs no
        # multiplicity allocation beyond the ordinary comparisons.
        self.assertEqual(result['confidence']['comparisons'], 4)

    def test_refusal_without_admissible_set_still_abstains(self):
        result = select(study(5))
        self.assertEqual(result['status'], 'no_certified_candidate')
        self.assertIsNone(result['selected'])
        self.assertIsNone(result['refusal'])

    def test_evidence_modes_gate_certification(self):
        result = select(study())
        self.assertEqual(result['scope']['evidence'], {'reuse_mode': 'fresh'})
        self.assertEqual(result['candidates']['compact']['certificate']['evidence'],
                         {'reuse_mode': 'fresh'})
        data = study()
        data['evidence'] = {'reuse_mode': 'split'}
        with self.assertRaisesRegex(ValueError, 'partition_recorded'):
            select(data)
        data['evidence'] = {'reuse_mode': 'split', 'partition_recorded': True}
        self.assertEqual(select(data)['selected'], 'compact')
        data = study()
        data['evidence'] = {'reuse_mode': 'adaptive'}
        with self.assertRaisesRegex(ValueError, 'adaptive_coverage'):
            select(data)
        data['evidence'] = {'reuse_mode': 'adaptive',
                            'adaptive_coverage': {'procedure': 'holdout-b',
                                                  'certificate_sha256': 'e' * 64}}
        self.assertEqual(select(data)['selected'], 'compact')
        for bad in ({'reuse_mode': 'recycled'}, {'reuse_mode': 'fresh', 'extra': 1},
                    {'partition_recorded': True},
                    {'reuse_mode': 'adaptive',
                     'adaptive_coverage': {'procedure': '', 'certificate_sha256': 'e' * 64}},
                    {'reuse_mode': 'adaptive',
                     'adaptive_coverage': {'procedure': 'holdout-b',
                                           'certificate_sha256': 'zz'}}):
            data = study()
            data['evidence'] = bad
            with self.subTest(evidence=bad), self.assertRaises(ValueError):
                select(data)

    def test_invalid_refusal_fails_closed(self):
        for key, value in [('router_id', ''), ('artifact_sha256', 'zz'),
                           ('inv_verified', False), ('inv_verified', 1),
                           ('refusal_only', False), ('refusal_only', 1),
                           ('terminal_cost', -1), ('terminal_cost', 1.5)]:
            data = self.refusal_study()
            data['refusal'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                select(data)
        data = self.refusal_study()
        del data['refusal']['terminal_cost']
        with self.assertRaises(ValueError):
            select(data)


class SelectionCLITests(unittest.TestCase):
    def invoke(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'study.json'
            path.write_text(text, encoding='utf-8')
            raw = path.read_bytes()
            result = subprocess.run([sys.executable, str(ROOT/'scripts/skillwren.py'),
                                     'select', str(path)], capture_output=True, text=True)
            self.assertEqual(path.read_bytes(), raw)
            return result, hashlib.sha256(raw).hexdigest()

    def test_selected_exit_and_input_hash(self):
        result, digest = self.invoke(json.dumps(study()))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['selected'], 'compact')
        self.assertEqual(report['input_sha256'], digest)

    def test_uncertified_exit_is_distinct_from_invalid_input(self):
        result, _ = self.invoke(json.dumps(study(5)))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(result.stdout)['action'], 'abstain')

    def test_verified_refusal_exits_zero_with_refuse_action(self):
        data = study(5)
        data['refusal'] = {'router_id': 'refuse-only', 'artifact_sha256': 'd' * 64,
                           'inv_verified': True, 'refusal_only': True,
                           'terminal_cost': 0.5}
        result, _ = self.invoke(json.dumps(data))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['action'], 'refuse')
        self.assertEqual(report['selected'], 'refuse-only')
        for text in ('{', '{"schema_version": 1, "schema_version": 2}'):
            result, _ = self.invoke(text)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('skillwren select:', result.stderr)


if __name__ == '__main__':
    unittest.main()
