# Independent review response — 2026-11-12

Source: user-supplied independent review of commit e4b07a6. Scores are
editorial judgments, not measurements. This document tracks the proposed
work without claiming the architectural findings are resolved.

## First corrections

- Ledger start accepts repeated `--require NAME` milestones, captured before
  execution. Exact names and successful events determine recorded milestone
  completion. No requirements means `execution_complete: null`, not true.
- Reports separate ordering validity, mechanism-level evidence validity
  (null unless strict mode), and recorded milestone completion. `ok` remains
  a compatibility field for the requested checks, not full conformance.
- Conform's read-only command exemption uses an exact token allowlist.
  Chaining, substitution, output-writing options and external-diff options
  receive no exemption. This is observation, not shell containment; even
  accepted Git commands depend on host configuration and executable trust.

## Prioritized remaining work

| Priority | Work | Acceptance evidence |
| --- | --- | --- |
| P0 | Bind prerequisites to verifiers | Wrong executable, arguments, input hashes and irrelevant successful commands rejected |
| P0 | Trusted operational controller | Protected write blocked before verification; no alternate agent-accessible write path |
| P0 | Evidence lifecycle | Input changes invalidate evidence; policy and verifier identity committed independently of agent |
| P1 | Independent recording | External checkpoint detects tail truncation and rewritten chains; recorder coverage reported |
| P1 | Isolated conform runs | Filesystem, process and network isolation tested, including transient and out-of-workspace effects |
| P1 | Controlled A/B/C evaluation | Equal content/tasks/models/budgets, randomized repetitions; raw results retained |
| P1 | CI and release gates | Linux/Windows supported Python matrix, mutations, installed-package CLI smoke checks |
| P2 | Stable operation identities | Incidental prose edits do not alter rule binding |
| P2 | Explicit refinements | Conservative analysis retained when predicates cannot establish implications |
| P2 | Short onboarding | Broken procedure, diagnostic, correction and observed runtime consequence |

The trusted controller must own protected capabilities. A wrapper invoked
voluntarily by an unrestricted agent is not a security boundary. Specify
that boundary before implementing a guard. Required milestones likewise
cover only the declared recorded milestones, not all real-world activity.

## Experiment protocol to implement

Compare prose, equal-content checked procedures, and enforced procedures
on the same sensitive-configuration tasks. Include attempted skipped
reviews, irrelevant verifier commands, stale inputs, direct writes,
legitimate repairs and verifier failures. Measure unauthorized writes,
false evidence acceptance, completed tasks, latency/tokens and false blocks.
Retain seeds, versions, budgets, raw traces and filesystem observations.
Do not claim an improvement until the runs exist; paid model evaluation
and infrastructure provisioning are separate execution steps.
