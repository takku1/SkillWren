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
    _object(study, {'schema_version', 'study_id', 'assumptions', 'delta', 'loss_max', 'loss_unit',
                    'samples_per_cell', 'requirements', 'cells', 'candidates'}, {'tail'})
    if type(study['schema_version']) is not int or study['schema_version'] != 1:
        raise ValueError('schema_version must be 1')
    _name(study['study_id'], 'study_id')
    _name(study['loss_unit'], 'loss_unit')
    _object(study['assumptions'], ASSUMPTIONS, label='assumptions')
    if any(v is not True for v in study['assumptions'].values()):
        raise ValueError('version 1 requires fixed candidates, fixed sample size and IID within cells')
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
    tail = study.get('tail')
    if tail is not None:
        _object(tail, {'nu', 'budget'}, label='tail')
        _number(tail['nu'], 0, 1, 'tail.nu')
        if not 0 < tail['nu'] < 1:
            raise ValueError('tail.nu must be strictly between 0 and 1')
        _number(tail['budget'], 0, maximum, 'tail.budget')
    candidates = study['candidates']
    if not isinstance(candidates, dict) or not candidates:
        raise ValueError('candidates must be a nonempty object')
    comparisons = len(candidates) * len(cells) * (len(requirements) + 1 + (tail is not None))
    eta = delta / comparisons
    if eta == 0:
        raise ValueError('delta is too small for this comparison count')
    gamma = confidence_radius(planned, eta)
    reports, feasible = {}, []
    for name, candidate in sorted(candidates.items()):
        _name(name, 'candidate id')
        _object(candidate, {'artifact_sha256', 'samples'}, {'structure'}, label='candidate')
        digest = candidate['artifact_sha256']
        if (not isinstance(digest, str) or len(digest) != 64
                or any(c not in '0123456789abcdef' for c in digest)):
            raise ValueError('artifact_sha256 must be 64 lowercase hexadecimal characters')
        structure = structural_check(candidate.get('structure'))
        samples = candidate['samples']
        if not isinstance(samples, dict) or samples.keys() - cells.keys():
            raise ValueError('candidate samples must be an object containing only declared cell IDs')
        reasons, cell_reports = [], {}
        if structure['status'] != 'passed_declared_sets':
            reasons.append('structural_' + structure['status'])
        for cell_id in sorted(cells):
            completed, errors = _observations(samples.get(cell_id, []), requirements, maximum, planned)
            row = {'completed': len(completed), 'execution_errors': errors,
                   'missing': planned - len(completed) - len(errors), 'bounds': None}
            cell_reports[cell_id] = row
            if len(completed) != planned:
                reasons.append(f'{cell_id}:incomplete')
                continue  # No confidence claim on a filtered, potentially biased subset.
            mean = math.fsum(s['loss'] / planned for s in completed)
            bounds = {'loss': _interval(mean, maximum * min(1.0, gamma), maximum), 'requirements': {}}
            for key, tolerance in sorted(requirements.items()):
                estimate = sum(s['violations'][key] for s in completed) / planned
                bound = _interval(estimate, gamma, 1)
                bounds['requirements'][key] = bound
                if bound['upper'] > tolerance:
                    reasons.append(f'{cell_id}:{key}:upper_exceeds_tolerance')
            if tail is not None:
                estimate = empirical_cvar([s['loss'] for s in completed], tail['nu'])
                # Clamp the radius too: the parameter itself lies in [0, loss_max].
                radius = maximum * min(1.0, gamma / (1 - tail['nu']))
                bounds['tail'] = _interval(estimate, radius, maximum)
                if bounds['tail']['upper'] > tail['budget']:
                    reasons.append(f'{cell_id}:tail:upper_exceeds_budget')
            row['bounds'] = bounds
        objective = (max(row['bounds']['loss']['upper'] for row in cell_reports.values())
                     if all(row['bounds'] is not None for row in cell_reports.values()) else None)
        status = 'certified' if not reasons else (
            'structurally_rejected' if structure['status'] == 'rejected' else 'uncertified')
        reports[name] = {'artifact_sha256': digest, 'status': status, 'structure': structure,
                         'reasons': reasons, 'cells': cell_reports, 'objective_upper': objective}
        if not reasons:
            feasible.append(name)
    chosen = min(feasible, key=lambda name: (reports[name]['objective_upper'], name)) if feasible else None
    return {'schema_version': 1, 'study_id': study['study_id'],
            'status': 'selected' if chosen is not None else 'no_certified_candidate',
            'selected': chosen, 'action': 'recommend' if chosen is not None else 'abstain',
            'confidence': {'delta': delta, 'comparisons': comparisons, 'per_bound_delta': eta,
                           'unit_radius': gamma, 'method': 'Hoeffding; DKW-Massart for optional CVaR'},
            'scope': {'requirements': dict(sorted(requirements.items())), 'cells': cells,
                      'loss_max': maximum, 'loss_unit': study['loss_unit'],
                      'samples_per_cell': planned, 'tail': tail,
                      'assumptions': study['assumptions'],
                      'structural_evidence': 'declared sets only; not authenticated or enforced',
                      'decision_deficiency': 'not certified', 'regret': 'not certified',
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
