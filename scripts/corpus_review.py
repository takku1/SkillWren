"""Independent review of the frozen NL fidelity corpus, per FROZEN.md.

The reviewer is a fresh headless Claude session with no tools, no
repository, and no user settings. Pass 1 sees ONLY an item's intent and the
deterministic `explain-workflow` output (never the flow file, never the
facts) and writes down the requirements, branches, permissions, and
limitations it recovers. Pass 2, a separate session, gets the pass-1 notes
plus the facts and classifies: facts recovered, facts missed, recovered
items no fact covers (candidate invented requirements or explainer noise),
and explanation statements contradicting the intent.

This is an independent model reviewer, not a human reviewer; it is outside
this authoring session, but shares a model family with the author.
Spends provider usage.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fidelity_eval  # noqa: E402
from fidelity_eval import explain, sha  # noqa: E402

RECOVER = """You are an independent reviewer of a workflow explainer. You see a
natural-language INTENT and an EXPLANATION generated deterministically from a
checked workflow that is supposed to implement it. You never see the workflow
file itself.

From the EXPLANATION alone, list what the workflow does: requirements (gates,
checks, writes, ordering constraints), branches (what happens on failure or
on each condition), permissions/authority (who decides, what is written),
and limitations (what the explanation says it cannot show). Then list any
point where the EXPLANATION disagrees with or falls short of the INTENT.

INTENT:
{intent}

EXPLANATION:
{explanation}
"""
CLASSIFY = """You are checking a reviewer's notes against an answer key.

NOTES were written by a reviewer who saw only an intent and a workflow
explanation. FACTS are short strings the corpus author says must be
recoverable from the explanation (typed IDs like 'verify#check' and quoted
messages are exact). For each fact decide whether the NOTES recovered it
(same meaning; exact wording not required). Then list items in the NOTES'
requirement/branch/permission lists that no fact covers, and copy the
NOTES' intent-mismatch points.

FACTS:
{facts}

NOTES:
{notes}
"""
RECOVER_SCHEMA = {"type": "object", "required": ["requirements", "branches", "authority",
                                                 "limitations", "intent_mismatches"],
                  "properties": {k: {"type": "array", "items": {"type": "string"}} for k in
                                 ("requirements", "branches", "authority", "limitations",
                                  "intent_mismatches")}}
CLASSIFY_SCHEMA = {"type": "object", "required": ["facts", "uncovered", "intent_mismatches"],
                   "properties": {
                       "facts": {"type": "array", "items": {
                           "type": "object", "required": ["fact", "recovered", "note"],
                           "properties": {"fact": {"type": "string"},
                                          "recovered": {"type": "boolean"},
                                          "note": {"type": "string"}}}},
                       "uncovered": {"type": "array", "items": {"type": "string"}},
                       "intent_mismatches": {"type": "array", "items": {"type": "string"}}}}


def ask(system, schema, model):
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, 'task.md').write_text(system, encoding='utf-8')
        cmd = [shutil.which('claude') or 'claude', '-p', 'Do the task in your system prompt.',
               '--model', model, '--output-format', 'json', '--tools', '',
               '--strict-mcp-config', '--no-session-persistence', '--setting-sources', '',
               '--system-prompt-file', str(Path(directory, 'task.md')),
               '--json-schema', json.dumps(schema)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                              errors='replace', timeout=600, cwd=directory)
    result = json.loads(proc.stdout)
    value = result.get('structured_output') or json.loads(result['result'])
    return value, result.get('total_cost_usd') or 0


def review(name, out, model, pins):
    files = [fidelity_eval.CORPUS / f'{name}-{kind}' for kind in ('intent.md', 'flow.md', 'facts.json')]
    for f in files:
        if sha(f) != pins[f.name]:
            raise SystemExit(f'{f.name} does not match the frozen manifest')
    intent, flow, facts_file = files
    explanation = explain(flow)
    notes, cost1 = ask(RECOVER.format(intent=intent.read_text(encoding='utf-8'),
                                      explanation=explanation), RECOVER_SCHEMA, model)
    facts = json.loads(facts_file.read_text(encoding='utf-8'))
    verdict, cost2 = ask(CLASSIFY.format(facts=json.dumps(facts, indent=1),
                                         notes=json.dumps(notes, indent=1)),
                         CLASSIFY_SCHEMA, model)
    total = sum(len(v) for v in facts.values()) if isinstance(facts, dict) else len(facts)
    record = {'name': name, 'facts': total,
              'recovered': sum(f['recovered'] for f in verdict['facts']),
              'missed': [f for f in verdict['facts'] if not f['recovered']],
              'uncovered': verdict['uncovered'],
              'intent_mismatches': notes['intent_mismatches'],
              'limitations_recovered': notes['limitations'],
              'notes': notes, 'cost_usd': round(cost1 + cost2, 4)}
    (out / f'{name}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(f"{name}: {record['recovered']}/{total} facts, "
          f"{len(record['intent_mismatches'])} mismatches", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--model', default='opus')
    parser.add_argument('--corpus', default=str(fidelity_eval.CORPUS), help='frozen corpus directory')
    parser.add_argument('--out', help='default: <corpus>/independent-review')
    parser.add_argument('--jobs', type=int, default=3)
    args = parser.parse_args()
    fidelity_eval.CORPUS = Path(args.corpus).resolve()
    args.out = args.out or str(fidelity_eval.CORPUS / 'independent-review')
    pins = fidelity_eval.manifest()
    names = sorted(n[:-len('-intent.md')] for n in pins if n.endswith('-intent.md'))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(lambda n: review(n, out, args.model, pins), names))
    totals = {'reviewer': f'fresh headless Claude session ({args.model}), no tools or repo',
              'items': len(records), 'facts': sum(r['facts'] for r in records),
              'recovered': sum(r['recovered'] for r in records),
              'intent_mismatches': sum(len(r['intent_mismatches']) for r in records),
              'uncovered_items': sum(len(r['uncovered']) for r in records),
              'cost_usd': round(sum(r['cost_usd'] for r in records), 3)}
    (out / 'summary.json').write_text(json.dumps({'totals': totals, 'items': [
        {k: r[k] for k in ('name', 'facts', 'recovered', 'missed', 'intent_mismatches')}
        for r in records]}, indent=2), encoding='utf-8')
    print(json.dumps(totals, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
