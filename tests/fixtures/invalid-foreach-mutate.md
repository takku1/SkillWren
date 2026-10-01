---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  items: { type: List<Text>, required: false }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: []
  second: []
flows: [main, second]
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
  leave things tidy
never:
  lose data
```

```logic
main:
  for each items as item:
    show item
    save item as items
  generate result from items as output
  return output as output
```

```logic
second:
  for each items as item:
    show item
    generate note from item as items
  generate result from items as output
  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
