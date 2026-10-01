---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  count: { type: Number, required: false }
  label: { type: Text, required: false }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: []
  helper: []
flows: [main, helper]
authority:
  user-decides: []
  system-decides: []
  system-may: []
  system-must-not: []
effects:
  reads: []
  creates: []
  mutates: []
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

```contract
resources:
always:
never:
```

```logic
main:
  run helper with:
    label = count

  return output as output
```

```logic
helper:
  generate result from label as output
  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
