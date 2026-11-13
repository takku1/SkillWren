# Skill B outcomes (stub draft -> human revision -> enforced execution)

The stub adapter proposed a generic check-then-record skeleton with four
unresolved questions and two stated assumptions. Everything concrete --
the check command, the pass criterion, the note target, the abort path --
is human-authored revision. The proposal itself would not have worked.

## Steps 1-4: draft, validate, explain, approve

- `draft --adapter-file adapter.json`: proposal saved; assumptions and
  questions printed; exit 0 with "Not approved".
- Human revision answered all four questions in `flow.md`.
- `check --fragment`: clean. `explain-workflow` saved as
  `explanation.txt`.
- `approve --policy policy.json`: approved; `#note` covered by
  `write#note`, `#coverage` uncovered (agent-side verify, same pattern
  as skill A).

## Steps 5-8: invoke on real repositories

Gap subject (README omits `clean`):
- Ledger exec exit 1, verdict `gaps`.
- Guard `verify` of the gaps candidate: denied.
- Ledger check: `incomplete`. Correct.

Clean subject (all three commands documented):
- Guard session: raw write denied, verify accepted, write accepted;
  `COVERAGE.md` holds the exact candidate bytes.
- Note with `--detail 'criterion: verdict clean, ...'`; milestones still
  match the step name exactly, detail rides along.
- Ledger check `--require-evidence`: `valid, complete`.

## Step 10

Appending `# probe` invalidated approval (exit 1); rewriting the
canonical bytes restored `approved: true` with the original timestamp,
proving byte-identity rather than re-approval.

## Guarantee accounting

- Statically checked: order rule, abort branch, typed IDs.
- Runtime-enforced: single-use binding, clean-only verifier, fail-closed
  garbage input.
- Agent-dependent: answering the draft's questions, running the check,
  choosing the candidate. The stub contributed structure only.
