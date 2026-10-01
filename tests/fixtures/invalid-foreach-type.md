---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  input: { type: Text, required: true }
  items: { type: List<Text>, required: false }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: [input exists]
  second: []
flows: [main, second]
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
main:
  require input exists
    otherwise:
      abort with "No."

  for each input as item:
    show item
  generate result from input as output
  return output as output
```

```logic
second:
  for each items as item:
    show item
  generate result from items as output
  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
