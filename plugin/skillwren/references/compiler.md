# Compile and review a compact skill

Two workflows produce a checked skill. `build` packages a skill that an
author (or agent) has already converted: check, measure, review, build; no
model is invoked and prose is not rewritten automatically. `compile` runs
the natural-language compiler: a model adapter writes the conversion, and
the tool accounts for every source requirement (see the last section).

## Optimized builds

```sh
skillwren measure original.md SKILL.md
skillwren build SKILL.md --out converted --original original.md --review review.json
```

`--original` and `--review` must occur together. These builds require complete
review bookkeeping and a strictly smaller expanded candidate. Optional
`--max-ratio 0.9` requires at least 10% reduction. Default `--metric tokens`
uses optional `tiktoken` and `--tokenizer cl100k_base`. `--metric characters`
uses Unicode characters, explicitly labeled. No estimated fallback exists.
`measure` checks size, not full validity: exit 0 means target met, 1 not met,
2 error. Use `check` or `build` for static validation.

Review JSON has `original_sha256` and `logic_sha256` for exact input bytes,
plus `requirements`: objects with a unique `id`, inclusive `original_lines`
pair, and nonempty `logic_contains` literal anchors in the expanded candidate.
Every nonblank original line must be covered. See `examples/optimization/review.json`.
Authors must review semantic parity: spans and anchors do not prove it.

Declare original supporting files with repeated `--original-context path/to/ref.md`,
resolved from the current directory and confined beneath the original directory.
Add review field `original_context_sha256`
mapping each name to its digest, and `original_file` on its requirements.
Duplicate/escaping input paths fail. Inputs are joined with blank lines for
comparison; raw byte totals are separately labeled. All expanded candidate
context counts. No references are guessed or silently omitted.

The manifest records measurement and review results, including
`semantic_equivalence_proven: false`; original bytes and review live under
`audit/` outside the loaded `SKILL.md`. Acceptance failures publish no output.

## Plain packaging and optional imports

SkillWren is a Markdown-based agent language. Its `contract` and `logic`
blocks use the existing 0.5 grammar and static analyses. `build` adds explicit
context imports and produces a complete, validated skill for an LLM host.
It does not execute the flow or prove natural-language judgments.

```sh
skillwren build examples/context-build/SKILL.md --out built-skill
skillwren check built-skill/SKILL.md
```

Without installing, set `PYTHONPATH=src` and use `python -m skillwren`.
The output directory must be new and its parent must exist. An invalid build
does not publish an output directory. Existing outputs are never intentionally
overwritten; use a fresh build path. Concurrent writers to the same destination
are not supported.

## Source grammar

Outside code fences, after all contract/logic blocks, declare each context:

```text
@context fidelity from "fidelity.md" as instruction
@context examples from "examples.md" as example
@context observations from "observations.md" as data
```

The declaration occupies one unindented line. IDs match
`[a-z][a-z0-9]*(?:-[a-z0-9]+)*` and must be unique in a build. The path is a
JSON double-quoted string, relative to the source document's directory.
Resolved paths, including symlink targets, must remain inside that directory.
Files must be UTF-8. Absolute paths, missing files, invalid encodings,
duplicate IDs, unknown roles, and malformed declarations fail compilation.

Every declared context is included in full. Imported content is literal:
declarations inside it are not recursively expanded. List each dependency
explicitly in the entry document. Roles distinguish instructions, examples,
and data for the reader; they are not a security boundary.

The existing control grammar and validation rules remain defined in
[SPEC.md](SPEC.md). Imports package required context; they do not compress it.

## Generated representation

Each context becomes an opaque Markdown fence with at least four backticks:

~~~~text
````context fidelity instruction
The complete imported text appears here.
````
~~~~

The compiler chooses a fence longer than every backtick run in the payload.
The validator treats the contents as context, not executable contract/logic.
Context blocks must follow all semantic blocks. Their bytes still count toward
the existing body budget. If that budget is exceeded, the build fails instead
of trimming text or increasing the declared budget automatically.

Native `@context` declarations are compilation directives. `check` alone does
not resolve imports; validate the built artifact to check the expanded skill.

## Output and retention contract

- `SKILL.md`: source Markdown with context declarations expanded in place.
- `manifest.json`: format `skillwren-build-1`, source snapshots encoded in
  base64, source/output SHA-256 hashes, warnings, and emitted context spans.

