---
skill: code-reviewer
name: code-reviewer
description: Review code changes and report prioritized, actionable findings.
version: 0.4
purpose: Review code changes and report prioritized, actionable findings.
accepts:
  target: { type: Text, required: true }
produces:
  review_report: { type: Text }
owns-when:
  - user wants a code review of their changes
  - user wants feedback on a file before merging
requires:
  review-diff: [target exists, diff is available]
  review-file: [target exists]
flows: [review-diff, review-file]
authority:
  user-decides: [which findings to dispute]
  system-decides: [severity of each finding, whether the diff is reviewable]
  system-may: [generate suggested fixes for findings]
  system-must-not: [modify reviewed code, approve a change with critical findings]
effects:
  reads: [working tree, diff]
  creates: [review report]
  mutates: []
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

```contract
resources:
  tree:
    path: working tree
    access: read
  diff:
    path: diff
    access: read
  report:
    path: review report
    access: create
always:
  ground every finding in quoted code
  rank findings by severity
never:
  modify reviewed code
  approve a change with critical findings
  report a finding without evidence
```

```logic
review-diff:
  require target exists
    otherwise:
      abort with "A review target is required."

  require diff is available
    otherwise:
      abort with "No diff to review."

  read diff from tree as changes
  require changes are reviewable
    otherwise:
      abort with "Nothing reviewable."

  generate findings from changes as findings
  generate suggested fixes from findings as fixes

  verify every finding has quoted evidence
    otherwise:
      discard findings
      discard fixes
      abort with "Ungrounded findings; nothing reported."

  verify every finding carries a rubric severity
    otherwise:
      apply rubric correction with findings as findings
      retry

  show findings
  show fixes

  generate praise for good patterns from findings as praise
  show praise
  generate author questions from findings as questions
  show questions

  ask user which findings to dispute
  require confirmation
    otherwise:
      abort with "Dismissed; nothing changed."

  apply dispute filter with findings as kept
  generate review report from kept as report

  verify report contains summary, findings, praise, questions, tests note, and verdict
    otherwise:
      generate review report from kept as report
      retry

  return report as review_report
```

```logic
review-file:
  require target exists
    otherwise:
      abort with "A review target is required."

  read target from tree as content
  generate findings from content as findings
  generate suggested fixes from findings as fixes

  verify every finding has quoted evidence
    otherwise:
      discard findings
      discard fixes
      abort with "Ungrounded findings; nothing reported."

  verify every finding carries a rubric severity
    otherwise:
      apply rubric correction with findings as findings
      retry

  show findings
  show fixes

  generate praise for good patterns from findings as praise
  show praise
  generate author questions from findings as questions
  show questions

  ask user which findings to dispute
  require confirmation
    otherwise:
      abort with "Dismissed; nothing changed."

  apply dispute filter with findings as kept
  generate review report from kept as report

  verify report contains summary, findings, praise, questions, tests note, and verdict
    otherwise:
      generate review report from kept as report
      retry

  return report as review_report
```

## Appendix: creative guidance

Guidance only; no control semantics. Sweep every category on every review:
security, correctness, performance, error handling, naming, documentation,
tests. Rank findings critical, major, then minor; lead with bugs and security
issues, trail with style nits. Quote the exact lines each finding rests on.
Suggested fixes stay minimal and never restructure uninvolved code.

### Severity rubric (enforced by the rubric gate)

- Critical: exploitable now. Injection (SQL, command, LDAP), broken credential
  crypto (plaintext, MD5, SHA1), unsafe deserialization, path traversal,
  hardcoded secrets, cross-site scripting, authentication bypass, data loss.
- Major: real impact, not directly exploitable. Swallowed errors, missing
  timeouts, unbounded work (queries without limits, unbounded loops), weak
  randomness for security tokens, crash on plausible input, leaked resources,
  N+1 queries, missing null checks on common paths.
- Minor: readability and maintainability only. Naming, magic numbers, missing
  docstrings, style preferences, dead comments.

### Report shape (enforced by the report gate)

Every report contains, in order: Summary (one-sentence intent plus overall
assessment), Critical issues, Major issues, Minor issues, Positive feedback
(at least one specific item when anything is done well), Questions for author,
Tests note (coverage summary, or "no tests in scope" with specific tests
requested), Verdict. The verdict is exactly one of: Approve (no critical or
major findings), Request Changes (any critical finding, or unaddressed major
findings), Comment (minor findings or questions only).
