---
skill: yaml-quoted
name: yaml-quoted
description: Probe that inline map values stay valid YAML.
version: 0.4.1
purpose: Probe that inline map values stay valid YAML.
accepts:
  input: { type: Text, required: true }
  mode: { type: "Enum[fast, full]", required: false }
produces:
  output: { type: Text }
owns-when:
  - user wants to probe quoted yaml values
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
  creates: []
  mutates: []
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

# YAML probe

```contract
resources:
  source:
    path: input
    access: read
always:
  leave the source unchanged
never:
  change the input
```

```logic
main:
  require input exists
    otherwise:
      abort with "An input is required."

  generate result from input as output

  return output as output
```

## Appendix

Guidance for the generate step.
