# Requirement review: code-reviewer

Source: sources/code-reviewer/SKILL.md
Reviewed by: <your name>
Date: <YYYY-MM-DD>
Candidate status: AI-drafted, AI-reviewed three times (drafting session; external AI
reviews 2026-11-20, revisions 2 and 3). Not human-approved: freezing needs the human
reviewer's name and date.

**How to review.** These are model-drafted candidates. For each line: keep it
(`[x]`), drop it (change to `[ ]`), or edit the requirement text so it says
what the source really requires. Add anything missing as a new line with the
next free ID (`CR-24`, ...); quote the source span, or write `inferred` if you
accept it without one. Kinds: obligation, prohibition, exception, ordering,
authority, output. Then fill in the two lines above.

Ask of each line: if a converted skill lost or weakened this, would the skill
be wrong? If not, drop it.

- [x] CR-1 | ordering | Summarize the PR's intent in one sentence before reviewing structure, details or tests. | "Summarize the PR's intent in one sentence before proceeding."
- [x] CR-2 | exception | If the intent cannot be summarized, ask the author to clarify instead of continuing the review. | "If you cannot, ask the author to clarify."
- [x] CR-3 | obligation | Read the PR description and understand the problem being solved. | "Read PR description, understand the problem being solved."
- [x] CR-4 | obligation | Review architecture and design: whether the change follows existing codebase patterns and whether new abstractions are justified. | "Does this follow existing patterns in the codebase? Are new abstractions justified?"
- [x] CR-5 | obligation | Check code quality, security and performance, including N+1 queries, hardcoded secrets and injection risks. | "Are there N+1 queries, hardcoded secrets, or injection risks?"
- [x] CR-6 | obligation | Check for security issues with the OWASP Top 10 as the baseline. | "Check for security issues (OWASP Top 10 as baseline)"
- [x] CR-7 | obligation | Validate tests: edge cases are covered and tests assert behavior, not implementation. | "Are edge cases covered? Do tests assert behavior, not implementation?"
- [x] CR-8 | obligation | Review tests as thoroughly as code. | "Review tests as thoroughly as code"
- [x] CR-9 | ordering | Note critical issues as soon as they are found, not only at the end. | "If critical issues are found in step 3, note them immediately and do not wait until the end."
- [x] CR-10 | exception | When the author explained a non-obvious choice in comments, acknowledge that reasoning before suggesting an alternative. | "acknowledge their reasoning before suggesting an alternative"
- [x] CR-11 | prohibition | When a linter or formatter is configured, do not block on style preferences or nitpick style. | "Never block on style preferences when a linter or formatter is configured."
- [ ] CR-12 | prohibition | Do not nitpick style when linters exist. | "Nitpick style when linters exist"
- [x] CR-13 | prohibition | Do not block on personal preferences. | "Block on personal preferences"
- [x] CR-14 | prohibition | Do not be condescending or rude. | "Be condescending or rude"
- [x] CR-15 | prohibition | Do not demand perfection. | "Demand perfection"
- [x] CR-16 | prohibition | Do not review without understanding why the change was made. | "Review without understanding the why"
- [x] CR-17 | obligation | Give specific, actionable feedback. | "Provide specific, actionable feedback"
- [x] CR-18 | obligation | Include code examples in suggestions. | "Include code examples in suggestions"
- [x] CR-19 | obligation | Praise good patterns; never skip praising good work. | "Praise good patterns"
- [x] CR-20 | obligation | Prioritize feedback from critical to minor. | "Prioritize feedback (critical → minor)"
- [x] CR-21 | output | The report contains a summary (one-sentence intent recap and overall assessment), critical, major and minor issues, positive feedback, questions for the author, and a verdict. | "Code review report must include:"
- [x] CR-22 | output | The verdict is one of Approve, Request Changes or Comment. | "Approve / Request Changes / Comment"
- [x] CR-23 | authority | Review only: read and search code; never edit files or run commands (derived from the tool allowlist, not stated in the prose; an allowlist limits the skill's tools, it is not host-enforced isolation). | "allowed-tools: Read, Grep, Glob"

## Revision log

- CR-11 now covers both blocking on and nitpicking style when a linter or formatter exists; CR-12 dropped as overlapping (external AI review: CR-11/12/13 overlap; CR-13, personal preferences in general, kept as distinct).
- CR-23 states that it is derived from `allowed-tools`, not from the prose (external AI review).
- Revision 3: CR-23 notes that a tool allowlist is not host-enforced isolation (external AI review).
