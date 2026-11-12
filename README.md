# SkillWren — checked procedures for agent skills (v0.6)

Agent skills are prose, and agents skip steps in prose. SkillWren writes a
skill's control flow (branches, gates, who decides, what is touched, how
failures recover, and what must happen before what) in a small closed
vocabulary that a static checker reads. Natural language describes meaning;
formal structure describes control.

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
  `measure`, `build`, `conform`). The validator is the
  `skillwren.validator` package: `syntax`, `document`, `schema`,
  `flowgraph`, `ordering`, `analysis`, `files`, `explain`.
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

- **Static:** 172 tests; 31 one-break mutants, all killed by their expected
  rule. The 0.6 refactor was checked by comparing every diagnostic on every
  fixture, example, and mutant before and after.
- **Field:** full-stack field report 3 found an assurance step skipped in
  two of two live builds. In full-stack's flows the step runs inside a
  design flow that the build flow calls only when no design is supplied; an
  `order:` rule flags that path (fixture `build-gap.md`). Checking
  full-stack's real flows found one more possible defect (an
  `integration` binding missing on some paths).
- **Behavior: unmeasured.** Two pilot rounds found 8/8 seeded issues with
  both prose and logic skills while loading 5-8x fewer bytes, but content
  changed too. Full-stack's FS-009 found a 312-token prose brief beat its
  full SkillWren-format skill on small tasks. Published procedure-following
  benchmarks report 27-50% compliance, and runtime ordering enforcement
  raising it sharply, which points to enforcement as the next step.

Read the [November review](docs/current/research/research-review-2026-11.md)
and [October review](docs/current/research/research-review-2026-10.md) for
the reasoning and limits, and [language direction](docs/current/language-design.md)
for the three separate claims (static validity, reviewed preservation,
observed behavior).

## Status

v0.6.0 (2026-11-12). See [docs/STATUS.md](docs/STATUS.md). Format 0.6 adds
fragments (`check --fragment`), cross-file `run <flow> from <file>`, contract
`inputs:` (fragments) and `order:` rules (P1), warnings W13-W14, and defined
`exec` command semantics. 0.5 files keep validating. Next: compile order
rules into runtime enforcement, then a controlled comparison with content
held constant (SPEC Section 17).

## License

MIT — see `LICENSE`.

## Runtime evidence (unreleased)

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
command meaningfully proves the named step.

The ledger checks recorded steps after execution; it does not block actions
or detect omitted events. Rules are captured at start. Hash chaining detects
edits within the retained chain, but cannot detect a fully rewritten chain
or truncation of its tail without an independently retained checkpoint.
