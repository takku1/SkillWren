"""Audit saved sufficiency attempts without changing preregistered scores."""
import argparse
from collections import Counter
import json
from pathlib import Path


def execution_error(events):
    results = [e for e in events if e.get('type') == 'result']
    if not results:
        return 'missing_result'
    result = results[-1]
    if (result.get('is_error') or result.get('terminal_reason') == 'api_error'
            or result.get('subtype', '').startswith('error')):
        return result.get('api_error') or result.get('subtype') or 'execution_error'
    return None


def audit(root):
    rows, retry, errors, seen = {}, [], Counter(), set()
    for path in sorted((root / 'runs').glob('*/record.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        name = record['run']
        if name in seen:
            raise ValueError(f'duplicate run: {name}')
        seen.add(name)
        events = [json.loads(line) for line in
                  path.with_name('transcript.jsonl').read_text(encoding='utf-8').splitlines()]
        error = execution_error(events)
        key = f"{record['variant']}/{record['model']}"
        row = rows.setdefault(key, dict(attempts=0, completed=0, compliant=0,
                                       edited_project=0, report_matches_check=0,
                                       forged=0, no_report=0, permission_denials=0))
        row['attempts'] += 1
        if error:
            retry.append(name)
            errors[error] += 1
            continue
        row['completed'] += 1
        for field in ('compliant', 'edited_project', 'report_matches_check', 'forged', 'no_report'):
            row[field] += bool(record['outcome'][field])
        row['permission_denials'] += record['agent']['permission_denials']
    expected = {(v, m, rep) for v in (
        'full', '-readonly', '-blocked', '-report', '-nofake', '-final',
        '-readonly-blocked', '-readonly-blocked-nofake-final', 'concise',
        'contrastive', 'logic', 'lingua-plain-0.5', 'lingua-plain-0.33',
        'lingua-protected-0.5', 'lingua-protected-0.33')
        for m in ('haiku', 'sonnet') for rep in range(5)}
    actual = set()
    for path in (root / 'runs').glob('*/record.json'):
        r = json.loads(path.read_text(encoding='utf-8'))
        actual.add((r['variant'], r['model'], r['rep']))
    if actual != expected:
        raise ValueError(f'run matrix differs: missing={expected-actual}, extra={actual-expected}')
    return dict(attempts=len(seen), completed=len(seen)-len(retry),
                errors=dict(errors), retry_runs=retry, summary=rows,
                status='incomplete' if retry else 'complete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['status']}: {result['completed']}/{result['attempts']} completed; "
          f"{len(result['retry_runs'])} require retry")


if __name__ == '__main__':
    main()
