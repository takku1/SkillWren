# Full-stack backfill: SkillWren format, validator, and doc changes

Status: BF-1 to BF-8 built 2026-10-05 as SkillWren 0.5.0 (BF-7 and BF-8
authorized the same day). Deviation: BF-7 dropped the separate `exec`
access value; `effects.executes` alone declares what a skill runs.
Records: SPEC §19 v0.5 and Unreleased, CHANGELOG. Produced with the
full-stack skill (package 0.3.0) in design-only mode. Format 0.5 was
authorized by the owner at the costly-commitment gate.

## Scope

**Outcome.** SkillWren absorbs the format-level lessons from full-stack,
the first real skill built and maintained in it, so the next author does
not rediscover them. Six work packages, BF-1 to BF-6 below.

**Evidence** (all in the full-stack repo, `Z:\full-stack`):

| Source | What it shows |
|---|---|
| `evals/trials/logic-conversion/pilot-report.md` | Conversion, D1-D5 dogfood findings, per-route cost |
| `docs/research/field-report-2026-10-03-mochios.md` | First live run; already backfilled here in commit `38a2da8` |
| `docs/research/field-report-2026-10-03-mochios-2.md` | Second live run: registry identity, subject precedence, shared run resources |
| `docs/research/review-2026-10-05-fresh-user.md` | Independent review, verdict NOT-YET; findings 2, 3, 11 are format-level |
| `docs/design-decisions.md` D-013 to D-015 | What full-stack changed and why |
| Session observation, 2026-10-05 | Claude Code listed full-stack's description as "Full Stack" (its H1) after an unquoted `Enum[...]` entered the header, and listed the real description again once it was quoted |

Probes run against the current validator (scratch copies of
`docs/skill-template.md`, 2026-10-05):

- An `if X:` arm and an `unless X:` arm that both bind `output` still fail U1
  at every later use. The format has no way to say "exactly one of these ran".
- `budget: { header: 900, body: 9000 }` validates clean, although §10 says
  "header at most 400 tokens, body at most 2500".
- `mode: { type: Enum[fast, full] }` validates clean but is rejected by
  PyYAML (`expected ',' or '}', but got '['`). §5's own example has the
  same shape.
- Baseline: `pytest -q` gives 72 passed, 50 subtests.

**Dispositions.**

- Required now: BF-1 to BF-6.
- Existing dependencies: the indentation AST and CFG in `validator.py`
  (definite binding, M1), the mutation catalog and tripwire, and the §19
  amendment log as the change record.
- Deferred enhancements, not in this design:
  - Nesting SkillWren fields under an Agent Skills `metadata:` map. This
    needs evidence that a host loader (not only Codex's skill-creator
    `quick_validate.py`) rejects unknown top-level keys.
  - Optional resources (already in §17).
  - The EBNF grammar.
  - Real cl100k counting.

**Exclusions.**

- No runtime or interpreter.
- No change to routing scoring.
- No edits to full-stack from this design. Full-stack adopts 0.5 later
  as its own work.
- The untracked `.agents/skill-drafts/` folder belongs to another session
  and is left untouched.

## Ownership and contracts

| Artifact | Owns | Changed by |
|---|---|---|
| `docs/SPEC.md` | Normative format: profile (§5), language (§6), failure semantics (§12), catalog (§13), compatibility (§16), log (§19) | BF-1 to BF-6 |
| `src/skillwren/validator.py` | Mechanical checks; must not accept what the SPEC rejects | BF-1, BF-2, BF-5, BF-6 |
| `docs/authoring-guide.md`, `docs/skill-template.md` | Authoring procedure and starting point; must validate clean | BF-3, BF-4, BF-6 |
| `tests/` (fixtures, `mutation_catalog.py`) | Evidence for each rule | Every validator change adds a valid and an invalid fixture |
| `CHANGELOG.md` "Unreleased" and SPEC §19 | Record of changes | Every package |

Contract with skill authors: a file that validates clean under 0.4.x keeps
validating under the 0.5 validator, except for one deliberate fix. BF-1
rejects headers that general YAML parsers cannot read. This is a bug fix,
not a format change: §5 already promises "YAML-compatible".

## Choices

- **BF-1, error or warning for non-YAML headers.** Chose F1 error. When a
  host fails to parse, it silently drops the description, which defeats
  discovery. Revisit if a host is shown to accept the profile directly.
