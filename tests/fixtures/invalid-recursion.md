---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.3
purpose: Do the thing.
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  a: []
  b: []
flows: [a, b]
authority:
  user-decides: []
  system-decides: [whether the input is valid]
  system-may: []
  system-must-not: [infer user approval]
effects:
  reads: [input]
  creates: [output]
  mutates: []
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
always:
  leave the source unchanged
never:
  return an unapproved result
```

```logic
a:
  run b with:
    input = input

  return output as output
```

```logic
b:
  run a with:
    input = input

  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
