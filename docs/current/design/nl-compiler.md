# NL compiler: full-context natural language to checked SkillWren

Status: build-order steps 1-4 implemented 2026-11-18 (`check --json`,
`skillwren inventory`, `skillwren compile` with a stub-driven offline test
suite, `scripts/adapters/claude_compile.py`); the full-context benchmark is
frozen in `research/nl-compiler/full-stack-0.2/`. It builds on the 0.9/0.10
pieces and the measured drafting results; it adds no syntax.

## Goal

One command takes a full-context natural-language source (a prose
`SKILL.md` and its references, or a long intent document) and emits a
checked SkillWren skill: an inline-form `SKILL.md` (contract and logic
blocks, step meanings, a step-to-command table) or a fragment set, plus a
requirement map that shows where every source requirement went. The output
is "SkillWren level": it passes `check`, has no unbacked verifies the
source did not allow, gives every guard verb a typed ID, and ends in a
`build` artifact a human can `approve` and `policy` can bind.

The compiler proposes. Approval stays a human step; nothing in this
design upgrades a model's output into an equivalence claim.

## What already exists, read as compiler phases

| Phase | Existing piece | Gap for full context |
|---|---|---|
| Front end (NL to IR) | `draft` + `scripts/adapters/claude_draft.py` (prompt 2) | One intent file in, one fragment out. No source spans, no reference files, no requirement list, no multi-file output |
| Semantic analysis | `check` (CFG, must-analysis, order, M1, authority), `check --audit` evidence classes, `draft`'s unbacked-verify report | Text-only diagnostics; a model repair loop has to parse prose |
| Decompiler | `explain-workflow` (deterministic AST to prose) | Used by evaluation, not by the drafting loop |
| Fidelity check | `review.py` requirement map (`original_lines`, `logic_contains`, hash-bound); `fidelity_eval.py` judge | The map is hand-written; the judge lives only in an eval script |
| Back end | `build` (single file, optimized with review, or fragment set), `policy`, `approve` | Optimized builds refuse fragment sets |
| Runtime | guard, ledger, audit, sandbox, conform | Not a compiler concern; consumes the output |

So the back half is solid. The missing part is the front end and the
fidelity loop around it, which is exactly where the measurements say the
loss is.

## What the measurements say the compiler must solve

- Silent requirement loss is the main defect, not invented permissions.
  v1: 22 requirement defects, 7 silent. v2 with prompt 2: 7 defects,
  3 silent (an ordering between two asks, a write moved into a branch, a
  dropped abort). (`research/nl-fidelity-v2/model-draft/`)
- Hand conversion of a real prose skill dropped four appendix-level
  details (severity rubric, oracle criterion, no-findings statement,
  unexecuted-tests note), caught only by comparison against another
  conversion. (`research/lifecycle/c-converted/`)
- Clarifying questions covered 9 of 22 defects; ranking them better does
  not reach the main loss. (`research/game-theory-2026-11.md`)
- First-draft validity was 3/9 files; one repair round with check errors
  reached 8/9. Failures were mechanical.

Conclusion: a per-requirement accounting, checked mechanically, is the
lever. Better prompting alone moved 19 to 7; the remaining silent defects
are structural and invisible to a single drafting pass.

## Pipeline

```text
sources ──► 1 ingest ──► 2 inventory ──► 3 lower ──► 4 check/repair ──► 5 round-trip ──► 6 build
 (prose,     spans,       requirement     logic,       structured        explain +         manifest,
  refs)      digests      IR (JSON)       contract,    diagnostics,      per-req judge,    map, report
                                          meanings     bounded loop      coverage gate
```

### 1. Ingest

Inputs: an entry file plus explicitly declared context files (same rule as
`--original-context`: confined, no guessing). Output: a source table of
files, digests, and numbered nonblank lines. Deterministic.

### 2. Requirement inventory (model, then mechanical check)

The model extracts a requirement list before writing any logic. Each item:

```json
{"id": "R07", "source": [{"file": "SKILL.md", "lines": [41, 43]}],
 "kind": "order|gate|branch|decision|effect|recovery|invariant|output|step-meaning|context|unrepresentable",
 "text": "run the dependency check before writing the report",
 "evidence": "exec|user|effect|self|none"}
```

Mechanical checks: every nonblank source line is covered by some item or
explicitly marked `non-requirement` with a reason (headings, examples
that do not change decisions). This is the existing review-map coverage
rule moved to the front of the pipeline. The `kind` decides where the item
must land; `unrepresentable` (correlated conditions, taste, optional
resources) lands in prose with a flag, never nowhere.

