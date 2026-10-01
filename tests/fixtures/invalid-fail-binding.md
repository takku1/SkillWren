---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts: {}
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
  reads: [source]
  creates: []
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
always:
  leave the source unchanged
never:
  lose the source
```

```logic
main:
  read data from source as blob
    otherwise:
      show blob
      abort with "No data."

  return blob as output
```
