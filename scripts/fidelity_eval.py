"""Model-draft reproduction test over the frozen NL fidelity corpus.

For each frozen `*-intent.md`: verify the manifest digest, draft a flow with
`skillwren draft` through a model adapter, `check` it (one repair round feeds
the check errors back), then compare against the approved flow three ways:

1. structural: per flow, the multiset of statement kinds (gate/action plus
   verb), order rules by verb pair, and written targets count; dropped and
   added elements are counted separately;
2. facts: the corpus facts, with typed IDs abstracted, searched in the
   draft's deterministic explanation (ID-agnostic recall);
3. judged: a separate model session sees the intent and both explanations
   (reference and candidate) and lists requirements the candidate dropped,
   added without support in the intent, or changed.

Spends provider usage. The judge shares a model family with the drafter;
treat judged counts as assisted review, not ground truth.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / 'docs/current/research/nl-fidelity'
PYTHON = str(Path(sys.executable).resolve())
SW = [PYTHON, str(ROOT / 'scripts' / 'skillwren.py')]
ADAPTER = [PYTHON, str(ROOT / 'scripts' / 'adapters' / 'claude_draft.py')]
JUDGE_SCHEMA = {"type": "object", "required": ["dropped", "added", "changed"],
                "properties": {k: {"type": "array", "items": {"type": "string"}}
                               for k in ("dropped", "added", "changed")}}
JUDGE_PROMPT = """You compare two workflow explanations against the intent they implement.
Each explanation is deterministic prose generated from a checked workflow.
REFERENCE is the human-approved implementation; CANDIDATE is a model draft.
Judge semantics only: step wording, IDs, flow-local names, and message text
do not matter unless the meaning changes.

List, as short phrases:
- dropped: requirements present in REFERENCE (and supported by the intent)
  that CANDIDATE lacks or weakens (a missing gate, branch, abort, ask,
  retry, write, or ordering constraint).
- added: requirements in CANDIDATE that the intent does not support (an
  extra gate, ask, write, abort, constraint, or permission). Do not count
  harmless restatements of something the intent says.
- changed: requirements both have but with different meaning (different
  order, a different abort condition, a write moved inside or outside a
  branch, a human decision made automatic or vice versa).
Empty lists are fine. Be strict and concrete.

INTENT:
{intent}

REFERENCE:
{reference}

CANDIDATE:
{candidate}
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest():
    text = (CORPUS / 'FROZEN.md').read_text(encoding='utf-8')
    return dict((name, digest) for digest, name in
                re.findall(r'^([0-9a-f]{64})  (\S+)$', text, re.M))


def sw(*args, cwd=None):
    proc = subprocess.run(SW + list(args), capture_output=True, text=True, cwd=cwd)
    return proc.returncode, proc.stdout, proc.stderr


def dump(flow):
    code, out, err = sw('explain-workflow', '--fragment', '--json', str(flow))
    return json.loads(out) if code == 0 and out.strip().startswith('{') else None


def explain(flow):
    code, out, err = sw('explain-workflow', '--fragment', str(flow))
    return out if code == 0 else err


def verb(statement):
    return statement.get('detail') or statement['text'].split()[0].lower()


def signature(statements):
    found = Counter()
    for s in statements:
        if s['kind'] not in ('otherwise', 'blank'):
            found[f"{s['kind']}:{verb(s)}"] += 1
        found.update(signature(s.get('children', [])))
    return found


def kind_of(ref):
    return ref.split('#')[0] if '#' in ref else ref.split()[0].lower()


def structure(d):
    flows = {name: signature(body) for name, body in d.get('flows', {}).items()}
    rules = Counter(f"{kind_of(r['first'])}->{kind_of(r['then'])}" for r in d.get('order_rules', []))
    writes = {name: len(t.get('writes', [])) for name, t in d.get('touches', {}).items()}
    return flows, rules, writes


