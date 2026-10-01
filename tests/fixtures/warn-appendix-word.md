---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: [input exists]
flows: [main]
authority:
  user-decides: [whether to approve the output]
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
      abort with "An input is required."

  generate result from input as output

  show output
  ask user to approve output
  require confirmation
    otherwise:
      abort with "Dismissed; nothing changed."

  return output as output
```

This is absolutely not an appendix.
