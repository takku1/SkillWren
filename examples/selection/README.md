# Empirical selection example

From the repository root:

```powershell
py -3 scripts/skillwren.py select examples/selection/study.json
```

This synthetic example has five planned observations per candidate. It
returns **exit 1**, `status: no_certified_candidate`, and `action: abstain`:
five successes cannot establish a 5% risk bound at the configured joint
confidence. One candidate also has an execution error; its cell receives
no statistical bounds. The observations are illustrative, not measured
model results. Candidate hashes identify the committed concise and
contrastive form files; the selector does not independently load or verify
those artifacts.

## Schema 1

The example is a complete input. Unknown fields and duplicate JSON keys
are rejected rather than silently ignored.

| Field | Meaning |
|---|---|
| `schema_version` | Integer 1 |
| `study_id` | Nonempty identifier for the predeclared certification study |
| `assumptions` | All three booleans must be true: `fixed_candidates`, `fixed_sample_size`, `iid_within_cell` |
| `delta` | Joint confidence failure budget, strictly between 0 and 1 |
| `loss_max` | Known finite positive upper bound for trajectory loss, fixed before sampling |
| `loss_unit` | Nonempty name for the common scale of trajectory loss and tail budget |
| `samples_per_cell` | Fixed positive number of observations per candidate/cell |
| `requirements` | Nonempty map of measured violation types to tolerances in [0,1] |
| `cells` | Named objects with `model` and `group`; must form the complete declared Cartesian product |
| `candidates` | Map of fixed candidate IDs to artifact hash, optional structure and cell samples |
| `tail` | Optional object: `nu` strictly between 0 and 1 and `budget` between 0 and `loss_max` |

Requirement types: `safety`, `omission`, `task`, `proc`, `sem`, `anchor`,
`fidelity`. Only configured types are certified. Define their host-scored
violation predicates before collecting data; these labels do not supply
semantic evaluators by themselves.

Each candidate has a lowercase 64-character `artifact_sha256`, a
`structure` list, and a `samples` object keyed by cell ID. Missing or null
`structure` makes the candidate uncertified. An empty or malformed list
is an input error. Each structural step names allowed, required and
retained privileges plus required dependencies, retained nodes and
already-resolved dependencies. Scope privileges to actual resources and
conditions. Supply a manifest that holds across all declared cells and
execution steps; the selector cannot verify completeness of that claim.

Each observation has a unique `id` within its candidate/cell. A
`completed` observation supplies a finite bounded `loss` and a
`violations` object with exactly one boolean for every configured type.
An `execution_error` supplies a nonempty `reason` instead of metrics.
Missing observations are permitted but cannot establish certification;
extra observations, undeclared cells, and duplicate IDs are input errors.
Tool denials or bad reports in an otherwise completed agent execution are
behavioral outcomes, not automatically infrastructure errors.

## Interpreting output

- Exit 0: `selected` names the candidate minimizing the maximum cell loss
  upper bound among those passing all configured tests. Ties use candidate
  ID order. `action: recommend` has no execution or permission effects.
- Exit 1: no candidate is certified; `action: abstain`. Per-candidate
  reasons distinguish incomplete observations, missing structure, failed
  structural inclusions and upper bounds exceeding limits. This does not
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
