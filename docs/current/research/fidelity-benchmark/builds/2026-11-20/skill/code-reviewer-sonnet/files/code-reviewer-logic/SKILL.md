---
name: code-reviewer
description: Analyzes code diffs and files to identify bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), code smells, N+1 queries, naming issues, and architectural concerns, then produces a structured review report with prioritized, actionable feedback. Use when reviewing pull requests, conducting code quality audits, identifying refactoring opportunities, or checking for security issues.
license: MIT
allowed-tools: Read, Grep, Glob
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: quality
  role: specialist
  scope: review
  output-format: report
  related-skills: security-reviewer, test-master, architecture-designer
---

# Code Reviewer

Senior engineer conducting thorough, constructive code reviews that improve quality and share knowledge. Read-only: this skill reads, searches and reports; it never edits the code under review.

```contract
inputs:
  request, target
order:
  verify #intent the intent is one sentence before generate structure findings
  verify #intent the intent is one sentence before generate detail findings
  verify #details quality before generate test findings
  verify #tests tests were reviewed before generate review report
  verify #report the report has before return#reviewed
```

```logic
code-reviewer:
  require target exists
    otherwise:
      abort with "Name the pull request, diff or files to review."

  read PR description and changed code from target as change
  if the references folder exists:
    read review checklist and common issues from references
    read feedback examples and report template from references
  read linter and formatter configuration from target

  generate one-sentence PR intent from change as intent
  verify #intent the intent is one sentence and states the problem being solved from intent
    otherwise:
      ask user for the author's clarification of the PR intent as clarification
      apply update with clarification as change
      generate one-sentence PR intent from change as intent
      retry

  generate structure findings from change as structure
  apply structure questions with structure as structure

  generate detail findings from change as details
  apply detail checks with details as details
  verify #details quality, security and performance were all checked from details
    otherwise:
      apply detail checks with details as details
      retry
  if details contain critical issues:
    show details

  if the review covers implementations or spec verification:
    read spec compliance guidance from references
  generate test findings from change as tests
  apply test checks with tests as tests
  verify #tests tests were reviewed as thoroughly as code from tests
    otherwise:
      apply test checks with tests as tests
      retry

  if the author left comments explaining non-obvious choices:
    apply author reasoning with structure as structure
  if a linter or formatter is configured for the target:
    apply style suppression with details as details

  generate review report from structure, details, tests as report
  apply report rules with report as report
  verify #report the report has every required section in order, a courteous tone, and nothing reviewed without understanding the why from report
    otherwise:
      apply report rules with report as report
      retry

  return #reviewed:
    report
```

## Step meanings

- **update**: fold the author's clarification into the change description.
- **structure questions**: ask whether this follows existing codebase patterns and whether new abstractions are justified.
- **detail checks**: check code quality, security and performance. Ask about N+1 queries (prefetch in bulk, no queries inside loops), hardcoded secrets, magic numbers (use named constants) and injection risks (parameterized queries, not string interpolation). Baseline is OWASP Top 10. Knowledge: SOLID, DRY, KISS, YAGNI, design patterns, language idioms, testing patterns. Critical issues are noted immediately, not held to the end.
- **test checks**: ask whether edge cases are covered and whether tests assert behavior, not implementation.
- **author reasoning**: acknowledge the author's stated reasoning before suggesting any alternative.
- **style suppression**: drop style nitpicks and never block on style or personal preferences when a linter or formatter is configured.
- **report rules**: be specific and actionable, include code examples in suggestions, prioritize critical to minor, praise good patterns specifically, never be condescending or rude, never demand perfection, never block on personal preferences. Sections in order: Summary (one-sentence intent recap plus overall assessment), Critical issues (must fix: bugs, security, data loss), Major issues (should fix: performance, design, maintainability), Minor issues (naming, readability), Positive feedback, Questions for author, Verdict (Approve / Request Changes / Comment).
- **references**: `references/` beside the skill; review-checklist, common-issues, feedback-examples, report-template, spec-compliance-review, receiving-feedback. Optional and may be absent.
- **target**: the PR, diff or files under review.
