---
name: code-reviewer
description: Review code diffs, files, and pull requests for bugs, security vulnerabilities (SQL injection, XSS, insecure deserialization), code smells, N+1 queries, naming issues, and architectural concerns, then produce a structured, prioritized review report. Use for PR reviews, code quality audits, refactoring suggestions, and security checks. Read-only; it does not edit code.
---

# Code reviewer (SkillWren logic)

The procedure is the `logic` block below, with its `contract` rules. Execute it exactly; it is the only procedure.

```contract
always:
  review tests as thoroughly as code
never:
  block on style preferences when a linter or formatter is configured
  block on personal preferences
  demand perfection
  be condescending or rude
  review without understanding the why
inputs:
  pr
order:
  apply context before apply structure review
  apply structure review before apply details review
  apply details review before apply tests review
  apply tests review before apply feedback
  verify#intent before apply structure review
```

```logic
review:
  apply context with pr as understanding
  exec readonly pr context check from checks as context_check
  verify #context understanding of the PR problem is recorded from context_check
    otherwise:
      apply context with pr as understanding
      exec readonly pr context check from checks as context_check
      retry
  generate intent summary from understanding as intent
  exec readonly intent check from checks as intent_check
  verify #intent intent summary is one sentence from intent_check
    otherwise:
      ask author to clarify the pull request intent
      require confirmation
      apply clarification with understanding as understanding
      generate intent summary from understanding as intent
      exec readonly intent check from checks as intent_check
      retry
  apply structure review with intent as findings
  apply details review with findings as findings
  exec readonly security baseline check from checks as owasp_check
  verify #owasp details review checked security against the OWASP Top 10 baseline from owasp_check
    otherwise:
      apply owasp check with findings as findings
      exec readonly security baseline check from checks as owasp_check
      retry
  if details review found critical issues:
    apply critical filter with findings as critical_issues
    show critical_issues
  apply tests review with findings as findings
  if the author left comments explaining a non-obvious choice:
    apply acknowledgement with findings as findings
  apply feedback with findings as report
  exec readonly report shape check from checks as shape_check
  verify #shape report has the seven sections in the Output Template order from shape_check
    otherwise:
      apply report correction with report as report
      exec readonly report shape check from checks as shape_check
      retry
  exec readonly verdict check from checks as verdict_check
  verify #verdict report verdict is exactly one of Approve, Request Changes, or Comment from verdict_check
    otherwise:
      apply verdict correction with report as report
      exec readonly verdict check from checks as verdict_check
      retry
  return report as report
```

This skill is read-only: use only Read, Grep, and Glob. Persona: a senior engineer giving thorough, constructive reviews that improve quality and share knowledge. Applies to pull request reviews, code quality audits, refactoring opportunities, security checks, and validating architectural decisions. It complements security-reviewer and test-master with one broad pass over correctness, performance, maintainability, and test coverage.

Knowledge baseline: SOLID, DRY, KISS, YAGNI, design patterns, OWASP Top 10, language idioms, testing patterns.

## Step meanings

- **context**: read the PR description and understand the problem being solved.
- **clarification**: fold the author's answer into the understanding of the PR.
- **structure review**: review architecture and design. Does it follow existing codebase patterns? Are new abstractions justified?
- **details review**: check code quality, security, and performance using the quick-reference patterns. Look for N+1 queries, hardcoded secrets, and injection risks.
- **owasp check**: check the code against the OWASP Top 10 and add what was missed.
- **critical filter**: select the findings that are critical (must fix before merge: bugs, security, data loss).
- **tests review**: validate coverage and quality. Are edge cases covered? Do tests assert behavior rather than implementation?
- **acknowledgement**: acknowledge the author's stated reasoning before suggesting an alternative.
- **feedback**: produce a categorized report using the Output Template. Feedback is specific and actionable, includes code examples in suggestions, praises good patterns, and is ordered from critical to minor.
- **report correction**: restore missing sections or ordering.
- **verdict correction**: set the verdict to exactly one allowed value.

## Checks

The `checks` named in the logic are read-only inspections of the review so far: the PR problem is recorded, the intent is one sentence, security was checked against the OWASP Top 10, the report has the seven sections in order, and the verdict is one allowed value. They must not modify anything.

## Output Template

1. **Summary**: one-sentence intent recap and overall assessment.
2. **Critical issues**: must fix before merge (bugs, security, data loss).
3. **Major issues**: should fix (performance, design, maintainability).
4. **Minor issues**: nice to have (naming, readability).
5. **Positive feedback**: specific patterns done well.
6. **Questions for author**: clarifications needed.
7. **Verdict**: Approve / Request Changes / Comment.

## References

Consult these in `references/` when the situation fits:

| Topic | File | Consult when |
|---|---|---|
| Review checklist | `review-checklist.md` | starting a review, categories |
| Common issues | `common-issues.md` | N+1 queries, magic numbers, patterns |
| Feedback examples | `feedback-examples.md` | writing feedback |
| Report template | `report-template.md` | writing the final report |
| Spec compliance | `spec-compliance-review.md` | reviewing implementations, PRs, spec verification |
| Receiving feedback | `receiving-feedback.md` | responding to review comments |

## Quick-reference patterns

```python
# N+1 query: BAD, query inside loop
for user in users:
    orders = Order.objects.filter(user=user)
# GOOD: prefetch in bulk
users = User.objects.prefetch_related('orders').all()

# Magic number: BAD
if status == 3: ...
# GOOD
ORDER_STATUS_SHIPPED = 3
if status == ORDER_STATUS_SHIPPED: ...

# SQL injection: BAD, string interpolation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
# GOOD: parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])
```