- **BF-2, how budgets work.**
  - Chose: the header ceiling has a hard maximum of 400 (Goal 1 depends on
    it), and declaring more is B1. Body ceilings are declared per skill,
    with W11 when the declaration exceeds 2500.
  - Alternative, enforce 2500 hard: rejected, because full-stack's
    plain-language glossary (D-015) needs about 3100.
  - This is a reversible default.
- **BF-6, `else:` versus recognizing complementary `if`/`unless`.** Chose
  `else:`. Matching conditions on text is fragile, and an explicit arm
  makes definite binding easy to check.
- **BF-6, the new access value.** Chose an additive `read+write`, which
  says what `effects.mutates` means. Existing `read+create` stays valid
  with its current meaning. Spelling it `mutate` was rejected because it
  mixes the verb and noun vocabularies.
- **BF-6, header relief.** `purpose` becomes optional and defaults to
  `description`; the spec example and full-stack carry both, nearly
  identical. An optional `release` field carries the package version, so
  `version` stays the format version.

## Increments

**BF-1: headers must parse as YAML (fix).**

- Requirement: the validator rejects any header value a YAML 1.2 parser
  would reject. Specifically, an unquoted value inside an inline map
  containing `[`, `]`, `{`, `}` or `,` is an F1 error, with the fix "quote
  the value".
- §5:
  - Quote the example: `{ type: "Enum[low, medium, high]" }`.
  - State that quoted type strings are parsed by the type grammar.
- Checks: a new invalid fixture with an unquoted Enum fails F1, and the
  quoted fixture is clean. Optional, and skipped when PyYAML is absent:
  a test that `yaml.safe_load` accepts every clean fixture's header.
- Closure evidence: the full-stack header validates and parses under
  PyYAML.
- Status: ready.

**BF-2: budget ceilings mean what §10 says.**

- Requirement:
  - A declared `budget.header` above 400 is B1.
  - A declared `budget.body` above 2500 is the new warning W11, with the
    message "body ceiling above the 2500 default".
  - §10 and the pre-submit checklist say the same.
- Checks: fixtures for header 401 (B1) and body 3200 (W11 only).
- Status: ready.

**BF-3: decline versus dismissal (docs plus template).**

- Requirement: §12 defines three outcomes for a decision `ask`:
  - Confirmed: the confirmation holds.
  - Declined: the user answers no, and the `otherwise:` repair runs.
  - Dismissed: no answer or cancel. The flow stops with zero mutation and
    the repair does not run.
- The template's repair message becomes "Declined; nothing changed."
- New guide mistake 22: a decline that should keep independent work must
  repair (mark and continue), not abort.
- Non-interactive hosts (for example `claude -p`): an `ask` that cannot
  reach a user counts as dismissed. Evidence: the full-stack A/B harness
  records attempted questions that a headless session could not answer.
- Evidence: full-stack D1 and fresh-user finding 1.
- Checks: the template validates clean and the M1 tripwire is unchanged.
- Status: ready.

**BF-4: host compatibility and live-use patterns (docs).**

- §1 Goal 1 and §9: today's hosts (Claude Code, Codex) route on `name` and
  `description` only. Headers-only routing is a SkillWren convention for
  future tooling, not current host behavior. This matches how Goal 2 was
  qualified in `38a2da8`.
- §16 gets a table of the fields hosts read versus SkillWren declarations
  hosts ignore. Write `description` as the routing text.
- Guide additions:
  - A **step-meanings glossary** pattern, as in full-stack's appendix: one
    line per `apply` spec. This is the concrete form of mistake 21.
  - A subject-precedence `always` line for skills that write into other
    repositories: "follow subject instructions over this package's
    defaults".
  - The multi-agent `always` recipe extended to shared build and run
    resources (wait, never kill), and to parallel workers: disjoint write
    sets per work package, one owner per shared file (manifest, lockfile,
    registry, generated code). §8 notes that a runtime guard can cover the
    multi-actor case the static validator excludes (full-stack D-016).
  - A resource path that names a fallback chain, as interim practice until
    optional resources land.
- Evidence: fresh-user findings 3 and 11, and field report 2 items G1, G2
  and G4.
- Status: ready.

**BF-5: make mistake 21 checkable.**

- Requirement: new warning W12. An `apply <spec>` whose spec words share
  fewer than two content words with any appendix line warns
  "apply spec has no appendix anchor". It uses the same overlap heuristic
  as W2 and W3.
- Checks:
  - A fixture with an unanchored `apply` gets W12.
  - The full-stack SKILL.md gets no W12, since its glossary anchors every
    spec.
  - The golden examples are checked and any W12 is fixed or justified.
