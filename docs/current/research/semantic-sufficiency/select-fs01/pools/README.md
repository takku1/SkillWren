# FS-01 brief pools

Evaluation material for the FS-01 full-stack representation study.
Authored offline. No model calls were used to write these briefs, and
**no candidate outputs have been generated**: success is frozen here
before any candidate is observed.

## Layout

- `briefs/design.json`, `briefs/implement.json` — the model-visible
  input only: `{id, group, difficulty, dimensions, title, brief,
  attachments[]}`. Attachments (`{name, content}`) are part of the
  input (dependency notes, policy excerpts, specs).
- `checks/design.json`, `checks/implement.json` — hidden acceptance
  checks, never revealed to models: `{brief_id, checks[]}` with
  `{id, kind, dimension, target?, expect?, graded_by, rubric?}`.
  Kinds: `contains`, `not_contains`, `file_exists`, `exit_zero`,
  `json_field`, `judge_rubric` (blinded human/model judge with rubric,
  used only where no deterministic predicate decides).
- `SPLIT.json` — frozen dev/holdout assignment plus sha256 of every
  pool file. Dev briefs exist for harness debugging only and never
  enter certification evidence.
- `COVERAGE.md` — group × difficulty × dimension matrix (generated).
- `DEDUP.md` — dedup method and adjudications.

## Authoring rules (enforced by review, not by construction)

- Briefs are written from first principles about security, privacy,
  authorization, error handling, dependency ordering, and workflow
  fidelity. They are never reverse-engineered from a candidate
  representation's output.
- Adversarial briefs target **decision-sensitive information**: an
  authorization exception buried in a dependency, a privacy constraint
  that flips an otherwise valid design, a seemingly optional step that
  is actually mandatory. Obscurity alone is not a trap.
- Full-context baseline can fail: several briefs are hard even with
  complete information, and some correct answers are refusals or
  pushback (missing authority, ambiguous scope). Falsification runs
  both ways.
- No difficulty quotas: the mix is recorded, not forced. Cell structure
  (model × group) and deployment weighting are fixed by the
  preregistration, not by the pool composition.

## Harness contract

Reveal per run only `{id, group, title, brief, attachments}`. Never
load `checks/` or `SPLIT.json` into model context. Score with the
preregistered predicates; deterministic kinds by script, `judge_rubric`
kinds blinded with candidate identity removed. Deterministic string
checks are tripwires, not oracles: a passing design that phrases a
requirement differently must not fail on wording alone. The scoring
protocol (a later deliverable) defines the violation mapping; where a
script check and the blinded judge disagree on the same dimension, the
judge governs and the disagreement is logged.
