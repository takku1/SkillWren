# SkillWren — checked procedures for agent skills (v0.7)

Agent skills are prose, and agents skip steps in prose. SkillWren writes a
skill's control flow (branches, gates, who decides, what is touched, how
failures recover, and what must happen before what) in a small closed
vocabulary that a static checker reads — and its runtime controller can
then enforce. Natural language describes meaning; formal structure
describes control; the guard denies what the structure forbids.

Two halves: the **checker** validates the written procedure (it does not
make a model follow it), and the **guard** is a trusted-host controller
that binds each protected write to an administrator policy, a pinned
verifier program, the exact approved bytes, and an unchanged target.
Approvals are single-use and die with the process; every request is
appended to an audit log held against an independent checkpoint.

Two ways to use it:

- **Flow files (fragments).** Keep `SKILL.md` to `name` and `description`
  plus a short core, and put `logic` blocks in on-demand Markdown flow
  files. Check them with `skillwren check --fragment`. This is how
  [full-stack](docs/current/research/research-review-2026-11.md), the
  format's one long-term user, is built.
- **Complete skills.** One file with a contract header (inputs, outputs,
  authority, effects, budgets) and logic body, checked with
  `skillwren check`. Hosts read only `name` and `description`, so the header
  serves tooling, not routing.

The checker validates the written procedure. It does not make a model follow
it; see [Evidence](#evidence).

## Layout

- `src/skillwren/` — stdlib-only package and `skillwren` CLI (`check`,
  `measure`, `build`, `conform`, `guard`, `sandbox`, `audit`, `ledger`).
  The validator is the `skillwren.validator` package: `syntax`,
  `document`, `schema`, `flowgraph`, `ordering`, `analysis`, `files`,
  `explain`. `guard` is the trusted-host controller, `sandbox` the
  isolated effect observer, `audit` the checkpointed event log, and
  `ledger` the offline run checker.
- `docs/STATUS.md` — current state. `docs/current/` — `SPEC.md` (normative),
  `authoring-guide.md`, `skill-template.md`, `fragment-template.md`,
  `compiler.md`, `language-design.md`, `design/`, `research/`.
  `docs/archive/` — finished designs.
- `examples/` — `theme-factory.golden.md`, `code-reviewer.md`,
  `optimization/` (reviewed conversion), `context-build/`.
- `tests/` — validator, fragment, compiler, conform, and input suites;
  fixtures (including `fixtures/fragments/skill/`, a small flow-file skill);
  the mutation tripwire over `mutation_catalog.py` (31 one-break mutants on
  four bases) and the `mutation_sweep.py` kill-matrix runner.
- `benchmarks/` — two pilot rounds (summaries plus frozen `archive/`).
- `skills/skillwren/SKILL.md` — reusable procedure for converting and
  checking a skill.

## Quickstart

Install (checking and plain builds use the standard library; exact token
metrics are optional):

```sh
pip install -e '.[tokens]'
```

Without installing, use `PYTHONPATH=src` and your interpreter: `python3`,
`python`, or on Windows `py -3` (`python` can be a Microsoft Store stub).

Check flow files, with each flow's inferred inputs, writes, and runs:

```sh
skillwren check --fragment --summary skill/flows/*.md
```

State an ordering in a flow file's contract block, and the checker follows
every path, including paths through `run <flow> from <file>`:

```text
order:
  apply assurance screen before write implementation
```

Check a complete skill (exit 0 clean, 1 on errors; `--explain` adds a
plain-language paragraph per diagnostic):

```sh
skillwren check path/to/SKILL.md
```

Measure and build a reviewed conversion:

```sh
skillwren measure examples/optimization/original.md examples/optimization/SKILL.md
skillwren build examples/optimization/SKILL.md --out built-skill \
  --original examples/optimization/original.md \
  --review examples/optimization/review.json
```

An optimized build requires a strictly smaller expanded prompt and a
complete, hash-bound review map. The map checks review bookkeeping, not
semantic parity. See the [compiler guide](docs/current/compiler.md) and the
[conversion skill](skills/skillwren/SKILL.md).

Run a skill once headless and compare what it changed and ran with what it
declared (needs the Claude Code CLI; spends model usage):

```sh
skillwren conform path/to/SKILL.md --prompt "..." --model claude-sonnet-5-5 \
  --budget-usd 0.3 --workspace path/to/sample --auth-from-profile \
  --record runs/
```

`conform` reports changed files outside the resources' `glob:` patterns,
asks followed by changes, and shell commands run without a declared
`effects.executes`. `--record` appends one JSON line per run, failures
included. It observes final state; it is not a sandbox (SPEC Section 14).

Run the offline suite:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Evidence

- **Static:** 231 tests; 31 one-break mutants, all killed by their expected
  rule. The 0.6 refactor was checked by comparing every diagnostic on every
  fixture, example, and mutant before and after.
- **Enforcement (scripted):** 90 paired A/B/C trials
  (`docs/current/research/runtime-ab-comparison.jsonl`, summary in
  `runtime-ab-summary.json`). Unguarded arms complete every task but write
  without authorization; the guarded arm makes 0 unauthorized writes with 0
  false blocks. These trials test enforcement mechanics, not whether
  structured prompts improve model behavior.
- **Deployment:** `tests/test_deployment.py` puts an adversarial agent in a
  digest-pinned container with no protected, policy, or audit mounts while
  the guard runs on the host. Direct access is unavailable; only
  verify-then-write through the request protocol mutates the target.
- **Field:** full-stack field report 3 found an assurance step skipped in
  two of two live builds. In full-stack's flows the step runs inside a
  design flow that the build flow calls only when no design is supplied; an
  `order:` rule flags that path (fixture `build-gap.md`). Checking
  full-stack's real flows found one more possible defect (an
  `integration` binding missing on some paths).