- Status: ready.

**BF-6: format 0.5 (authorized 2026-10-05).**

- Requirement:
  - **`else:`** may follow an `if`, `unless` or `when` block at the same
    indentation. Exactly one arm runs, and a name bound in both arms is
    definitely bound after the join (U1).
  - **`access: read+write`** joins the canonical values. A resource
    written by any flow and declared under `effects.mutates` should use it
    (warning-grade hint, not an error).
  - **`purpose`** becomes optional and defaults to `description`.
    **`release`** becomes an optional package-version string; it is not
    compared as a format version.
  - **`version`:** `0.5` validates under the new validator, and 0.4.x
    files still validate.
- Docs:
  - §6 adds `else` to the structure words (6). §5 and §8 get the field
    and access changes.
  - The guide's verb reference and template are updated.
  - §19 gets a v0.5 entry.
- Checks:
  - Fixtures: an if/else bound in both arms is clean; bound in one arm
    fails U1; an `else` with no preceding branch fails O1.
  - `read+write` is accepted; no `purpose` is clean; `release: 0.3.0` is
    clean.
  - New mutants in `mutation_catalog.py` (an else-arm binding removed, an
    else after a non-branch).
  - The tripwire passes, and every 0.4.x fixture result is unchanged.
- Order: BF-1 first, because BF-6 touches the same header parser.
- Status: ready.

**BF-7: running commands is a first-class effect (conditional: not yet
authorized).**

- Problem: the vocabulary has no way to run a command, and `effects` has
  no `executes`. Yet running tests and scripts is the most common real
  effect of a build skill. Full-stack 0.3.0 had to model "run the guard
  script" and "run the acceptance checks" as `write claim with run_log`
  and `write checks with run_log`, which is structurally valid but
  misdescribes what happens.
- Requirement:
  - New action `exec <command description> as <binding>`.
  - New effects group `executes: [...]`, covered like reads and writes
    (E1 and E2).
  - New resource access value `exec` for bundled scripts, so `scripts/*`
    can be declared like `references/*`.
  - `verify <condition> from <binding>`, so a gate names its evidence
    source, typically an `exec` result. Then "verify checks pass" is tied
    to an executed check rather than to the model's recollection.
- Format impact: extends 0.5 with one verb (12 to 13 actions), one effects
  group, one access value, and one `verify` form. The owner authorized
  0.5 for BF-6's surface; this is new surface, so it needs a separate
  decision.
- Checks:
  - Fixtures: undeclared `exec` (E2); `exec` on a resource without `exec`
    access (E1); `verify ... from` an unbound name (U1).
  - Mutants: drop an `executes` entry; drop the `from` binding.
  - Full-stack's implement flow rewritten with `exec` validates clean.

**BF-8: runtime conformance for the release criteria (conditional: not
yet authorized).**

- Problem: §1's release criteria ("zero undeclared mutations in eval
  scenarios; every required gate fires; user dismissals never mutate")
  are runtime properties. §14 names a precision suite, but nothing runs
  one; the validator proves structure only. Full-stack now has both
  missing pieces: a git-based guard (`scripts/run_guard.py`) and an
  isolated headless A/B harness (`evals/ab/run_ab.py`).
- Requirement:
  - Resources gain an optional `glob:` property: a machine-readable path
    pattern next to the natural-language `path`. This changes §8's closed
    resource schema.
  - A `skillwren conform` command runs a skill headless in a throwaway
    git workspace, then reports any changed file not covered by a
    `glob:` of a resource under `creates` or `mutates`. Those are
    undeclared mutations.
  - An `ask` that fires headless counts as dismissed (BF-3); the run must
    then show zero changes.
- Reuse: port, don't copy, the full-stack harness's isolation (empty
  `CLAUDE_CONFIG_DIR`, login copied to a temp dir, a budget cap per
  session).
- Checks: a fixture skill that writes an undeclared file is caught; the
  golden examples run clean; one dismissal scenario shows zero changes.
- Cost: spends model usage on every conformance run. Gate it behind an
  explicit flag and never run it in CI by default.

**Order.** BF-1, then BF-2 (same validator area). BF-3 and BF-4 are docs
and can go in parallel. BF-5 follows BF-4, so the glossary pattern is
documented before it is enforced. BF-6 comes last.

## Blockers

None for BF-1 to BF-6. BF-7 and BF-8 wait on the owner's decision. The deferred `metadata:` nesting is blocked on
evidence about host loaders, as listed under dispositions.
