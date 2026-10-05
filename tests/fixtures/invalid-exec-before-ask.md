---
skill: exec-before-ask
name: exec-before-ask
description: Fixture for format 0.5 rules.
version: 0.5
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants an exec before ask fixture
requires:
  main: [input exists]
flows: [main]
authority:
  user-decides: []
  system-decides: [whether the input is valid]
  system-may: []
  system-must-not: [infer user approval]
effects:
  reads: [input]
  creates: [output]
  mutates: []
  executes: [checks]
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

```contract
resources:
  source:
    path: input
    access: read
  output:
    path: output
    access: create
  checks:
    path: scripts/check.py
    access: read
always:
  leave the source unchanged
never:
  return an unchecked result
```

```logic
main:
  require input exists
    otherwise:
      abort with "An input is required."

  exec acceptance checks from checks as results
  generate copy from input as output
  ask user to approve the copy
  require confirmation
    otherwise:
      abort with "Declined; nothing changed."

  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
