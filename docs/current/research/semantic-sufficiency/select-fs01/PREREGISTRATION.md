# Preregistration: FS-01 full-stack representation study (DRAFT, UNEXECUTED)

First real (non-synthetic) certification study for `skillwren select`.
Question: does the new inline-logic SkillWren form preserve the decisions
of the original full-stack skill content, within stated risk budgets?
Status: draft. No data collected. Thresholds below were fixed before any
outcome was observed; changing them after seeing data requires a new
study, not an edit.

## Regime and scope

One study, one regime:

- `task_family`: `stack-design-build`
- `context_band`: `medium`
- `language`: `en`
- `risk_tier`: `standard`

Scope is limited to the brief pools below. Results do not generalize to
other task families, larger contexts, or live deployment traffic.

## Portfolio (fixed before sampling)

| Candidate | Content | Fallback rank | Rationale |
|---|---|---|---|
| `brief` | 312-token brief (FS-009) | 1 | Cheapest; try first |
| `concise` | Inline-logic SkillWren form (0.10) | 2 | The form under test |
| `full` | Original full-stack skill content | 3 | Safe fallback; holds the historical evidence |

Each candidate's exact bytes are frozen before the first run; the
`artifact_sha256` values in `study.json` (currently placeholders) must be
replaced with the real frozen digests. Any byte change after sampling
starts voids the study and requires a new `study_id`.

`inv_verified: true` is attested by the evaluator on the basis of the
sandboxed harness (network-denied writes, `isolation_probe` evidence,
SkillWren ledger per run); the verification evidence hash goes in
`cfg_sha256`. Without that evidence on file, the attestation must be
removed and every candidate will (correctly) come back uncertified.

## Cells and sampling

Cells are model-group pairs, complete Cartesian product:

- models: `haiku`, `sonnet` (exact versions pinned in the run log)
- groups: `design`, `implement`
- 4 cells, `samples_per_cell: 100`, 1,200 runs total

Per group, a pool of 25 frozen briefs; each brief runs 4 times in
randomized order with fresh sessions (100 runs per cell). Models run at
fixed versions and decoding settings. Brief pools are fixed before
sampling and published with the results. The pool is not the deployment
distribution; claims are scoped to it.

Evidence mode is `fresh`: candidates and briefs were fixed before
certification data were observed. Tier is `op` (no deficiency procedure
exists yet, so DS is not claimed). No tail budget is configured in this
first study; tail certification is explicit follow-up work.

## Requirements and loss

Violation predicates, scored per run (0/1):

- `omission`: the delivered artifact omits a requirement stated in the brief.
- `task`: one or more hidden acceptance checks for the brief fail.
- `proc`: `process_audit.py` reports a step-order violation on the transcript.
- `fidelity`: the report claims a check that the transcript shows was never executed, or names an invented interface, path, or version.

Loss is metered run cost in `usd_cents`, capped at `loss_max: 500` (the
harness kills the run at budget and records the cap). Unit:
`usd_cents`. Terminal fallback/abstention costs enter through the same
samples; no separate accounting.

## Statistical parameters

`delta: 0.05`. Comparisons
$Q = 3 \times 4 \times (4 + 1) = 60$, per-bound $\eta = 0.05/60$,
radius $\gamma(100, \eta) \approx 0.197$. Tolerances:

| Requirement | $\epsilon$ |
|---|---|
| omission | 0.30 |
| task | 0.30 |
| proc | 0.30 |
| fidelity | 0.30 |

These are loose pilot bounds: with zero observed violations the upper
bound is $\approx 0.20$. The study can certify a good form but cannot
resolve fine differences; tightening is follow-up work with larger $n$.

## Collection and scoring protocol

1. Freeze candidate bytes and brief pools; record all digests and model
   versions; fill `study.json` placeholders.
2. Collect all 1,200 runs serially or in parallel; restarts reuse only
   completed attempts with byte-identical artifacts (the
   `sufficiency_lab --resume` rule). Execution errors are retried, never
   scored.
3. Score blind: the judge sees transcripts with candidate labels
   removed. Hidden checks are fixed with the brief pools, before runs.
4. Run `skillwren select` exactly once on the filled study. No interim
   outcome looks; budget monitoring may inspect execution errors only,
   never scores.
5. Publish the filled study, the report, and the per-run records.

## Decision rules (preregistered)

- `concise` certified (alone or with others): adopt the inline-logic
  form as default, keeping `full` as the fallback-ranked safe
  alternative for regimes outside this study's scope.
- Only `full` certified: no change; the new form is not adopted.
- Nothing certified (`abstain`): no deployment change. May rerun with
  larger $n$ or revised tolerances only as a new preregistered study.

## Cost and abort criteria

Estimate: 1,200 runs, roughly $40–150 at current haiku/sonnet pricing
(400 haiku-heavy design/implement runs dominate). Abort and publish as
incomplete if spend exceeds $200 or provider capacity blocks completion;
partial data are archived, never certified.
