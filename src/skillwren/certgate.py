"""Host-side DPCC deployment gate: bind certificates to artifact bytes.

Offline checkable part of the deployment contract. Given a `skillwren
select` report, this verifies the certificate bundle against real bytes
and the live deployment context before a trusted host authorizes
consequential execution:

  CertificateValid = artifact bytes match + regime match + config match
      + fallback links resolve + invariant attestation present

`MonitorPass` and `PolicyAllows` are runtime inputs asserted by the
caller through flags; per-action `StructOK` stays with the runtime
monitor. Anything the gate cannot verify is a denial, never a pass.
The two success-shaped outcomes are different contracts:

  Allow  ==> full deployment validation (bundle, context, monitor, policy).
  Refuse ==> verified refusal only; safe terminal outcome, never an
             authorization to execute. It stays available exactly when
             monitor or policy fail, so it shares none of allow's checks
             beyond refusal identity, flags, and artifact bytes.

Callers must not treat exit 0 alone as permission: only `allow` (exit 0
with verdict `allow`) authorizes; `refuse` exits 3.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def _digest(data, label):
    digest = hashlib.sha256(data).hexdigest()
    if len(digest) != 64:
        raise ValueError(f'{label}: sha256 digest malformed')
    return digest


def _report(report):
    if not isinstance(report, dict):
        raise ValueError('report must be a JSON object')
    missing = {'schema_version', 'study_id', 'status', 'selected', 'action',
               'tier', 'regime', 'deployment_order', 'candidates'} - report.keys()
    if missing:
        raise ValueError(f'report: missing keys {sorted(missing)}')
    if report['schema_version'] != 2:
        raise ValueError('report schema_version must be 2')
    return report


def _check_chain(candidates, selected, artifacts, regime, cfg_sha256, reasons):
    """Walk fallback links; every link must resolve to bound evidence.

    Each member carries the same regime, config, and tier binding as the
    selected router: a stale fallback certificate denies the chain even
    when its artifact bytes still match.
    """
    seen, name, chain = set(), selected, []
    while name != 'abstain':
        if name in seen:
            reasons.append('fallback:cycle')
            return []
        seen.add(name)
        candidate = candidates.get(name)
        if candidate is None:
            reasons.append(f'fallback:unknown:{name}')
            return []
        certificate = candidate.get('certificate')
        if candidate.get('status') != 'admissible' or not isinstance(certificate, dict):
            reasons.append(f'fallback:inadmissible:{name}')
            return []
        if not certificate.get('inv_verified'):
            reasons.append(f'fallback:unverified:{name}')
            return []
        if certificate.get('regime') != regime:
            reasons.append(f'fallback:regime:{name}')
            return []
        if certificate.get('cfg_sha256') != cfg_sha256:
            reasons.append(f'fallback:cfg:{name}')
            return []
        blob = artifacts.get(name)
        if blob is None:
            reasons.append(f'artifact:missing:{name}')
            return []
        if _digest(blob, name) != candidate['artifact_sha256']:
            reasons.append(f'artifact:mismatch:{name}')
            return []
        chain.append(name)
        name = certificate.get('fallback_next', 'abstain')
    return chain


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def verify(report, artifacts, regime, cfg_sha256, monitor_pass, policy_allows,
           study=None, study_sha256=None):
    """Return a gate verdict; deny on anything unverifiable.

    artifacts maps candidate/router id to exact artifact bytes. regime
    is the live deployment regime object. cfg_sha256 binds the live
    configuration. monitor_pass and policy_allows are caller-asserted
    runtime inputs. study is the original certification study: the gate
    re-runs selection and denies reports that do not match the fresh
    outcome, so coordinated report rewrites fail unless the attacker
    also controls the host's evidence store holding the study.
    study_sha256 optionally binds the raw study bytes against the
    report's input hash.
    """
    report = _report(report)
    reasons, checked = [], {}
    status, selected = report['status'], report['selected']
    if not isinstance(study, dict):
        reasons.append('study:missing')
        return {'gate_schema_version': 1, 'verdict': 'deny', 'selected': selected,
                'action': 'deny', 'reasons': reasons, 'checked': checked}
    try:
        from .selection import select as _select
        fresh = _select(study)
    except (ValueError, OverflowError):
        reasons.append('study:invalid')
        return {'gate_schema_version': 1, 'verdict': 'deny', 'selected': selected,
                'action': 'deny', 'reasons': reasons, 'checked': checked}
    presented = dict(report)
    presented.pop('input_sha256', None)
    if _canonical(fresh) != _canonical(presented):
        reasons.append('report:inauthentic')
    if 'input_sha256' in report:
        if study_sha256 is None or report['input_sha256'] != study_sha256:
            reasons.append('study:unbound')
    if not isinstance(regime, dict) or not regime:
        raise ValueError('regime must be a nonempty object')
    if (not isinstance(cfg_sha256, str) or len(cfg_sha256) != 64
            or any(c not in '0123456789abcdef' for c in cfg_sha256)):
        raise ValueError('cfg_sha256 must be 64 lowercase hexadecimal characters')
    if not isinstance(report.get('candidates'), dict):
        raise ValueError('report candidates must be an object')

    if status == 'refusal' and selected is not None and report.get('action') == 'refuse':
        refusal = report.get('refusal') or {}
        if not refusal.get('router_id') == selected:
            reasons.append('refusal:identity')
        if refusal.get('inv_verified') is not True or refusal.get('refusal_only') is not True:
            reasons.append('refusal:unverified')
        blob = artifacts.get(selected)
        if blob is None:
            reasons.append(f'artifact:missing:{selected}')
        elif _digest(blob, selected) != refusal.get('artifact_sha256'):
            reasons.append(f'artifact:mismatch:{selected}')
        checked = {'route': 'refusal',
                   'inputs': {'regime': regime, 'cfg_sha256': cfg_sha256,
                              'artifacts': sorted(artifacts),
                              'monitor_pass': monitor_pass, 'policy_allows': policy_allows}}
        verdict = 'refuse' if not reasons else 'deny'
        return {'gate_schema_version': 1, 'verdict': verdict, 'selected': selected,
                'action': 'refuse' if verdict == 'refuse' else 'deny',
                'reasons': reasons, 'checked': checked}

    candidates = report['candidates']
    if not (status == 'selected' and selected is not None
            and report.get('action') == 'recommend'):
        reasons.append('report:no-deployable-selection')
        return {'gate_schema_version': 1, 'verdict': 'deny', 'selected': selected,
                'action': 'deny', 'reasons': reasons, 'checked': checked}

    candidate = candidates.get(selected)
    if candidate is None or candidate.get('status') != 'admissible':
        reasons.append('selected:not-admissible')
        return {'gate_schema_version': 1, 'verdict': 'deny', 'selected': selected,
                'action': 'deny', 'reasons': reasons, 'checked': checked}

    # Recompute the optimum from the reported bounds; a report whose
    # winner contradicts its own evidence is tampered or stale.
    def _evidence(name):
        rep = candidates[name]
        mean, rank = rep.get('objective_mean'), rep.get('fallback_rank')
        if (not isinstance(mean, (int, float)) or isinstance(mean, bool)
                or not isinstance(rank, int) or isinstance(rank, bool)):
            return None
        return (mean, rank, name)
    eligible = [name for name in candidates
                if candidates[name].get('status') == 'admissible'
                and _evidence(name) is not None]
    expected = min(eligible, key=_evidence, default=None)
    if expected != selected or selected not in eligible:
        reasons.append('selected:inconsistent')
    checked['recomputed'] = expected

    certificate = candidate.get('certificate') or {}
    if certificate.get('regime') != regime:
        reasons.append('regime:mismatch')
    if certificate.get('cfg_sha256') != cfg_sha256:
        reasons.append('cfg:unbound-or-mismatch')
    if certificate.get('tier') != report.get('tier'):
        reasons.append('tier:mismatch')
    checked['chain'] = _check_chain(candidates, selected, artifacts, regime,
                                      cfg_sha256, reasons)
    checked['inputs'] = {'regime': regime, 'cfg_sha256': cfg_sha256,
                         'artifacts': sorted(artifacts),
                         'monitor_pass': monitor_pass, 'policy_allows': policy_allows}
    if not monitor_pass:
        reasons.append('monitor:not-passing')
    if not policy_allows:
        reasons.append('policy:not-allowing')
    verdict = 'allow' if not reasons else 'deny'
    return {'gate_schema_version': 1, 'verdict': verdict, 'selected': selected,
            'action': 'recommend' if verdict == 'allow' else 'deny',
            'reasons': reasons, 'checked': checked}


def _load_json_argument(text, label):
    if text.startswith('@'):
        return json.loads(Path(text[1:]).read_text(encoding='utf-8-sig'))
    return json.loads(text)


def main(argv):
    parser = argparse.ArgumentParser(prog='skillwren certgate', description=__doc__)
    parser.add_argument('report', type=Path, help='skillwren select report JSON')
    parser.add_argument('--study', type=Path, required=True,
                        help='original certification study JSON (host evidence store)')
    parser.add_argument('--artifacts', type=Path, required=True,
                        help='directory with one file per candidate/router id')
    parser.add_argument('--regime', required=True,
                        help='live regime object as JSON, or @file')
    parser.add_argument('--cfg', required=True, help='live config sha256')
    parser.add_argument('--monitor-pass', action='store_true',
                        help='assert the runtime monitor passes')
    parser.add_argument('--policy-allows', action='store_true',
                        help='assert the host policy allows the action')
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_bytes().decode('utf-8-sig'))
        raw_study = args.study.read_bytes()
        study = json.loads(raw_study.decode('utf-8-sig'))
        artifacts = {path.name: path.read_bytes()
                     for path in sorted(args.artifacts.iterdir()) if path.is_file()}
        regime = _load_json_argument(args.regime, 'regime')
        verdict = verify(report, artifacts, regime, args.cfg,
                         args.monitor_pass, args.policy_allows, study=study,
                         study_sha256=hashlib.sha256(raw_study).hexdigest())
    except (OSError, ValueError) as error:
        print(f'skillwren certgate: {error}', file=sys.stderr)
        return 2
    print(json.dumps(verdict, indent=2, allow_nan=False))
    if verdict['verdict'] == 'deny':
        return 1
    if verdict['verdict'] == 'refuse':
        return 3
    return 0
