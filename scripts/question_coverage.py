"""Do a drafter's own questions point at the requirements it got wrong?

Prerequisite test for any value-of-information policy over draft questions
(rank questions by expected loss reduction, ask only when value exceeds the
cost of the human's attention): such a policy can only help if the question
pool covers the actual defects. For each item of a `fidelity_eval.py` run,
a model judge maps every judged dropped/added/changed requirement to the
drafter's questions and assumptions that would have surfaced it.
Spends provider usage.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = {"type": "object", "required": ["defects"], "properties": {"defects": {
    "type": "array", "items": {"type": "object",
                               "required": ["defect", "covered_by_question",
                                            "disclosed_as_assumption", "mechanism_only"],
                               "properties": {"defect": {"type": "string"},
                                              "covered_by_question": {"type": "boolean"},
                                              "disclosed_as_assumption": {"type": "boolean"},
                                              "mechanism_only": {"type": "boolean"}}}}}}
PROMPT = """A model drafted a workflow from an intent and listed QUESTIONS for the human
and ASSUMPTIONS it made. A reviewer then found DEFECTS in the draft. For each
defect decide:
- covered_by_question: would a straightforward human answer to one of the
  QUESTIONS have exposed or fixed this defect? Topic overlap is not enough.
- disclosed_as_assumption: does an ASSUMPTION state this choice openly?
- mechanism_only: is the defect only a lost stable ID / enforceability
  (the step still happens), rather than a changed or missing requirement?

DEFECTS:
{defects}

QUESTIONS:
{questions}

ASSUMPTIONS:
{assumptions}
"""


def section(text, start, end):
    lines, inside = [], False
    for line in text.splitlines():
        if line.startswith(start):
            inside = True
            continue
        if line.startswith(end):
            inside = False
        if inside and line.startswith('  - '):
            lines.append(line[4:])
    return lines


def classify(item_dir, model):
    record = json.loads((item_dir / 'record.json').read_text(encoding='utf-8'))
    judged = record.get('judged') or {}
    defects = [f"{k}: {d}" for k in ('dropped', 'added', 'changed') for d in judged.get(k, [])]
    if not defects:
        return {'name': record['name'], 'defects': []}
    stderr = (item_dir / 'draft-stderr.txt').read_text(encoding='utf-8')
    questions = section(stderr, 'unresolved questions:', 'Not approved')
    assumptions = section(stderr, 'assumptions:', 'unresolved questions:')
    prompt = PROMPT.format(defects='\n'.join(f'- {d}' for d in defects),
                           questions='\n'.join(f'- {q}' for q in questions) or '(none)',
                           assumptions='\n'.join(f'- {a}' for a in assumptions) or '(none)')
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, 'task.md').write_text(prompt, encoding='utf-8')
        proc = subprocess.run(
            [shutil.which('claude') or 'claude', '-p', 'Do the task in your system prompt.',
             '--model', model, '--output-format', 'json', '--tools', '',
             '--strict-mcp-config', '--no-session-persistence', '--setting-sources', '',
             '--system-prompt-file', str(Path(directory, 'task.md')),
             '--json-schema', json.dumps(SCHEMA)],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=600, cwd=directory)
    result = json.loads(proc.stdout)
    value = result.get('structured_output') or json.loads(result['result'])
    return {'name': record['name'], 'questions': len(questions), 'defects': value['defects'],
            'cost_usd': result.get('total_cost_usd')}


def main():
    parser = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    parser.add_argument('run', help='fidelity_eval output directory for one model')
    parser.add_argument('--model', default='sonnet')
    args = parser.parse_args()
    run = Path(args.run)
    items = [classify(d, args.model) for d in sorted(run.iterdir())
             if (d / 'record.json').is_file()]
    defects = [d for item in items for d in item['defects']]
    real = [d for d in defects if not d['mechanism_only']]
    totals = {'defects': len(defects), 'requirement_defects': len(real),
              'requirement_defects_covered_by_question': sum(d['covered_by_question'] for d in real),
              'requirement_defects_disclosed_as_assumption':
                  sum(d['disclosed_as_assumption'] for d in real),
              'requirement_defects_silent': sum(not d['covered_by_question']
                                                and not d['disclosed_as_assumption']
                                                for d in real),
              'questions_asked': sum(item.get('questions', 0) for item in items)}
    (run / 'question-coverage.json').write_text(
        json.dumps({'totals': totals, 'items': items}, indent=2), encoding='utf-8')
    print(json.dumps(totals, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
