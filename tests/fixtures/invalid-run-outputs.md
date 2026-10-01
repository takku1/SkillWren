---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  input: { type: Text, required: false }
produces:
  cat: { type: Text }
  dog: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  a: []
  b: []
  c: []
flows: [a, b, c]
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
a:
  generate result from input as cat
  return cat as cat
```

```logic
b:
  run a with:
    input = input

  show dog
  return cat as cat
```

```logic
c:
  generate result from input as dog
  return dog as dog
```

## Appendix

Keep the result minimal and faithful to the input.
