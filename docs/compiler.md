# Compile and review a compact skill

The primary workflow is original skill → authored logic conversion → check,
measure, review, build. No model is invoked and prose is not rewritten automatically.

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
remain future work. Warnings are retained in the manifest and counted in the
CLI result. Error locations currently refer to the generated `SKILL.md`;
context spans identify originating files, but general location remapping is
not yet built.

Tests cover source recovery, exact payload spans, Unicode/CRLF, embedded code
fences, unresolved imports, duplicate IDs, path escape, unknown roles, invalid
control flow, output protection, and unclosed contexts.
