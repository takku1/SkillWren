---
name: code-reviewer
description: Review a diff, pull request, or set of files for correctness bugs, security vulnerabilities, code smells, N+1 queries, naming, architecture, and test coverage, then write a prioritized report with a verdict. Use when asked to review a PR, audit code quality, find refactoring opportunities, or check code for security issues.
---

# Code reviewer

```contract
inputs:
  request
order:
  verify#intent before apply structure review
  apply structure review before apply detail review
  apply detail review before apply test review
  apply detail review before show critical issues
  apply test review before apply review report
  apply review report before return#review
```

```logic
code-reviewer:
  require request exists
    otherwise:
      abort with "Name the diff, pull request, or files to review."

  read the code under review from request as target
    otherwise:
      abort with "The review target could not be read."

  generate pr intent from target as intent
  label intent check:
  verify #intent the author's intent is stated in one sentence from intent
    otherwise:
      ask user for the PR intent in one sentence as clarification
      apply intent update with clarification as intent
      return to intent check

  read the matching reference from references as guidance
    otherwise:
      abort with "A reference file named in the Reference Guide is missing; add it to references and rerun."

  apply structure review with guidance as structure
  apply detail review with structure as details
  if details has a critical issue:
    show critical issues from details

  apply test review with details as tests
  apply review report with tests as report
  show report
  return #review report as report
```

## Reference Guide

Load the matching file for the context of the review:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Review Checklist | `references/review-checklist.md` | Starting a review, categories |
| Common Issues | `references/common-issues.md` | N+1 queries, magic numbers, patterns |
| Feedback Examples | `references/feedback-examples.md` | Writing good feedback |
| Report Template | `references/report-template.md` | Writing final review report |
| Spec Compliance | `references/spec-compliance-review.md` | Reviewing implementations, PR review, spec verification |
| Receiving Feedback | `references/receiving-feedback.md` | Responding to review comments, handling feedback |

## Step meanings

- **intent update**: restate the PR's intent in one sentence using the author's clarification.
- **structure review**: check architecture and design. Does the change follow existing patterns in the codebase? Are new abstractions justified?
- **detail review**: check code quality, security, and performance using the Review Patterns and the MUST DO checks. Look for N+1 queries (query inside a loop), magic numbers (unnamed constants such as `if status == 3`), SQL injection (string-built queries), hardcoded secrets, and other injection risks. Security uses the OWASP Top 10 as baseline. Mark each finding critical, major, or minor.
- **critical issues**: the critical findings from details (bugs, security, data loss) that must be fixed before merge. Name them immediately.
- **test review**: validate coverage and quality. Are edge cases covered? Do tests assert behavior, not implementation? Review tests as thoroughly as code.
- **review report**: the report in this order: 1. Summary (one-sentence intent recap and overall assessment). 2. Critical issues (must fix before merge). 3. Major issues (should fix: performance, design, maintainability). 4. Minor issues (nice to have: naming, readability). 5. Positive feedback (specific patterns done well; never skip praise). 6. Questions for author. 7. Verdict: Approve, Request Changes, or Comment. Every suggestion gives specific, actionable feedback with a code example.
- **Constraints**: be respectful, never condescending. Do not nitpick style when a linter or formatter is configured; never block on personal preference or demand perfection. Review the why behind a choice before judging it. When the author has left comments explaining a non-obvious choice, acknowledge their reasoning before suggesting an alternative.
- **references**: the reference files named in the Reference Guide above.
- **knowledge**: SOLID, DRY, KISS, YAGNI, design patterns, OWASP Top 10, language idioms, and testing patterns.
- **read-only**: the review reads code and writes only the report. It never edits the code under review.
