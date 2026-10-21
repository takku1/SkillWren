---
skill: evidence-review-logic
name: evidence-review-logic
description: Review a code change for consequential defects using source evidence; report uncertainty and verification advice without editing or executing it.
version: 0.5
accepts:
  target: { type: Path, required: true }
produces:
  report: { type: Text }
owns-when: [user wants an evidence-based code review]
requires:
  review: [target exists]
flows: [review]
authority:
  user-decides: []
  system-decides: [scope, evidence, severity]
  system-may: []
  system-must-not: [invent evidence]
effects:
  reads: [repo]
  creates: []
  mutates: []
risk: low
cost: moderate
budget: { header: 400, body: 2500 }
---

```contract
resources:
  repo:
    path: reviewed project
    access: read
    immutable: true
always:
  follow project conventions; limit findings to the supplied change
  distinguish source evidence, runtime claims, and unverified concerns
never:
  edit, refactor, execute, commit, or publish during review
  invent requirements, environment, traces, or test outputs
```

```logic
review:
  require target exists
    otherwise:
      abort with "Supply the target."
  read project instructions, diff, {target}, and necessary callers/dependencies from repo as code
  generate correctness/security/behavior findings with credible reachable failure cases; exclude style preferences unless requested from code as findings
  verify each confirmed finding has file/lines, trigger, consequence, and supporting {code} from findings
    otherwise:
      generate report labeling unsupported concerns unverified and naming missing evidence from findings as report
      return report as report
  generate report with impact-ranked findings, minimal correction directions, independent-oracle regression suggestions, limitations, and unrun checks from findings as report
  return report as report
```

## Appendix

Report briefly: summary, confirmed findings, limitations, unrun checks.
High = reachable security breach/data loss/core failure; medium = limited
functional failure; low = minor consequential defect. Justify impact, not
keywords. Expected test results need a specification/caller contract/independent
source; current output is not an oracle. Suggested tests are unexecuted, not
reproduction evidence. Say when no findings are confirmed; correctness remains
unproved. Add detail only if requested.