Each context span is a half-open **byte** range `[start_byte, end_byte)` in
`SKILL.md`. Slicing those bytes reproduces the imported file exactly, including
CRLF line endings, Unicode, and absence of a final newline. A separate newline
may be added outside the span to close the Markdown fence. The source entry's
original bytes are also retained, including its BOM if present.

The manifest reports `mode: full` and no deferred contexts. Full means all
**declared** files, not every file in the directory or every cited URL.
The author must identify external context dependencies. Snapshots preserve the
supplied source; they cannot prove an earlier rewrite captured every
requirement of an unprovided original.

Inclusion does not prove comprehension or behavioral equivalence. There is no
automatic summary, semantic compression, network retrieval, or hidden selection.

## Current limits

This is an initial compiler using the existing grammar and its documented
analysis limits. Stronger types, named verifier implementations, scoped approval
tokens, automatic requirement mapping, and richer source-mapped diagnostics
remain future work. `build` packages a fragment-set directory (a
`SKILL.md` plus flow files, SPEC Section 20) after checking every logic
fragment with cross-file runs resolved inside the set, and `measure`
accepts such directories; optimized builds (`--original`/`--review`)
still take a single-file skill only. Warnings are retained in the manifest and counted in the
CLI result. Error locations currently refer to the generated `SKILL.md`;
context spans identify originating files, but general location remapping is
not yet built.

Tests cover source recovery, exact payload spans, Unicode/CRLF, embedded code
fences, unresolved imports, duplicate IDs, path escape, unknown roles, invalid
control flow, output protection, and unclosed contexts.

## Natural-language compilation (`compile`, `inventory`)

```sh
skillwren compile prose/SKILL.md --context prose/references/a.md --out compiled   [--layout inline|fragments] [--rounds 3] [--no-judge] [--keep-failed DIR]   -- py -3 scripts/adapters/claude_compile.py
```

Design and rationale: [design/nl-compiler.md](design/nl-compiler.md).
The adapter protocol is one JSON request per call on stdin with a `phase`:

| Phase | Request | Reply |
|---|---|---|
| `inventory` | numbered `sources`, `entry`; on retry `previous`, `findings` | `inventory` (`requirements`, `non_requirements`), `questions`, `assumptions` |
| `lower` | `sources`, checked `inventory`, `layout` | `files` (path to text, including `SKILL.md`), `lands` (requirement ID to literal anchors) |
| `repair` | as `lower`, plus previous `files`/`lands`, `diagnostics` (`check --json` shape), `findings`, `unbacked_verifies` | as `lower` |
| `judge` | landed `inventory`, `explanations` (deterministic `explain-workflow` text) | `dropped`, `added`, `changed` |

Inventory requirements carry `id`, `kind` (order, gate, branch, decision,
effect, recovery, invariant, input, output, step-meaning, context,
unrepresentable), `text`, `evidence` (exec, user, effect, self, none), and
`source` spans. Findings: I1 malformed, I3 source lines not accounted for,
I4 no landing, I5 anchor not found, I6 wrong placement for the kind (order
on an `order:` rule; gate, branch, decision, effect, recovery on a logic
statement), I7 demanded evidence missing (a gate requirement needs the gate
itself to cite the exec result), I8 kept as prose (warning). Reverse
traceability: I9 a behaviour-bearing statement (ask, `require
confirmation`/`require user`, `abort`, `retry`, `return to`, `write`,
`save`, `exec`, `run`) that no requirement anchor names alone, labelled
with its failure (over-asking or permission restriction, invented abort or
retry, permission expansion); I10 declared scaffolding (warning; only an
evidence `exec` or a branch may be scaffolding); I11 a branch no
requirement justifies (warning); I12 an ask justified only by requirements
that are not decisions, inputs, or user evidence (warning, over-asking);
I13 malformed scaffolding entry. Anchors are literal text or line
references (`L42`, `flows/x.md#L42`); an ambiguous literal justifies
nothing, and review maps receive line references as statement text. J1 is
a judge finding with its category: omission, invention, over_asking,
permission_expansion, permission_restriction, control_flow_distortion,
ordering_distortion. `skillwren inventory check` and `inventory review` run the same
checks on any inventory and emit the review map for a single-file
candidate.

Output: the skill files plus `audit/inventory.json`, `audit/review.json`
(single-file output; it validates under `build --original --review`, which
additionally requires the candidate to be smaller), per-file explanations,
and `audit/compile-manifest.json`. The compiler never approves and never
claims equivalence.
