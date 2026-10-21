---
skill: careful-summary
name: careful-summary
description: Summarize supplied text while retaining its constraints and exceptions.
version: 0.5
accepts:
  request: { type: Text, required: true }
produces:
  summary: { type: Text }
owns-when:
  - user requests a faithful summary of supplied text
requires:
  summarize: [request exists]
flows: [summarize]
authority:
  user-decides: []
  system-decides: [whether the summary retains the constraints]
  system-may: []
  system-must-not: [omit an exception to make the summary shorter]
effects:
  reads: []
  creates: []
  mutates: []
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

# Careful summary

```contract
resources:
  request:
    path: supplied text
    access: read
always:
  preserve constraints and exceptions
never:
  invent a fact absent from the supplied text
```

```logic
summarize:
  require request exists
    otherwise:
      abort with "Supply the text to summarize."

  generate summary from request as summary
  verify summary preserves constraints and exceptions from request
    otherwise:
      abort with "Cannot establish that the summary is faithful."
  return summary as summary
```

## Appendix

@context fidelity from "fidelity.md" as instruction
@context examples from "examples.md" as example
