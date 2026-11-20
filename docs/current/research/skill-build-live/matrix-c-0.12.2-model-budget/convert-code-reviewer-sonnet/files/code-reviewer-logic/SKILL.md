---
name: code-reviewer
description: Analyzes code diffs and files to identify bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), code smells, N+1 queries, naming issues, and architectural concerns, then produces a structured review report with prioritized, actionable feedback. Use when reviewing pull requests, conducting code quality audits, identifying refactoring opportunities, or checking for security issues. Complements specialized skills (security-reviewer, test-master, architecture-designer) by providing broad-scope review across correctness, performance, maintainability, and test coverage in a single pass.
license: MIT
allowed-tools: Read, Grep, Glob
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: quality
  triggers: code review, PR review, pull request, review code, code quality
  role: specialist
  scope: review
  output-format: report
  related-skills: security-reviewer, test-master, architecture-designer
---

# Code Reviewer

Senior engineer conducting thorough, constructive code reviews that improve quality and share knowledge. The review is read-only: it uses only Read, Grep and Glob and changes nothing in the reviewed code.

```contract
inputs:
  request, target
order:
  verify #intent the intent summary is a single sentence before generate structure findings
  verify #report the report meets the output and tone rules before return#reviewed
```

```logic
code-reviewer:
  require target exists
    otherwise:
      abort with "Name the pull request, diff or files to review."

  label context:
  read PR description and the problem being solved from target as description
  generate intent summary from description as intent
  verify #intent the intent summary is a single sentence that states the problem being solved from intent
    otherwise:
      ask user for a clarification of the PR's intent from the author as clarification
      apply update with clarification as description
      generate intent summary from description as intent
      retry

  read review checklist from references
  read common issues from references

  generate structure findings from target, intent as structure
  apply review conventions with structure as structure

  generate detail findings from target, structure as details
  apply review conventions with details as details
  apply security baseline with details as details
  if details contain critical issues:
    show critical issues in details

  read spec compliance guidance from references
  generate test findings from target, details as tests
  apply review conventions with tests as tests

  read report template from references
  read feedback examples from references
  generate review report from intent, structure, details, tests as report
  apply report rules with report as report
  verify #report the report meets the output and tone rules from report
    otherwise:
      if the repair budget is spent:
        return #blocked report as blocker
      apply report rules with report as report
      retry

  show report
  return #reviewed:
    report
```

## Step meanings

- **update**: fold the author's clarification into the PR description.
- **target**: the pull request, diff or files named by the user; the reviewer reads it with Read, Grep and Glob only.
- **review conventions**: for this stage's findings: be specific and actionable and include code examples in suggestions (N+1 queries: prefetch in bulk, not queries inside a loop; magic numbers: named constants; SQL injection: parameterized queries, never string interpolation). Structure stage: does the change follow existing codebase patterns, and are new abstractions justified? Details stage: check code quality, security and performance, including N+1 queries, hardcoded secrets and injection risks. Tests stage: review tests as thoroughly as code; are edge cases covered, and do tests assert behavior rather than implementation? If the author left comments explaining a non-obvious choice, acknowledge their reasoning before suggesting an alternative. Never block on style preferences when a linter or formatter is configured, and never review without understanding the why. Draw on SOLID, DRY, KISS, YAGNI, design patterns, language idioms and testing patterns. Record specific good patterns for praise.
- **security baseline**: check the details against the OWASP Top 10 as the baseline.
- **report rules**: the report must contain, in order: 1. Summary (one-sentence intent recap plus overall assessment); 2. Critical issues (must fix before merge: bugs, security, data loss); 3. Major issues (should fix: performance, design, maintainability); 4. Minor issues (nice to have: naming, readability); 5. Positive feedback (specific patterns done well); 6. Questions for author (clarifications needed); 7. Verdict (Approve, Request Changes or Comment). Feedback is prioritized from critical to minor, specific and actionable, with code examples in suggestions, and it praises good patterns. The tone is constructive: never condescending or rude, no nitpicking style when linters exist, no blocking on personal preferences, no demanding perfection, no skipping praise of good work.
- **references**: the `references/` folder of the original code-reviewer skill. Its files (review-checklist.md, common-issues.md, feedback-examples.md, report-template.md, spec-compliance-review.md, receiving-feedback.md) were not present when this skill was converted; if one is missing, continue from these step meanings. Load receiving-feedback.md when responding to review comments.
