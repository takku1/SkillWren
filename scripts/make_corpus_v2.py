"""Derive NL fidelity corpus v2 from the frozen v1 bytes (one-time, reproducible).

Applies the fixes recorded in `nl-fidelity/independent-review/README.md`:
four semantic defects (pairs16 f17, pairs21 f22, 05, and the unrequested
existence gates) and the matching facts. v1 stays frozen; v2 is written to
`nl-fidelity-v2/` and frozen separately by `--freeze`.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / 'docs/current/research/nl-fidelity'
V2 = ROOT / 'docs/current/research/nl-fidelity-v2'
NAMES = ['01', '02', '03', '04', '05', 'pairs06', 'pairs11', 'pairs16', 'pairs21']


def drop_gate(text, flow, name):
    """Remove `require <name> exist(s)` and its otherwise/abort from one flow."""
    pattern = (rf"({re.escape(flow)}:\n)  require {name} exists?\n    otherwise:\n"
               rf"      abort with \"[^\"]*\"\n")
    new, count = re.subn(pattern, r"\1", text)
    assert count == 1, (flow, name)
    return new


def replace(text, old, new):
    assert text.count(old) == 1, old[:60]
    return text.replace(old, new)


F17_OLD = '''f17:
  when window is open:
    verify #window window is open
      otherwise:
        abort with "Window shut."
    write #slot booked slot with target
  return request as request'''
F17_NEW = '''f17:
  verify #window window is open
    otherwise:
      abort with "Window shut."
  write #slot booked slot with target
  return request as request'''
F22_OLD = '''f22:
  exec service check from checks as state
  verify #service service is healthy from state
    otherwise:
      apply service restart with state as state
      apply service reload with state as state
      abort with "Still unhealthy."
  return state as state'''
F22_NEW = '''f22:
  exec service check from checks as state
  verify #service service is healthy from state
    otherwise:
      apply service restart with state as state
      exec service check from checks as state
      verify #restarted service is healthy from state
        otherwise:
          apply service reload with state as state
          exec service check from checks as state
          verify #reloaded service is healthy from state
            otherwise:
              abort with "Still unhealthy."
          return state as state
      return state as state
  return state as state'''
S05_OLD = '''The request must exist; the flow returns it unchanged and touches
nothing.

```logic
summarize:
  require request exists
    otherwise:
      abort with "Nothing to summarize."
  return request as request
```'''
S05_NEW = '''The request must exist; the flow summarizes it for the log and touches
nothing.

```logic
summarize:
  require request exists
    otherwise:
      abort with "Nothing to summarize."
  generate summary from request as summary
  return summary as summary
```'''


def build():
    V2.mkdir(exist_ok=True)
    for stale in V2.glob('*-*.*'):
        stale.unlink()
    for name in NAMES:
        for kind in ('intent.md', 'flow.md', 'facts.json'):
            shutil.copy2(V1 / f'{name}-{kind}', V2 / f'{name}-{kind}')
    edits = {
        # The gate also declared `design` as an input; declare it instead.
        '03': lambda t: replace(drop_gate(t, 'develop', 'design'),
                                '```contract\norder:', '```contract\ninputs:\n  design\norder:'),
        '05': lambda t: replace(t, S05_OLD, S05_NEW),
        'pairs06': lambda t: drop_gate(t, 'f08', 'request'),
        'pairs11': lambda t: drop_gate(t, 'f14', 'items'),
        'pairs16': lambda t: replace(
            drop_gate(drop_gate(drop_gate(t, 'f16', 'request'), 'f17', 'request'),
                      'f18', 'draft').replace(
                'order:\n  verify#parts before write#assembly',
                'order:\n  verify#parts before write#assembly\n  verify#window before write#slot'),
            F17_OLD, F17_NEW),
        'pairs21': lambda t: replace(
            drop_gate(drop_gate(t, 'f21ingest', 'request'), 'f24', 'note'), F22_OLD, F22_NEW),
    }
    for name, edit in edits.items():
        path = V2 / f'{name}-flow.md'
        path.write_bytes(edit(path.read_bytes().decode('utf-8')).encode('utf-8'))
    facts = {
        '05': ["no order rules", "nothing requires a human decision", "changes nothing",
               "generate summary from request", "return summary as summary"],
    }
    pairs16 = json.loads((V2 / 'pairs16-facts.json').read_text(encoding='utf-8'))
    pairs16['f17'] = ["'verify#window' before 'write#slot'", "Window shut", "booked slot"]
    facts['pairs16'] = pairs16
    pairs21 = json.loads((V2 / 'pairs21-facts.json').read_text(encoding='utf-8'))
    pairs21['f22'] = ["apply service restart", "service reload", "verify #restarted",
                      "verify #reloaded", "Still unhealthy"]
    pairs21['f24'] = ["write #memo recorded note", "eligible for guard enforcement"]
    facts['pairs21'] = pairs21
    for name, value in facts.items():
        (V2 / f'{name}-facts.json').write_bytes(json.dumps(value).encode('utf-8'))


def freeze():
    lines = []
    for path in sorted(V2.glob('*-*.*')):
        if path.name.split('-')[-1] in ('intent.md', 'flow.md', 'facts.json'):
            lines.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    parser.add_argument('--freeze', action='store_true', help='print the v2 manifest')
    args = parser.parse_args()
    if args.freeze:
        print(freeze(), end='')
    else:
        build()
        print(f'wrote {V2}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
