# Evidence review (independent conversion)

```contract
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
  read project instructions, target diff, and necessary callers from repo as code
  generate correctness, security, and behavior findings with reachable failure cases, excluding style unless requested, from code as findings
  verify #evidence each finding has location, trigger, consequence, and supporting source from findings
    otherwise:
      generate report with unverified concerns and missing evidence from findings as report
      return report as report
  generate report with impact-ordered findings, minimal corrections, independent verification advice, limitations, and unrun checks from findings as report
  return report as report
```

## Appendix

Report briefly: summary, confirmed findings, limitations, unrun checks.
High = reachable security breach, data loss, or core behavior failure;
medium = limited functional failure; low = minor consequential defect.
Expected results need an independent specification, caller contract, or
source; the current output is not an oracle. Suggested tests are
unexecuted, not reproduction evidence. Say when no findings are
confirmed; that does not establish correctness.
