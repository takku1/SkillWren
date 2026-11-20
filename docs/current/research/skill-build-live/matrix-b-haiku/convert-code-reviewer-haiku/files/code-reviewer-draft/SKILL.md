---
name: code-reviewer
description: Review code diffs and files for bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), N+1 queries, code smells, naming issues, and architectural concerns, then produce a categorized report with prioritized, actionable feedback. Use when reviewing pull requests, auditing code quality, finding refactoring opportunities, or checking for security issues.
---

# Code reviewer

Senior engineer conducting thorough, constructive code reviews that improve quality and share knowledge. This procedure reads the review target and never modifies it.

```contract
inputs:
  target, pr_description
order:
  verify #intent before apply structure review
  apply critical notes before apply test review
  apply test review before generate report
  generate report before return #report
```

```logic
code-reviewer:
  require target exists
    otherwise:
      abort with "Name the pull request, diff, or files to review."

  generate intent from pr_description and target as intent

  label intent_check:
  verify #intent the intent states the PR's purpose in one sentence from intent
    otherwise:
      ask user to have the author clarify the PR's intent
      require user has the author clarified the PR's intent
        otherwise:
          abort with "PR intent is unclear; the review stops until the author clarifies it."
      return to intent_check

  apply structure review with target as structure
  show structure
  apply detail review with target as details
  apply critical notes with details as critical
  show critical

  apply test review with target as tests
  show tests

  generate report from intent, structure, details, critical, tests as report
  apply output template with report as review

  return #report review as review
```

## Step meanings

- **structure review**: Check whether the change follows existing patterns in the codebase and whether new abstractions are justified. Draw on SOLID, DRY, KISS, YAGNI, and design patterns. Ask: does this follow existing patterns, and are new abstractions justified?
- **detail review**: Check code quality, security, and performance, using the OWASP Top 10 as the baseline (SQL injection, XSS, insecure deserialization, hardcoded secrets), N+1 queries, magic numbers, and naming. Use these patterns: prefetch in bulk instead of querying inside a loop; name magic numbers as constants; use parameterized queries instead of string interpolation. If the author has left comments explaining a non-obvious choice, acknowledge their reasoning before suggesting an alternative. Never block on style when a linter or formatter is configured, and never block on personal preferences. Note critical issues as soon as they are found.
- **critical notes**: List each critical issue (must fix before merge: bugs, security, data loss) with its location, in the order found. Do not wait for the end of the review.
- **test review**: Check that edge cases are covered and that tests assert behavior, not implementation. Review tests as thoroughly as code.
- **output template**: Produce the report with these seven sections in order: 1. Summary: one-sentence intent recap and overall assessment. 2. Critical issues: must fix before merge. 3. Major issues: should fix (performance, design, maintainability). 4. Minor issues: nice to have (naming, readability). 5. Positive feedback: specific patterns done well. 6. Questions for author. 7. Verdict: Approve, Request Changes, or Comment; Request Changes when any critical issue exists. Prioritize feedback from critical to minor. Give specific, actionable feedback with code examples in suggestions. Be courteous, never condescending, and praise good work.
