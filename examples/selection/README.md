# Empirical selection example

From the repository root:

```powershell
py -3 scripts/skillwren.py select examples/selection/study.json
```

This synthetic example has five planned observations per candidate. It
returns **exit 1**, `status: no_admissible_candidate`, and `action: abstain`:
five successes cannot establish a 5% risk bound at the configured joint
confidence. One candidate also has an execution error; its cell receives
no statistical bounds. The observations are illustrative, not measured
model results. Candidate hashes identify the committed concise and
contrastive form files; the selector does not independently load or verify
those artifacts.

## Schema 2

The example is a complete input. Unknown fields and duplicate JSON keys
are rejected rather than silently ignored.

| Field | Meaning |
|---|---|
| `schema_version` | Integer 2 |
| `study_id` | Nonempty identifier for the predeclared admissibility study |
| `regime` | Deployment regime: `task_family`, `context_band`, `language`, `risk_tier`, all nonempty strings |
| `tier` | `op` (structure + risk + tail) or `ds` (additionally an evaluator-attested deficiency bound) |
| `assumptions` | All three booleans must be true: `fixed_candidates`, `fixed_sample_size`, `iid_within_cell` |
| `delta` | Joint confidence failure budget, strictly between 0 and 1 |
| `loss_max` | Known finite positive upper bound for trajectory loss, fixed before sampling |
| `loss_unit` | Nonempty name for the common scale of trajectory loss and tail budget |
| `samples_per_cell` | Fixed positive number of observations per candidate/cell |
| `requirements` | Nonempty map of measured violation types to tolerances in [0,1] |
| `cells` | Named objects with `model` and `group`; must form the complete declared Cartesian product |
| `candidates` | Map of fixed candidate IDs to artifact hash, required `fallback_rank` (positive, unique), required `inv_verified` attestation (missing/False leaves the candidate inadmissible), optional `cfg_sha256` config provenance, optional structure, optional `deficiency` attestation, and cell samples |
| `refusal` | Optional verified refusal-only router (`router_id`, `artifact_sha256`, `inv_verified: true`, `refusal_only: true`, `terminal_cost`): selected with action `refuse` when nothing is admissible; never a risk-budget claim |
| `evidence` | Optional reuse-mode declaration (default `fresh`): `split` needs `partition_recorded: true`; `adaptive` needs an `adaptive_coverage` procedure + certificate digest; anything else denies the study |
| `cell_weights` | Optional map from every cell ID to a nonnegative weight summing to 1 (default uniform): weights the objective mean toward the intended deployment distribution; bounds and multiplicity are unaffected |
| `tail` | Optional object: `nu` strictly between 0 and 1 and `budget` between 0 and `loss_max` |

Requirement types: `safety`, `omission`, `task`, `proc`, `sem`, `anchor`,
`fidelity`. Only configured types are bounded. Define their host-scored
violation predicates before collecting data; these labels do not supply
semantic evaluators by themselves.

Each candidate has a lowercase 64-character `artifact_sha256`, a
`structure` list, and a `samples` object keyed by cell ID. Missing or null
`structure` makes the candidate inadmissible. An empty or malformed list
is an input error. Each structural step names allowed, required and
retained privileges plus required dependencies, retained nodes and
already-resolved dependencies. Scope privileges to actual resources and
conditions. Supply a manifest that holds across all declared cells and
execution steps; the selector cannot verify completeness of that claim.

Each observation has a unique `id` within its candidate/cell. A
`completed` observation supplies a finite bounded `loss` and a
`violations` object with exactly one boolean for every configured type.
An `execution_error` supplies a nonempty `reason` instead of metrics.
Missing observations are permitted but cannot establish admissibility;
extra observations, undeclared cells, and duplicate IDs are input errors.
Tool denials or bad reports in an otherwise completed agent execution are
behavioral outcomes, not automatically infrastructure errors.

## Interpreting output

- Exit 0: `selected` names the candidate minimizing the mean
  trajectory-loss estimate across cells among those passing all configured
  tests (worst-cell upper loss is still reported for audit, and all safety
  stays in the per-cell bounds, not the objective). Ties prefer the lower
  `fallback_rank`, then candidate ID order. `action: recommend` has no
  execution or permission effects.
- `deployment_order` lists admissible candidates in fallback-preference
  order for a deployment-side router; each carries a `certificate` with
  its scope, bounds, thresholds, and `fallback_next` link (`abstain` for
  the last). Under tier `ds` each candidate needs a `deficiency`
  attestation (`upper` at or under `threshold`); the selector checks the
  evaluator's bound, it does not prove it.
- Exit 1: no candidate is admissible and no verified refusal is configured;
  `action: abstain`. Per-candidate reasons distinguish incomplete
  observations, missing structure, failed structural inclusions, missing
  invariant verification, and upper bounds exceeding limits. This does not
  prove population infeasibility.
- Exit 2: invalid input or unreadable file; diagnostic on stderr, no JSON
  recommendation on stdout.

The report includes the input SHA-256, full confidence allocation, bounds,
thresholds and scope. It is written only to stdout; redirect it to a new
report file if needed. Input assertions are not independently verified.
There is no configurable automatic safe baseline: an operational baseline
needs separate certification and host authority.

The formulas and their assumptions are in
[FORMULATION.md](../../docs/current/research/semantic-sufficiency/FORMULATION.md).
Five-repetition success counts from the historical sufficiency study must
not be relabeled as certification under this new design. Do not choose
thresholds after looking at those results.
