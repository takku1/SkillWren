"""Stub stand-in for a model adapter: transparent, deterministic, dumb.

Reads {"intent": text} on stdin and returns a generic check-then-record
skeleton plus the questions a real drafter must answer before the flow
can be concrete. It invents nothing domain-specific: every concrete
name, command, and criterion below is a placeholder the human must
replace. Labeled a stub everywhere it appears.
"""
import json
import sys

request = json.load(sys.stdin)
assert isinstance(request.get("intent"), str) and request["intent"].strip()
flow = """# Proposed workflow (STUB - placeholders must be replaced)

```contract
order:
  verify#result before write#note
```

```logic
draft:
  exec run the check from checks as result
  verify #result result meets the criterion from result
    otherwise:
      abort with "Criterion not met."
  write #note findings note with target
  return note as note
```
"""
print(json.dumps({
    "flow": flow,
    "assumptions": [
        "stub assumes a single check-then-record shape with no branches",
        "stub assumes the check is an executable that exits nonzero on failure",
    ],
    "questions": [
        "what exactly is the check command and what does it output?",
        "what counts as passing - exact criterion on the output?",
        "where must the note be written, and who is allowed to write it?",
        "what must happen when the check itself cannot run?",
    ],
}))
