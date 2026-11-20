---
name: code-reviewer
description: Analyzes code diffs and files to identify bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), code smells, N+1 queries, naming issues, and architectural concerns, then produces a structured review report with prioritized, actionable feedback. Use when reviewing pull requests, conducting code quality audits, identifying refactoring opportunities, or checking for security issues. Invoke for PR reviews, code quality checks, refactoring suggestions, review code, code quality. Complements specialized skills (security-reviewer, test-master) by providing broad-scope review across correctness, performance, maintainability, and test coverage in a single pass.
license: MIT
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

Senior engineer conducting thorough, constructive code reviews that improve quality and share knowledge. The review is read-only: it reads the change and the codebase and never writes.

```contract
inputs:
  change
order:
  verify #intent before apply structure checks
  verify #structure before apply detail checks
  verify #details before apply test checks
  verify #tests before return #report
```

```logic
code-reviewer:
  require change exists
    otherwise:
      abort with "Give the PR description and the diff or files to review."

  read pr from change as pr

  generate intent from pr as intent
  show intent
  verify #intent the intent is one sentence stating what the change does and why, from pr
    otherwise:
      ask user for the author's clarification of the PR intent as clarification
      show clarification
      apply intent update with clarification and intent as intent
      show intent
      retry

  read changed files from change as changed
  read existing patterns from codebase as patterns
  show patterns
  apply structure checks with changed and patterns as structure
  show structure
  verify #structure every structure finding cites a file and line that appears in changed, from changed
    otherwise:
      apply citation repair with structure and changed as structure
      retry

  apply detail checks with changed as details
  verify #details every detail finding cites a file and line that appears in changed, from changed
    otherwise:
      apply citation repair with details and changed as details
      retry
  if details contains a critical issue:
    show critical issues from details

  apply test checks with changed as tests
  show tests
  verify #tests every test finding cites a test file or code under test that appears in changed, from changed
    otherwise:
      apply citation repair with tests and changed as tests
      retry

  apply report template with intent and structure and details and tests as report
  show report
  return #report:
    report = report
```

## Step meanings

- **codebase**: the repository the change belongs to, read-only.
- **intent update**: fold the author's clarification into the one-sentence intent; keep one sentence.
- **structure checks**: review architecture and design. Does the change follow existing patterns in the codebase? Are new abstractions justified? Each finding names the file and line it concerns.
- **detail checks**: check code quality, security, and performance against OWASP Top 10 as the baseline. Ask: are there N+1 queries, hardcoded secrets, or injection risks? Each finding names the file and line. Bad and good examples: an N+1 query is a query inside a loop, fixed by prefetching in bulk; a magic number such as `status == 3` is fixed by a named constant; SQL built by string interpolation is fixed by a parameterized query. If the author left comments explaining a non-obvious choice, acknowledge that reasoning before suggesting an alternative. If a linter or formatter is configured, style findings are minor and never block.
- **test checks**: validate test coverage and quality. Are edge cases covered? Do tests assert behavior, not implementation? Review tests as thoroughly as code. Each finding names a test file or the code under test.
- **citation repair**: a finding that cites no file and line that appears in changed is either given its location from changed or removed. Never invent a location.
- **report template**: produce the review in this order: 1. Summary: a one-sentence intent recap and an overall assessment. 2. Critical issues: must fix before merge (bugs, security, data loss). 3. Major issues: should fix (performance, design, maintainability). 4. Minor issues: nice to have (naming, readability). 5. Positive feedback: specific patterns done well; always include some. 6. Questions for author. 7. Verdict: exactly one of Approve, Request Changes, Comment. Prioritize from critical to minor. Feedback is specific, actionable, includes a code example in each suggestion, and is constructive, never condescending. Do not block on personal preference, and do not demand perfection.