This step is where the "dropped abort" and "lost ordering" defects become
visible: they are now rows with no destination.

### 3. Lower to SkillWren

The model writes the skill from the inventory, not from the raw prose, and
tags each statement with the requirement IDs it implements. Tags travel as
a side table (statement line to IDs), never as syntax, so the language
does not change. Output layout follows the 0.9 recommendation: inline
contract and logic in `SKILL.md`, step meanings, command table; fragment
files only when the flow count makes one file too large.

Lowering rules already proven by prompt 2 become deterministic lint
instead of prompt text where possible: typed IDs on every `verify`/`write`,
no bare `return`, no unrequested existence gates, re-check before `retry`.

### 4. Check and repair (bounded)

Run `check` (and `--audit`) and feed structured diagnostics back. Needs a
`check --json` output (rule, line, message, fix, flow). Repair rounds are
bounded (default 3); a skill still invalid after the bound is a compile
failure with the diagnostics, not a degraded output.

Also checked here, deterministically:

- every inventory item of kind order/gate/branch/decision/effect/recovery
  is tagged on at least one statement or contract line;
- every `order` item became an `order:` rule and does not warn W13;
- every gate whose item says `evidence: exec` is a `verify ... from` an
  `exec` binding (`unbacked_verifies` already exists);
- every `step-meaning` and `context` item appears in the prose sections.

### 5. Round-trip (decompile and judge)

`explain-workflow` the candidate. A separate judge session compares each
inventory item against the explanation and returns dropped, added,
changed. This is `fidelity_eval.py`'s judge promoted into the pipeline,
scoped per requirement so findings name an ID. A dropped item goes back to
step 3 once; after that it is reported. The judge is a model; its verdicts
are labelled assisted review in the manifest.

### 6. Build and report

Emit through the existing `build`. Generate `review.json` from the
inventory and tags (`original_lines` from spans, `logic_contains` from the
tagged statements), so the hash-bound optimized-build gate validates the
compiler's own bookkeeping. The manifest records model, prompt version,
source digests, rounds used, unresolved questions, assumptions,
unrepresentable items, and judge findings. Exit codes: 0 compiled clean,
1 compiled with open findings (questions, judge drops, unrepresentable
items), 2 failed.

## Contracts

- `skillwren compile SOURCE [--context FILE]... --out DIR -- ADAPTER...`
  Adapter protocol extends `draft`'s stdin/stdout JSON with a `phase`
  field (`inventory`, `lower`, `repair`, `judge`), so `draft` keeps
  working and a stub adapter can drive tests offline.
- Inventory and tag tables are JSON files in the output's `audit/`
  directory, outside the loaded prompt.
- No step writes outside `--out`; failure publishes nothing (same as
  `build`).

## What stays out

- No new syntax. Requirement tags are a side table.
- No automatic approval, no "semantically equivalent" claim. The manifest
  keeps `semantic_equivalence_proven: false`.
- No inference of correlated conditions (STATUS key decision, 0.9).
- DPCC selection (`select`/`certgate`) can later choose between compiled
  representations under measured risk; it is not needed for a first
  compiler.

## Evaluation gate

The 26-flow corpus is intent-sized. Full context needs real sources:

- prose originals with known conversions: `examples/optimization/original.md`,
  the theme-factory original, the code-reviewer source, full-stack flows;
- the reserved converter regressions from the full-stack field report
  (two M1 violations, the conditional assurance screen, the missing stack
  check, the early return that skipped the final check);
- corpus v2 as the small-case regression set.

Measure per run: valid after repair, inventory coverage, requirement
defects by judge, silent defects (no question, assumption, or flag), and
cost. Freeze the set before the first paid run, as with v2. Target to beat:
prompt 2's 7 defects / 3 silent on v2, and zero silent drops on the
lifecycle-c original. Human review of a sample stays an open item.

## Build order

1. `check --json` and `explain-workflow --json` (deterministic, no model).
2. Requirement inventory schema, coverage checker, and review-map
   generator from inventory plus tags (deterministic, testable with fixtures).
3. `compile` command with phased adapter protocol and a stub adapter;
   offline tests for the loop, bounds, and no-publish-on-failure.
4. Claude adapter phases (inventory, lower, repair, judge), reusing prompt 2.
5. Freeze the full-context corpus; run; write up results including nulls.
6. Allow optimized builds of fragment sets, or keep compile output to
   inline form until that lands.