- **Behavior vs prose: unmeasured at model level.** Two pilot rounds found
  8/8 seeded issues with both prose and logic skills while loading 5-8x
  fewer bytes, but content changed too. Full-stack's FS-009 found a
  312-token prose brief beat its full SkillWren-format skill on small
  tasks. Model A/B/C arms are pending a provider and usage budget; see
  [model evaluation plan](docs/current/research/model-evaluation-plan.md).
  The scripted A/B gap measures enforcement, not syntax.

Read the [November review](docs/current/research/research-review-2026-11.md)
and [October review](docs/current/research/research-review-2026-10.md) for
the reasoning and limits, and [language direction](docs/current/language-design.md)
for the three separate claims (static validity, reviewed preservation,
observed behavior).

## Status

v0.8.0 (2026-11-12). See [docs/STATUS.md](docs/STATUS.md) and
[CHANGELOG.md](CHANGELOG.md). 0.8 adds the authoring pipeline
(`draft`, `explain-workflow`, `approve`), the NL fidelity corpus, and
ledger `cwd`/`readonly`/`detail`/`attempt` support. 0.7 added the
runtime controller (`guard`), the isolated observer (`sandbox`), the
checkpointed audit log (`audit`), and ledger completeness contracts.
0.5 files keep validating. Next: the model A/B/C comparison with content
held constant ([plan](docs/current/research/model-evaluation-plan.md)).

## Authoring pipeline: intent to approved workflow

Draft a proposal from natural language, validate it, read what it
means, approve the exact bytes, then enforce the covered operations:

```text
skillwren draft --intent-file intent.md --adapter '["python", "adapter.py"]' --out proposal.md
skillwren check --fragment proposal.md
skillwren explain-workflow --fragment proposal.md
skillwren approve --fragment proposal.md --by you --policy policy.json
skillwren approve --check proposal.md
```

The drafter only proposes: assumptions and unresolved questions are
part of its output, and nothing is approved without a human. Approval
records the file digest and which enforceable operations the guard
policy covers; any edit invalidates it. The
[NL fidelity corpus](docs/current/research/nl-fidelity/) holds 26
hand-authored intent-to-flow pairs whose key facts the explainer must
state, so reviewers can judge meaning without reading the logic.

## Guarded write end to end

