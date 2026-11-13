# Skill A outcomes (manual NL -> SkillWren -> guard-enforced execution)

Authored by hand from `intent.md`. Every command below was actually run;
subjects live outside the repo (`skill-subjects/a-blocked`, `a-clean`).

## Steps 1-4: author, validate, explain, approve

- `check --fragment flow.md`: clean.
- `explain-workflow` saved as `explanation.txt`; states the order rule,
  the abort branch, the effect (`writes target`), and that the exec step
  is advisory-only while `verify #deps`/`write #report` are enforceable
  if the policy defines the operation.
- `approve --by lifecycle-probe --policy policy.json`: approved, with an
  honest coverage gap -- `#report` is covered by `write#report`;
  `#deps` is uncovered because no separate guard operation performs the
  dependency verification. That check runs as ledger evidence plus the
  verifier's byte re-check at write time.

## Steps 5-8: invoke on real repositories

Blocked subject (`requests==1.0.0`):
- `ledger exec 'dependency check ran'` exit 1, verdict `blocked`.
- Guard `verify` of the blocked candidate: denied
  (`verifier rejected candidate or returned wrong digest`).
- An earlier draft of the verifier accepted any well-formed verdict and
  approved the blocked candidate; tightening it to `clean`-only made the
  write impossible rather than merely forbidden. Caught by executing,
  not by review.
- `ledger check`: `incomplete`, both milestones missing. Correct.

Clean subject:
- Guard session: raw write denied (`missing, stale or consumed
  verification`), verify accepted, write accepted; `REPORT.md` holds
  the exact candidate bytes.
- A trailing empty request line was also denied (fail-closed on
  unparseable input).
- `ledger note 'report written'` with the report as artifact;
  `ledger check --require-evidence`: `valid, complete`.

## Step 10: approval invalidation

Appending one comment line to `flow.md` made `approve --check` report
`file changed since approval` (exit 1); restoring the canonical bytes
returned `approved: true`. Note: the editor used mid-probe introduced a
CRLF that survived the first restore, so restoration was done by
rewriting the canonical bytes and re-running the ledger sequences --
itself evidence that the digest means exact bytes, not intent.

## Guarantee accounting

- Statically checked: order rule, abort branch, typed IDs, clean check.
- Runtime-enforced: single-use verify-then-write binding, verifier
  re-check of candidate bytes, fail-closed crashes and garbage input.
- Agent-dependent: running the check at all, choosing the candidate,
  and the `#deps` verification step (no separate guard operation).
