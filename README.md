# SkillWren — a static checker for agent-skill procedures

SkillWren writes a skill's control flow (branches, gates, who decides,
what is touched, how failures recover, and what must happen before what)
in a small closed vocabulary, and **checks it statically**: it builds an
AST and control-flow graph per flow and proves properties such as "this
verification completes before that write on every path" or "nothing is
changed before a question the user may dismiss". That is the part with
the clearest demonstrated value: on full-stack's real flows it found a
conditional path that skipped the assurance step and two mutations before
a dismissible ask that prose review had missed.

What it does **not** show yet: that writing a procedure in this syntax
makes a model follow it better than concise prose. Every controlled
comparison so far is a tie at the ceiling (see [Evidence](#evidence)).

The runtime pieces are narrower than "procedure enforcement":

- **Guard:** a trusted-host controller for protected writes. Each write
  needs a pinned verifier's acceptance of the exact bytes and an
  unchanged target; approvals are single-use. Bound to a workflow
  (`skillwren policy`), it also refuses to start unless the host approval
  record matches the flow's exact bytes, and it enforces the flow's typed
  order rules **between guard operations** as write preconditions. It does
  not interpret branches, prose steps, or steps outside its operations;
  those stay static or ledger checks, and `status` lists them.
- **Ledger and audit:** hash-chained records of a run, checked after the
  fact. They depend on cooperative recording and on host isolation.
- **Isolation is the host's job:** a same-account process can bypass the
  guard. The repository tests the container topology; real deployments
  must keep policy, verifiers, targets, approvals and checkpoints out of
  the agent's reach.

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
  `explain-workflow`, `draft`, `approve`, `policy`, `guard`, `ledger`,
  `audit`, `sandbox`, `measure`, `select`, `certgate`, `build`, `conform`).
  The validator is the `skillwren.validator` package: `syntax`,
  `document`, `schema`, `flowgraph`, `ordering`, `analysis`, `files`,
  `explain`. `guard` is the trusted-host controller, `sandbox` the
  isolated effect observer, `audit` the checkpointed event log,
  `ledger` the offline run checker, and `certgate` the deployment gate
  that binds selection certificates to artifact bytes and live context.
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

For fixed-study empirical representation selection, `skillwren select`
checks supplied structural manifests and simultaneous requirement-risk
bounds across model-group cells of one deployment regime, with an optional
CVaR budget and an optional decision-sufficiency tier. It recommends the
cheapest admissible candidate, falls back to a configured verified refusal
router, or abstains; it ranks admissible policies in fallback-preference
order and emits per-candidate certificates for a deployment-side router.
It does not classify live inputs, monitor execution, or prove semantic
equivalence. See the [input
example](examples/selection/README.md) and [working
formulation](docs/current/research/semantic-sufficiency/FORMULATION.md).

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

- **Static:** the offline suite (CI on Linux and Windows, Python 3.9-3.15)
  plus 31 one-break mutants, all killed by their expected rule; the guard
  has its own runtime mutation sweep (`tests/runtime_mutation_sweep.py`).
  The 0.6 refactor was checked by comparing every diagnostic on every
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
- **Real agent:** headless Claude Code loads a packaged skill from a
  one-line request on a disposable clone and leaves an evidence chain the
  host verifies; replay and blocked submissions are denied
  ([host demo](docs/current/research/host-demo/README.md)).
- **Behaviour vs prose: no difference found.** 72 real-agent runs across
  prose, logic, both, and inline forms complied 72/72
  ([skill forms](docs/current/research/skill-forms/README.md)); the model
  A/B/C runtime comparison is a 90/90 tie once the task states its format
  ([evaluation](docs/current/research/model-evaluation-plan.md)); the
  preregistered repair task with a host-hook baseline is in
  [repair-eval](docs/current/research/repair-eval/README.md): 48/48 supported reports in every arm, including a plain Claude Code hook and the guard, because the honest fix was as cheap as the shortcut. Earlier,
  full-stack's FS-009 found a 312-token prose brief beat its full
  SkillWren-format skill on small tasks. The syntax's value shown so far is
  static checking and machine-readable structure, not better model
  behaviour.
- **Drafting:** model drafts lose requirements silently; `draft`/`approve`
  now flag gates without recorded evidence, and drafter prompt 2 cut
  requirement defects from 19 to 7 on corpus v2
  ([results](docs/current/research/nl-fidelity-v2/model-draft/README.md)).
  Corpus reviews so far are by model sessions, not humans.

Read the [November review](docs/current/research/research-review-2026-11.md)
and [October review](docs/current/research/research-review-2026-10.md) for
the reasoning and limits, and [language direction](docs/current/language-design.md)
for the three separate claims (static validity, reviewed preservation,
observed behavior).

## Status

v0.9.0 (2026-11-17). See [docs/STATUS.md](docs/STATUS.md) and
[CHANGELOG.md](CHANGELOG.md). 0.9 shows a real coding agent (headless
Claude Code) loading a packaged skill and leaving a host-checkable
evidence chain ([host demo](docs/current/research/host-demo/README.md)),
adds typed return anchors and declared read-only `exec`, packages
fragment-set skills (`build DIR`, `measure DIR`), and reports the first
model measurements: draft fidelity, an independent corpus review, a
skill-form comparison, and the model A/B/C runtime comparison. 0.8 added
the authoring pipeline (`draft`, `explain-workflow`, `approve`); 0.7 the
runtime controller (`guard`), `sandbox`, `audit`, and ledger contracts.
0.5 files keep validating.

## Authoring pipeline: intent to approved workflow

Draft a proposal from natural language, validate it, read what it
means, approve the exact bytes, then enforce the covered operations:

```text
skillwren draft --intent-file intent.md --out proposal.md -- python adapter.py
skillwren check --fragment proposal.md
skillwren explain-workflow --fragment proposal.md
skillwren approve --fragment proposal.md --by you --policy policy.json
skillwren approve --check proposal.md
```

(The adapter follows `--` as plain words, so no JSON quoting is needed on
any shell; `--adapter` and `--adapter-file` remain. `draft` and `approve`
list `verify` gates that cite no recorded evidence.)

Generate a pinned, workflow-bound guard policy from an approved flow and an
operation map (verifier command and, for writes, the protected target):

```text
skillwren policy flow.md --approvals approvals/ --map ops.json --out policy.json
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

## Deployment gate

`skillwren certgate` binds a `select` report to artifact bytes and the
live deployment context before a trusted host authorizes execution:

```text
skillwren certgate report.json --artifacts ./artifacts --regime '{"task_family":"audit",...}' --cfg <sha256> --monitor-pass --policy-allows
```

It verifies the winner against its own reported bounds, artifact digests,
regime and config binding, the full fallback chain, and invariant
attestation; `--monitor-pass` and `--policy-allows` are caller-asserted
runtime inputs. Verdicts: `allow` (exit 0), `refuse` for a verified
refusal router (exit 0), `deny` (exit 1), invalid input (exit 2).
Per-action structural checks stay with the runtime monitor.

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
