---
# TODO: pick a kebab-case id; set skill, name, description, purpose.
skill: my-skill
name: my-skill
description: One sentence saying what this skill does.
version: 0.5
purpose: One sentence saying what this skill does.
# TODO: declare inputs (closed types) and outputs.
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
# TODO: write 1-4 triggers in requester words.
owns-when:
  - user wants to transform the input
# TODO: copy each flow's leading require lines here, exact wording.
requires:
  main: [input exists]
flows: [main]
# TODO: fill all four lists; phrase user-decides like your asks.
authority:
  user-decides: [whether to approve the output]
  system-decides: [whether the input is valid]
  system-may: []
  system-must-not: [infer user approval]
# TODO: summarize every resource the flows touch.
effects:
  reads: [input]
  creates: [output]
  mutates: []
risk: low
cost: cheap
# Budgets are cl100k tokens (approx ceil(chars/4)), not bytes.
budget: { header: 400, body: 2500 }
---

# My Skill

TODO: copy this file, rename the skill, then work the TODOs top to
bottom. Procedure: docs/authoring-guide.md. This preamble is ignored.

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

  verify output is valid
    otherwise:
      discard output
      abort with "Could not produce a valid result."

  show output
  ask user to approve output
  require confirmation
    otherwise:
      abort with "Declined; nothing changed."

  return output as output
```

## Appendix

TODO: guidance for the generate step goes here (taste, shape, examples).

TODO checklist before `skillwren check`: header fields filled; contract
resources match the flows; every require/verify that can fail has an
otherwise repair; every decision ask has a confirmation after it.
