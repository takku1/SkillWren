"""Validate FS-01 brief pools, report coverage, check duplicates.

Usage:
  py scripts/fs01_pool_check.py                  validate everything
  py scripts/fs01_pool_check.py --write-manifest  refresh SPLIT.json hashes
  py scripts/fs01_pool_check.py --write-coverage  refresh COVERAGE.md

Stdlib only. Reads briefs/ and checks/; never contacts models.
Exit 0 clean, 1 problems found, 2 usage error.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOLS = ROOT / 'docs/current/research/semantic-sufficiency/select-fs01/pools'

DIMENSIONS = {'security', 'privacy', 'authorization', 'error-handling',
              'dependency-ordering', 'workflow-fidelity'}
DIFFICULTIES = {'routine', 'complex', 'adversarial'}
KINDS = {'contains', 'not_contains', 'file_exists', 'exit_zero', 'json_field',
         'judge_rubric'}


def load(name):
    return json.loads((POOLS / name).read_bytes().decode('utf-8-sig'))


def validate(briefs, checks):
    errors = []
    seen = {}
    for brief in briefs:
        for key in ('id', 'group', 'difficulty', 'dimensions', 'title', 'brief'):
            if key not in brief:
                errors.append(f"{brief.get('id', '?')}: missing {key}")
        if brief['id'] in seen:
            errors.append(f"duplicate brief id: {brief['id']}")
        seen[brief['id']] = brief
        if brief.get('group') not in ('design', 'implement'):
            errors.append(f"{brief['id']}: bad group")
        if brief.get('difficulty') not in DIFFICULTIES:
            errors.append(f"{brief['id']}: bad difficulty")
        for dim in brief.get('dimensions', []):
            if dim not in DIMENSIONS:
                errors.append(f"{brief['id']}: bad dimension {dim}")
        for att in brief.get('attachments', []):
            if set(att) != {'name', 'content'}:
                errors.append(f"{brief['id']}: bad attachment shape")
    by_brief = {}
    for entry in checks:
        by_brief.setdefault(entry.get('brief_id'), []).append(entry)
    for bid, brief in seen.items():
        if bid not in by_brief:
            errors.append(f'{bid}: no hidden checks')
    for entry in checks:
        for check in entry.get('checks', []):
            if check.get('kind') not in KINDS:
                errors.append(f"{entry.get('brief_id')}: bad kind {check.get('kind')}")
            if check.get('dimension') not in DIMENSIONS:
                errors.append(f"{entry.get('brief_id')}: bad check dimension")
            if check.get('kind') == 'judge_rubric' and not check.get('rubric'):
                errors.append(f"{entry.get('brief_id')}: judge check needs rubric")
    return errors, seen


def tokens(text):
    return set(re.findall(r'[a-z0-9]{3,}', text.lower()))


def signature(brief):
    parts = [brief['title'], brief['brief']]
    parts += [a['content'] for a in brief.get('attachments', [])]
    return tokens('\n'.join(parts))


def dedup(briefs, threshold=0.45):
    flags = []
    sigs = [(b['id'], signature(b)) for b in briefs]
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            aid, a = sigs[i]
            bid, b = sigs[j]
            union = a | b
            score = len(a & b) / len(union) if union else 1.0
            if score >= threshold:
                flags.append((round(score, 2), aid, bid))
    return sorted(flags, reverse=True)


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-manifest', action='store_true')
    parser.add_argument('--write-coverage', action='store_true')
    args = parser.parse_args(argv)
    briefs = load('briefs/design.json') + load('briefs/implement.json')
    checks = load('checks/design.json') + load('checks/implement.json')
    errors, _seen = validate(briefs, checks)
    split_path = POOLS / 'SPLIT.json'
    if split_path.exists():
        split = json.loads(split_path.read_bytes().decode('utf-8-sig'))
        holdout, devset = set(split.get('holdout', [])), set(split.get('dev', []))
        all_ids = set(_seen)
        if holdout & devset:
            errors.append(f'split overlap: {sorted(holdout & devset)}')
        if holdout | devset != all_ids:
            errors.append('split does not partition the brief set: '
                          f'missing={sorted(all_ids - holdout - devset)}, '
                          f'unknown={sorted((holdout | devset) - all_ids)}')
        for rel, digest in split.get('files', {}).items():
            path = POOLS / rel
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                errors.append(f'split manifest mismatch or missing: {rel}')
    flags = dedup(briefs)
    if args.write_manifest:
        files = {}
        for path in sorted(POOLS.rglob('*')):
            if path.is_file() and path.name not in ('SPLIT.json', 'COVERAGE.md'):
                files[str(path.relative_to(POOLS))] = hashlib.sha256(
                    path.read_bytes()).hexdigest()
        split_path = POOLS / 'SPLIT.json'
        if split_path.exists():
            split = json.loads(split_path.read_bytes().decode('utf-8-sig'))
        else:
            split = {'dev': [], 'holdout': [], 'note': ''}
        split['files'] = files
        split_path.write_text(json.dumps(split, indent=2) + '\n', encoding='utf-8')
    if args.write_coverage:
        lines = ['# FS-01 coverage matrix', '',
                 'Generated by `scripts/fs01_pool_check.py --write-coverage`.',
                 'Difficulty mix is recorded, not quota-forced.', '',
                 '| brief | group | difficulty | dimensions | split |',
                 '|---|---|---|---|---|']
        split_path = POOLS / 'SPLIT.json'
        split = (json.loads(split_path.read_bytes().decode('utf-8-sig'))
                 if split_path.exists() else {})
        holdout, devset = set(split.get('holdout', [])), set(split.get('dev', []))
        for b in sorted(briefs, key=lambda b: b['id']):
            tag = ('holdout' if b['id'] in holdout
                   else ('dev' if b['id'] in devset else 'UNASSIGNED'))
            dims = ','.join(sorted(b['dimensions']))
            lines.append(f"| {b['id']} | {b['group']} | {b['difficulty']} "
                         f"| {dims} | {tag} |")
        (POOLS / 'COVERAGE.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'briefs: {len(briefs)}, checks: {len(checks)}')
    print(f'duplicate pairs above threshold: {len(flags)}')
    for score, aid, bid in flags[:20]:
        print(f'  {score} {aid} {bid}')
    if errors:
        print('ERRORS:')
        for error in errors:
            print(f'  {error}')
        return 1
    if flags:
        print('note: flagged pairs need human adjudication in DEDUP.md')
    print('OK')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