def compare(ref, cand):
    rf, rr, rw = structure(ref)
    cf, cr, cw = structure(cand)
    # Align same-named flows, then pair the rest greedily by statement overlap
    # (flow names are incidental when the intent does not name them).
    pairs = {n: n for n in set(rf) & set(cf)}
    left = [n for n in rf if n not in pairs]
    right = [n for n in cf if n not in pairs.values()]
    while left and right:
        _, a, b = max(((sum((rf[a] & cf[b]).values()), a, b) for a in left for b in right))
        pairs[a] = b
        left.remove(a)
        right.remove(b)
    dropped, added = Counter(), Counter()
    flows = {}
    for name in list(rf) + right:
        r = rf.get(name, Counter())
        c = cf.get(pairs.get(name, name), Counter()) if name in rf else cf[name]
        flows[name] = {'candidate': pairs.get(name) if name in rf else name,
                       'dropped': dict(r - c), 'added': dict(c - r),
                       'missing_flow': name in rf and name not in pairs,
                       'extra_flow': name not in rf}
        dropped.update(r - c)
        added.update(c - r)
    return {'flows': flows, 'dropped_statements': sum(dropped.values()),
            'added_statements': sum(added.values()),
            'reference_statements': sum(sum(v.values()) for v in rf.values()),
            'dropped_rules': dict(rr - cr), 'added_rules': dict(cr - rr),
            'reference_rules': sum(rr.values()),
            'writes_delta': {n: cw.get(pairs.get(n, n), 0) - rw.get(n, 0)
                             for n in set(rw) | set(right)
                             if cw.get(pairs.get(n, n), 0) != rw.get(n, 0)}}


def abstract(text):
    text = re.sub(r"\b([a-z]+)#[a-z][a-z0-9_-]*", r"\1#", text)
    text = re.sub(r"\b([a-z]+) #[a-z][a-z0-9_-]*", r"\1 #", text)
    return re.sub(r'\s+', ' ', text).lower()


def fact_recall(facts, explanation):
    if isinstance(facts, dict):
        items = [(flow, f) for flow, fs in facts.items() for f in fs]
    else:
        items = [(None, f) for f in facts]
    text = abstract(explanation)
    hits = [f for _, f in items if abstract(f) in text]
    # Strict: only typed IDs are abstracted, so abort-message and flow-name
    # facts are wording-sensitive. The judged comparison is the semantic one.
    return {'facts': len(items), 'recovered': len(hits),
            'missed': [f for _, f in items if abstract(f) not in text]}


def judge(intent, reference, candidate, model):
    prompt = JUDGE_PROMPT.format(intent=intent, reference=reference, candidate=candidate)
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, 'prompt.md').write_text(prompt, encoding='utf-8')
        cmd = [shutil.which('claude') or 'claude', '-p',
               'Read the comparison task in your system prompt and answer.',
               '--model', model, '--output-format', 'json', '--tools', '',
               '--strict-mcp-config', '--no-session-persistence', '--setting-sources', '',
               '--system-prompt-file', str(Path(directory, 'prompt.md')),
               '--json-schema', json.dumps(JUDGE_SCHEMA)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=600, cwd=directory)
    result = json.loads(proc.stdout)
    verdict = result.get('structured_output') or json.loads(result['result'])
    verdict['cost_usd'] = result.get('total_cost_usd')
    return verdict


