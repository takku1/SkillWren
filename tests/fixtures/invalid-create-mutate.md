---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.4
purpose: Do the thing.
accepts: {}
produces:
  report: { type: Text }
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
  reads: [app.log]
  creates: [app.log]
  mutates: []
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

```contract
resources:
  log:
    path: app.log
    access: read+create
always:
  keep the log
never:
  lose entries
```

```logic
main:
  read app.log as content
  save content as app.log
  return content as report
```
