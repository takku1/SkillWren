---
skill: verify-unbound
name: verify-unbound
description: Fixture for format 0.5 rules.
version: 0.5
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants an unbound evidence fixture
requires:
  main: [input exists]
flows: [main]
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
  return an unchecked result
```

```logic
main:
  require input exists
    otherwise:
      abort with "An input is required."

  generate copy from input as output
  verify output passes the acceptance checks from results
    otherwise:
      abort with "Checks failed; nothing returned."

  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
