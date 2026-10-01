---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  a: { type: List<DragonSpaghetti>, required: false }
  b: { type: Enum[], required: false }
  c: { type: Enum[x, x], required: false }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: []
flows: [main]
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
  generate result from a as output
  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