Install, protect one file, attempt a raw write, verify the candidate,
write it, and check the audit trail (PowerShell shown; `python3` on
Linux/macOS):

```powershell
pip install .
mkdir protected, independent
py -3 scripts/guard_policy.py --target $PWD\protected\config.json --out policy.json
'{"action":"write","operation":"write#config","content":"{\"debug\": false}"}',
'{"action":"verify","operation":"write#config","content":"{\"debug\": false}"}',
'{"action":"write","operation":"write#config","content":"{\"debug\": false}"}' |
  py -3 scripts/skillwren.py guard policy.json --audit events.jsonl --checkpoint independent\anchor.json
Get-Content protected\config.json
py -3 scripts/skillwren.py audit events.jsonl independent\anchor.json
```

The first request without a prior `verify` is denied; after verification
the write lands and the audit reports a closed session with an intact
chain. Policy, verifier, protected output, and checkpoint must all live
outside the agent's reach — see the
[runtime walkthrough](docs/current/quickstart-runtime.md).

## License

MIT — see `LICENSE`.

## Runtime ledger (offline)

`check --fragment --audit flow.md` reports evidence classes and branch
controllers. W15 warns when an ordering prerequisite rests on a self-report.
The research rationale is in
[game theory and evidence](docs/current/research/game-theory-2026-11.md).

Record an observed run with the ledger:

```text
skillwren ledger start flow.md
skillwren ledger exec latest --step "verify design has an assurance table" -- py -3 verify_design.py
skillwren ledger note latest --step "write implementation" --artifact implementation.py
skillwren ledger check latest --require-evidence
skillwren ledger show latest
```

Use the run ID printed by `start` when multiple runs share a directory.
`exec` preserves every argument after `--` and returns the child's exit code.
Failed commands do not satisfy prerequisites. Bare notes are self-reports;
artifact notes record file hashes. Strict checking rejects prerequisites
supported only by self-reports, but does not establish that an artifact or
command meaningfully proves the named step. A run with no required
milestones is reported as `unassessed`, never as complete; pass explicit
`--require` names at `start` and `check --require-completeness` to make
assurance CI fail the unassessed case.

The ledger checks recorded steps after execution; it does not block actions
or detect omitted events. Rules are captured at start. Hash chaining detects
edits within the retained chain, but cannot detect a fully rewritten chain
or truncation of its tail without an independently retained checkpoint.

## Codex

This checkout includes a Codex skill at `.agents/skills/skillwren/SKILL.md`.
Start a new Codex session in this repository and ask:
`Use $skillwren to check tests/fixtures/fragments/skill/flows/build-fixed.md`.
The skill uses the same checker and ledger as other hosts. See the
[official skill documentation](https://learn.chatgpt.com/docs/build-skills).

No installation or API key is needed for static checking or ledger commands:

```powershell
py -3 scripts/skillwren.py check --fragment --summary --audit tests/fixtures/fragments/skill/flows/build-fixed.md
```

On macOS/Linux use `python3 scripts/skillwren.py` with the same arguments.
From another project, use the absolute path to this checkout's launcher;
input paths and ledger output remain relative to your current directory.
For conversion, the Codex skill links to the canonical conversion procedure
and repository documentation. Keep this checkout available; copying only
its skill folder into another project will break those relative references.

`check`, `measure`, `build`, and `ledger` are host-independent. `conform`
currently launches Claude Code and does **not** evaluate Codex runs. The
ledger can record commands Codex executes, but is not a Codex hook and does
not enforce actions or prove model adherence.

### Ledger completion scope

At start, repeat `--require "exact milestone name"` to commit required
milestones. The report separates `ordering_valid`, `evidence_valid`, and
`execution_complete`. Without declared milestones, completion is unknown
(`null`) and the outcome is `incomplete`; the legacy `ok` field and exit
status still report the requested ordering/evidence checks. With milestones,
missing successful exact-name events fail the check. Completion describes
recorded milestones only, not independent proof of actual execution.

See the [independent review response](docs/current/design/independent-review-response.md)
for unresolved verifier binding, trusted enforcement and benchmark work.
