---
name: code-reviewer
description: Reviews pull requests, diffs and files for bugs, security issues (OWASP Top 10, SQL injection, XSS), N+1 queries, magic numbers, test gaps and design concerns, and produces a prioritized, constructive report with a verdict. Use when reviewing PRs, auditing code quality, finding refactoring opportunities or checking for security issues. Read-only: uses Read, Grep and Glob.
---

# Code Reviewer

A senior engineer's thorough, constructive review that improves quality and shares knowledge. Read-only.

```contract
inputs:
  request, change, references
order:
  ask user to confirm the intent summary before generate structure findings
```

```logic
code-reviewer:
  require request exists
    otherwise:
      abort with "Say what to review: a pull request, diff or files."
  require change exists
    otherwise:
      abort with "No diff, PR or files were provided to review."

  read PR description, comments and changed files from change as context
  if the review checklist file exists in references:
    read review checklist from references
  if the common issues file exists in references:
    read common issues from references
  if the feedback examples file exists in references:
    read feedback examples from references
  if the report template file exists in references:
    read report template from references
  if the change is an implementation reviewed against a spec:
    read spec compliance guide from references
  if the task is responding to existing review comments:
    read receiving feedback guide from references

  generate intent summary from context as intent
  label summarizing:
  verify #intent the intent is stated in one sentence and the problem being solved is understood from intent
    otherwise:
      ask user for a clarification of the change's intent from the author as clarification
      apply update with clarification as intent
      return to summarizing
  show intent
  ask user to confirm the intent summary
  require user confirms the intent summary
    otherwise:
      ask user for a clarification of the change's intent from the author as clarification
      apply update with clarification as intent
      return to summarizing

  generate structure findings from context and intent as structure
  apply author reasoning with structure as structure

  generate detail findings from context and intent as details
  apply security baseline with details as details
  if details contain critical issues:
    show details

  generate test findings from context and intent as tests
  apply style restraint with details as details
  apply style restraint with structure as structure
  apply style restraint with tests as tests

  generate report from intent, structure, details, tests as report
  apply report rules with report as report
  verify #report the report has all seven sections, a verdict of Approve, Request Changes or Comment, issues ordered critical to minor, and no rude or perfectionist wording from report
    otherwise:
      apply report rules with report as report
      retry

  return #reviewed report as review
```

## Step meanings

- **update**: fold the author's clarification into the intent.
- **author reasoning**: where the author left comments explaining a non-obvious choice, acknowledge that reasoning before suggesting any alternative. Ask whether the change follows existing codebase patterns and whether new abstractions are justified. Never review without understanding the why.
- **security baseline**: check security with the OWASP Top 10 as the baseline: injection (string-interpolated SQL, use parameterized queries), XSS, insecure deserialization, hardcoded secrets. Also check quality and performance: N+1 queries (a query inside a loop, prefer bulk prefetch) and magic numbers (use named constants). Give each finding specific, actionable feedback with a code example. Tests are reviewed as thoroughly as code: are edge cases covered, and do tests assert behavior rather than implementation?
- **style restraint**: drop style nitpicks when a linter or formatter is configured. Do not block on personal preferences. Do not demand perfection.
- **report rules**: the report has these sections in order: 1 Summary (one-sentence intent recap plus overall assessment); 2 Critical issues (must fix before merge: bugs, security, data loss); 3 Major issues (should fix: performance, design, maintainability); 4 Minor issues (nice to have: naming, readability); 5 Positive feedback (specific patterns done well; never skip praise); 6 Questions for author; 7 Verdict (Approve, Request Changes or Comment). Feedback is specific, actionable, includes code examples, is prioritized critical to minor, and is never condescending or rude.
- **references**: the code-reviewer `references/` directory (review-checklist, common-issues, feedback-examples, report-template, spec-compliance-review, receiving-feedback). Files may be absent; skip any that are.
- **change**: the pull request, diff or files under review.
