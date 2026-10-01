---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  input: { type: Text, required: false }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  Bad: []
flows: [Bad]
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
Bad:
  generate result from input as output
  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
