---
skill: v05-header
name: v05-header
description: Fixture for format 0.5 rules.
version: 0.5
release: 0.3.0
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants a release field fixture
requires:
  main: [input exists]
flows: [main]
authority:
  user-decides: []
  system-decides: [whether the input is valid]
  system-may: []
  system-must-not: [infer user approval]
effects:
  reads: [input, notes]
  creates: [output]
  mutates: [notes]
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
  notes:
    path: notes.md
    access: read+write
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

  read notes.md as notes
  show notes
  generate copy from input as output
  write output with notes.md

  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
