"""Fixed-study empirical selection; declarations are not authenticated proofs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


REQUIREMENTS = {'safety', 'omission', 'task', 'proc', 'sem', 'anchor', 'fidelity'}
ASSUMPTIONS = {'fixed_candidates', 'fixed_sample_size', 'iid_within_cell'}


def _object(value, required, optional=(), label='object'):
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be an object')
    missing, extra = set(required) - value.keys(), value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f'{label}: missing keys {sorted(missing)}, unknown keys {sorted(extra)}')


def _name(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be a nonempty string')
    return value


def _number(value, low, high, label):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not low <= value <= high):
        raise ValueError(f'{label} must be finite in [{low}, {high}]')
    return value


def _atoms(value, label):
    if not isinstance(value, list):
        raise ValueError(f'{label} must be a list')
    for atom in value:
        _name(atom, label)
    if len(set(value)) != len(value):
        raise ValueError(f'{label} contains duplicates')
    return set(value)


def _hex64(value, label):
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in '0123456789abcdef' for c in value)):
        raise ValueError(f'{label} must be 64 lowercase hexadecimal characters')
    return value


def structural_check(steps):
    """Check only declared sets; no claim of extraction accuracy or enforcement."""
    if steps is None:
        return {'status': 'missing', 'failures': []}
    if not isinstance(steps, list) or not steps:
        raise ValueError('structure must be a nonempty step list or null')
    fields = {'step', 'allowed_privileges', 'required_privileges', 'retained_privileges',
              'required_dependencies', 'retained_nodes', 'resolved_dependencies'}
    failures, names = [], set()
    for step in steps:
        _object(step, fields, label='structural step')
        name = _name(step['step'], 'step')
        if name in names:
            raise ValueError(f'duplicate structural step: {name}')
        names.add(name)
        sets = {k: _atoms(step[k], k) for k in fields - {'step'}}
        checks = {
            'authority_amplified': sets['retained_privileges'] - sets['allowed_privileges'],
            'required_authority_lost': sets['required_privileges'] - sets['retained_privileges'],
            'dependency_unresolved': sets['required_dependencies'] - (
                sets['retained_nodes'] | sets['resolved_dependencies']),
        }
        for invariant, atoms in checks.items():
            if atoms:
                failures.append({'step': name, 'invariant': invariant, 'atoms': sorted(atoms)})
    return {'status': 'rejected' if failures else 'passed_declared_sets', 'failures': failures}


def confidence_radius(n, eta):
    if type(n) is not int or n <= 0 or not 0 < eta < 1:
        raise ValueError('confidence radius needs positive integer n and 0 < eta < 1')
    return math.sqrt((math.log(2) - math.log(eta)) / (2 * n))


def empirical_cvar(losses, nu):
    """Upper-tail mean with fractional boundary mass, including discrete losses."""
    _number(nu, 0, 1, 'nu')
    if not 0 < nu < 1 or not losses:
        raise ValueError('CVaR needs observations and 0 < nu < 1')
    for loss in losses:
        _number(loss, 0, float('inf'), 'loss')
    mass = (1 - nu) * len(losses)
    remaining, terms = mass, []
    for loss in sorted(losses, reverse=True):
        weight = min(1.0, remaining)
        terms.append(loss * (weight / mass))
        remaining -= weight
        if remaining <= 0:
            break
    return math.fsum(terms)


def _interval(mean, radius, maximum):
    return {'estimate': mean, 'radius': radius,
            'lower': max(0.0, mean - radius), 'upper': min(maximum, mean + radius)}


def _observations(samples, requirements, maximum, planned):
    if not isinstance(samples, list) or len(samples) > planned:
        raise ValueError('observations must be a list no longer than samples_per_cell')
    seen, completed, errors = set(), [], []
    for sample in samples:
        if not isinstance(sample, dict):
            raise ValueError('observation must be an object')
        if sample.get('status') == 'execution_error':
            _object(sample, {'id', 'status', 'reason'}, label='execution error')
            _name(sample['reason'], 'execution error reason')
            errors.append({'id': sample['id'], 'reason': sample['reason']})
        elif sample.get('status') == 'completed':
            _object(sample, {'id', 'status', 'loss', 'violations'}, label='completed observation')
            _number(sample['loss'], 0, maximum, 'loss')
            _object(sample['violations'], requirements, label='violations')
            if any(type(v) is not bool for v in sample['violations'].values()):
                raise ValueError('violation indicators must be JSON booleans')
            completed.append(sample)
        else:
            raise ValueError('observation status must be completed or execution_error')
        name = _name(sample['id'], 'observation id')
        if name in seen:
            raise ValueError(f'duplicate observation id in a cell: {name}')
        seen.add(name)
    return completed, errors


def select(study):
    """Return an auditable recommendation, never execute a candidate or fallback."""
    _object(study, {'schema_version', 'study_id', 'regime', 'tier', 'assumptions', 'delta',
                    'loss_max', 'loss_unit', 'samples_per_cell', 'requirements', 'cells',
                    'candidates'}, {'tail', 'refusal', 'evidence', 'cell_weights'})
    if type(study['schema_version']) is not int or study['schema_version'] != 2:
        raise ValueError('schema_version must be 2')
    _name(study['study_id'], 'study_id')
    regime = study['regime']
    _object(regime, {'task_family', 'context_band', 'language', 'risk_tier'}, label='regime')
    for field in ('task_family', 'context_band', 'language', 'risk_tier'):
        _name(regime[field], f'regime.{field}')
    tier = study['tier']
    if tier not in ('op', 'ds'):
        raise ValueError("tier must be 'op' or 'ds'")
    evidence = study.get('evidence')
    if evidence is None:
        evidence = {'reuse_mode': 'fresh'}
    else:
        _object(evidence, {'reuse_mode'}, {'partition_recorded', 'adaptive_coverage'},
                label='evidence')
    mode = evidence['reuse_mode']
    if mode not in ('fresh', 'split', 'adaptive'):
        raise ValueError("evidence.reuse_mode must be 'fresh', 'split' or 'adaptive'")
    if mode == 'split':
        if evidence.get('partition_recorded') is not True:
            raise ValueError('split reuse requires partition_recorded true')
    if mode == 'adaptive':
        coverage = evidence.get('adaptive_coverage')
        if not isinstance(coverage, dict):
            raise ValueError('adaptive reuse requires an adaptive_coverage certificate')
        _object(coverage, {'procedure', 'certificate_sha256'}, label='adaptive_coverage')
        _name(coverage['procedure'], 'adaptive_coverage.procedure')
        _hex64(coverage['certificate_sha256'], 'adaptive_coverage.certificate_sha256')
    _name(study['loss_unit'], 'loss_unit')
    _object(study['assumptions'], ASSUMPTIONS, label='assumptions')
    if any(v is not True for v in study['assumptions'].values()):
        raise ValueError('schema 2 requires fixed candidates, fixed sample size and IID within cells')
    delta = _number(study['delta'], 0, 1, 'delta')
    if not 0 < delta < 1:
        raise ValueError('delta must be strictly between 0 and 1')
    maximum = _number(study['loss_max'], 0, float('inf'), 'loss_max')
    if maximum <= 0:
        raise ValueError('loss_max must be positive')
    planned = study['samples_per_cell']
    if type(planned) is not int or planned < 1:
        raise ValueError('samples_per_cell must be a positive integer')
    requirements = study['requirements']
    if not isinstance(requirements, dict) or not requirements or requirements.keys() - REQUIREMENTS:
        raise ValueError('requirements must name a nonempty subset of supported requirement types')
    for key, tolerance in requirements.items():
        _number(tolerance, 0, 1, f'requirements.{key}')
    cells = study['cells']
    if not isinstance(cells, dict) or not cells:
        raise ValueError('cells must be a nonempty object')
    pairs = set()
    for name, cell in cells.items():
        _name(name, 'cell id')
        _object(cell, {'model', 'group'}, label='cell')
        pair = (_name(cell['model'], 'model'), _name(cell['group'], 'group'))
        if pair in pairs:
            raise ValueError('duplicate model-group pair')
        pairs.add(pair)
    # H is explicitly a Cartesian product, not a list that silently omits hard groups.
    if len(pairs) != len({m for m, _ in pairs}) * len({g for _, g in pairs}):
        raise ValueError('cells must contain the complete declared model-group Cartesian product')
    # Cell weights map the study objective onto the intended deployment
    # distribution. Uniform by default; an explicit map must name every
    # cell exactly once and sum to one. Weights change only the objective
    # aggregation, never the per-cell bounds or their multiplicity cost.
    raw_weights = study.get('cell_weights')
    if raw_weights is None:
        weights = {name: 1 / len(cells) for name in sorted(cells)}
    else:
        _object(raw_weights, set(cells), label='cell_weights')
        weights = {}
        for name in sorted(raw_weights):
            weights[name] = _number(raw_weights[name], 0, 1, f'cell_weights.{name}')
        if abs(math.fsum(weights.values()) - 1) > 1e-9:
            raise ValueError('cell_weights must sum to 1')
    tail = study.get('tail')
    if tail is not None:
        _object(tail, {'nu', 'budget'}, label='tail')
        _number(tail['nu'], 0, 1, 'tail.nu')
        if not 0 < tail['nu'] < 1:
            raise ValueError('tail.nu must be strictly between 0 and 1')
        _number(tail['budget'], 0, maximum, 'tail.budget')
    refusal = study.get('refusal')
    if refusal is not None:
        _object(refusal, {'router_id', 'artifact_sha256', 'inv_verified', 'refusal_only',
                          'terminal_cost'}, label='refusal')
        _name(refusal['router_id'], 'refusal.router_id')
        _hex64(refusal['artifact_sha256'], 'refusal.artifact_sha256')
        if refusal['inv_verified'] is not True:
            raise ValueError('refusal.inv_verified must be true')
        if refusal['refusal_only'] is not True:
            raise ValueError('refusal.refusal_only must be true')
        _number(refusal['terminal_cost'], 0, maximum, 'refusal.terminal_cost')
    candidates = study['candidates']
    if not isinstance(candidates, dict) or not candidates:
        raise ValueError('candidates must be a nonempty object')
    comparisons = (len(candidates) * len(cells)
                   * (len(requirements) + 1 + (tail is not None) + (tier == 'ds')))
    eta = delta / comparisons
    if eta == 0:
        raise ValueError('delta is too small for this comparison count')
    gamma = confidence_radius(planned, eta)
    loss_radius = maximum * min(1.0, gamma)
    tail_radius = (maximum * min(1.0, gamma / (1 - tail['nu']))
                   if tail is not None else None)
    reports, feasible = {}, []
    seen_ranks = {}
    for name, candidate in sorted(candidates.items()):
        _name(name, 'candidate id')
        _object(candidate, {'artifact_sha256', 'samples', 'fallback_rank'},
                {'structure', 'deficiency', 'inv_verified', 'cfg_sha256'}, label='candidate')
        rank = candidate['fallback_rank']
        if type(rank) is not int or rank < 1:
            raise ValueError('fallback_rank must be a positive integer')
        if rank in seen_ranks:
            raise ValueError(f'duplicate fallback_rank {rank}: {seen_ranks[rank]} and {name}')
        seen_ranks[rank] = name
        digest = _hex64(candidate['artifact_sha256'], 'artifact_sha256')
        structure = structural_check(candidate.get('structure'))
        samples = candidate['samples']
        if not isinstance(samples, dict) or samples.keys() - cells.keys():
            raise ValueError('candidate samples must be an object containing only declared cell IDs')
        reasons, cell_reports = [], {}
        if structure['status'] != 'passed_declared_sets':
            reasons.append('structural_' + structure['status'])
        verified = candidate.get('inv_verified')
        if verified is None or verified is False:
            reasons.append('router:unverified')
        elif verified is not True:
            raise ValueError('inv_verified must be true')
        cfg_digest = candidate.get('cfg_sha256')
        if cfg_digest is not None:
            _hex64(cfg_digest, 'cfg_sha256')
        attestation = candidate.get('deficiency')
        if tier == 'op':
            if attestation is not None:
                raise ValueError('deficiency attestation requires tier ds')
        elif attestation is None:
            reasons.append('deficiency:unattested')
        else:
            _object(attestation, {'upper', 'threshold'}, label='deficiency')
            upper = _number(attestation['upper'], 0, float('inf'), 'deficiency.upper')
            threshold = _number(attestation['threshold'], 0, float('inf'),
                               'deficiency.threshold')
            if upper > threshold:
                reasons.append('deficiency:upper_exceeds_threshold')
        for cell_id in sorted(cells):
            completed, errors = _observations(samples.get(cell_id, []), requirements, maximum, planned)
            row = {'completed': len(completed), 'execution_errors': errors,
                   'missing': planned - len(completed) - len(errors), 'bounds': None}
            cell_reports[cell_id] = row
            if len(completed) != planned:
                reasons.append(f'{cell_id}:incomplete')
                continue  # No confidence claim on a filtered, potentially biased subset.
            mean = math.fsum(s['loss'] for s in completed) / planned
            bounds = {'loss': _interval(mean, loss_radius, maximum), 'requirements': {}}
            for key, tolerance in sorted(requirements.items()):
                estimate = sum(s['violations'][key] for s in completed) / planned
                bound = _interval(estimate, gamma, 1)
                bounds['requirements'][key] = bound
                if bound['upper'] > tolerance:
                    reasons.append(f'{cell_id}:{key}:upper_exceeds_tolerance')
            if tail is not None:
                estimate = empirical_cvar([s['loss'] for s in completed], tail['nu'])
                # Clamp the radius too: the parameter itself lies in [0, loss_max].
                bounds['tail'] = _interval(estimate, tail_radius, maximum)
                if bounds['tail']['upper'] > tail['budget']:
                    reasons.append(f'{cell_id}:tail:upper_exceeds_budget')
            row['bounds'] = bounds
        complete = all(row['bounds'] is not None for row in cell_reports.values())
        # Worst-cell upper loss is reported for audit; the selection objective
        # is the weighted mean cost estimate (v23 Section VIII: argmin J-hat
        # over the feasible set, weighted by the deployment distribution).
        # Safety stays in the per-cell bounds, not the objective.
        objective_upper = (max(row['bounds']['loss']['upper'] for row in cell_reports.values())
                           if complete else None)
        objective_mean = (math.fsum(cell_reports[cid]['bounds']['loss']['estimate']
                                    * weights[cid] for cid in cell_reports)
                          if complete else None)
        status = 'admissible' if not reasons else (
            'structurally_rejected' if structure['status'] == 'rejected' else 'inadmissible')
        reports[name] = {'artifact_sha256': digest, 'status': status, 'structure': structure,
                         'reasons': reasons, 'cells': cell_reports,
                         'objective_upper': objective_upper,
                         'objective_mean': objective_mean,
                         'fallback_rank': rank}
        if not reasons:
            feasible.append(name)
    if feasible:
        chosen = min(feasible, key=lambda name: (reports[name]['objective_mean'],
                                                 reports[name]['fallback_rank'], name))
        status, action = 'selected', 'recommend'
    elif refusal is not None:
        chosen = refusal['router_id']
        status, action = 'refusal', 'refuse'
    else:
        chosen = None
        status, action = 'no_admissible_candidate', 'abstain'
    order = sorted(feasible, key=lambda name: (reports[name]['fallback_rank'], name))
    for position, name in enumerate(order):
        nxt = order[position + 1] if position + 1 < len(order) else 'abstain'
        reports[name]['certificate'] = {
            'study_id': study['study_id'], 'regime': regime, 'tier': tier,
            'candidate': name, 'artifact_sha256': reports[name]['artifact_sha256'],
            'admissible': True, 'fallback_next': nxt,
            'inv_verified': True,
            'cfg_sha256': candidates[name].get('cfg_sha256'),
            'evidence': {'reuse_mode': mode},
            'thresholds': {'requirements': dict(sorted(requirements.items())), 'tail': tail,
                           'deficiency': candidates[name].get('deficiency'),
                           'cell_weights': dict(weights)},
            'confidence': {'delta': delta, 'comparisons': comparisons,
                           'per_bound_delta': eta},
            'scope': 'declared regime, cells, and evaluator evidence only; '
                     'not authenticated or enforced'}
    refusal_report = None
    if refusal is not None:
        refusal_report = {
            'router_id': refusal['router_id'], 'artifact_sha256': refusal['artifact_sha256'],
            'terminal_cost': refusal['terminal_cost'],
            'note': 'verified to refuse deployment safely; not asserted to satisfy '
                    'task-risk or omission-risk budgets'}
    return {'schema_version': 2, 'study_id': study['study_id'],
            'status': status, 'selected': chosen, 'action': action,
            'tier': tier, 'regime': regime, 'deployment_order': order,
            'refusal': refusal_report,
            'confidence': {'delta': delta, 'comparisons': comparisons, 'per_bound_delta': eta,
                           'unit_radius': gamma, 'method': 'Hoeffding; DKW-Massart for optional CVaR'},
            'scope': {'requirements': dict(sorted(requirements.items())), 'cells': cells,
                      'loss_max': maximum, 'loss_unit': study['loss_unit'],
                      'samples_per_cell': planned, 'tail': tail,
                      'assumptions': study['assumptions'], 'evidence': evidence,
                      'cell_weights': dict(weights),
                      'structural_evidence': 'declared sets only; not authenticated or enforced',
                      'decision_deficiency': ('evaluator-attested, not independently certified'
                                              if tier == 'ds' else 'not certified'),
                      'regret': 'not certified',
                      'distribution_shift': 'not certified'},
            'candidates': reports}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def main(argv):
    parser = argparse.ArgumentParser(prog='skillwren select', description=__doc__)
    parser.add_argument('study', type=Path, help='schema-1 JSON study; see examples/selection')
    args = parser.parse_args(argv)
    try:
        raw = args.study.read_bytes()
        study = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_unique_object)
        report = select(study)
        report['input_sha256'] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError, OverflowError) as error:
        print(f'skillwren select: {error}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report['selected'] is not None else 1