def evaluate(name, out, args, pins):
    intent_file = CORPUS / f'{name}-intent.md'
    reference = CORPUS / f'{name}-flow.md'
    for f in (intent_file, reference, CORPUS / f'{name}-facts.json'):
        if sha(f) != pins[f.name]:
            raise SystemExit(f'{f.name} does not match the frozen manifest')
    work = out / name
    work.mkdir(parents=True, exist_ok=True)
    adapter_file = work / 'adapter.json'
    adapter_file.write_text(json.dumps(ADAPTER), encoding='utf-8')
    env = dict(os.environ, SW_DRAFT_MODEL=args.model, SW_ADAPTER_LOG=str(work / 'usage.jsonl'))
    draft = work / 'draft.md'
    proc = subprocess.run(SW + ['draft', '--intent-file', str(intent_file), '--adapter-file',
                                str(adapter_file), '--out', str(draft)],
                          capture_output=True, text=True, env=env)
    (work / 'draft-stderr.txt').write_text(proc.stderr, encoding='utf-8')
    record = {'name': name, 'draft_exit': proc.returncode}
    if proc.returncode != 0:
        return record
    code, check_out, check_err = sw('check', '--fragment', str(draft))
    record['valid_first'] = code == 0
    record['first_errors'] = (check_out + check_err).strip().splitlines()[:20]
    if code != 0:
        repair_intent = work / 'repair-intent.md'
        repair_intent.write_text(
            intent_file.read_text(encoding='utf-8') +
            '\n\nYour previous draft was:\n\n' + draft.read_text(encoding='utf-8') +
            '\n\n`skillwren check --fragment` reported:\n\n' + (check_out + check_err) +
            '\nReturn a corrected full fragment that fixes these errors without '
            'changing what the intent requires.\n', encoding='utf-8')
        shutil.copy2(draft, work / 'draft-first.md')
        proc = subprocess.run(SW + ['draft', '--intent-file', str(repair_intent),
                                    '--adapter-file', str(adapter_file), '--out', str(draft)],
                              capture_output=True, text=True, env=env)
        code, check_out, check_err = sw('check', '--fragment', str(draft))
    record['valid_after_repair'] = code == 0
    record['final_errors'] = (check_out + check_err).strip().splitlines()[:20]
    (work / 'check.txt').write_text(check_out + check_err, encoding='utf-8')
    ref_dump, cand_dump = dump(reference), dump(draft)
    ref_text, cand_text = explain(reference), explain(draft)
    (work / 'explanation.txt').write_text(cand_text, encoding='utf-8')
    if cand_dump is None:
        record['structural'] = None
        return record
    record['structural'] = compare(ref_dump, cand_dump)
    facts = json.loads((CORPUS / f'{name}-facts.json').read_text(encoding='utf-8'))
    record['facts'] = fact_recall(facts, cand_text)
    if not args.no_judge:
        record['judged'] = judge(intent_file.read_text(encoding='utf-8'), ref_text,
                                 cand_text, args.judge_model)
        (work / 'judged.json').write_text(json.dumps(record['judged'], indent=2), encoding='utf-8')
    usage = [json.loads(l) for l in (work / 'usage.jsonl').read_text().splitlines() if l.strip()]
    record['draft_cost_usd'] = round(sum(u.get('cost_usd') or 0 for u in usage), 4)
    record['draft_calls'] = len(usage)
    (work / 'record.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(f"{name}: valid_first={record['valid_first']} valid={record['valid_after_repair']} "
          f"dropped={record['structural']['dropped_statements']} "
          f"added={record['structural']['added_statements']} "
          f"facts={record['facts']['recovered']}/{record['facts']['facts']}", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', default='sonnet')
    parser.add_argument('--judge-model', default='opus')
    parser.add_argument('--out', default=str(CORPUS / 'model-draft'))
    parser.add_argument('--jobs', type=int, default=3)
    parser.add_argument('--no-judge', action='store_true')
    parser.add_argument('--only', help='comma list of corpus names, e.g. 01,pairs06')
    args = parser.parse_args()
    pins = manifest()
    names = sorted(n[:-len('-intent.md')] for n in pins if n.endswith('-intent.md'))
    if args.only:
        names = [n for n in names if n in args.only.split(',')]
    out = Path(args.out) / args.model
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(lambda n: evaluate(n, out, args, pins), names))
    totals = {
        'model': args.model, 'judge_model': None if args.no_judge else args.judge_model,
        'items': len(records),
        'flows_reference': sum(len(r['structural']['flows']) for r in records if r.get('structural')),
        'valid_first': sum(bool(r.get('valid_first')) for r in records),
        'valid_after_repair': sum(bool(r.get('valid_after_repair')) for r in records),
    }
    scored = [r for r in records if r.get('structural')]
    for key in ('dropped_statements', 'added_statements', 'reference_statements', 'reference_rules'):
        totals[key] = sum(r['structural'][key] for r in scored)
    totals['dropped_rules'] = sum(sum(r['structural']['dropped_rules'].values()) for r in scored)
    totals['added_rules'] = sum(sum(r['structural']['added_rules'].values()) for r in scored)
    totals['facts'] = sum(r['facts']['facts'] for r in scored)
    totals['facts_recovered'] = sum(r['facts']['recovered'] for r in scored)
    if not args.no_judge:
        for key in ('dropped', 'added', 'changed'):
            totals['judged_' + key] = sum(len(r.get('judged', {}).get(key, [])) for r in scored)
    totals['draft_cost_usd'] = round(sum(r.get('draft_cost_usd') or 0 for r in records), 3)
    totals['judge_cost_usd'] = round(sum((r.get('judged') or {}).get('cost_usd') or 0
                                         for r in records), 3)
    report = {'totals': totals, 'records': records,
              'caveat': ('Structural and fact counts are deterministic; judged counts come '
                         'from a model reviewer and are assisted review, not ground truth.')}
    (out / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(totals, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
