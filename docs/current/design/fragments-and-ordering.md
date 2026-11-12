# Fragments, cross-file runs, and order rules (format 0.6)

Status: built 2026-11-12 as package 0.6.0. Normative text: SPEC Sections 6,
11, 13, 17, and 20. Evidence and reasoning:
[research review 2026-11](../research/research-review-2026-11.md).

## Outcome

`skillwren check --fragment` checks the `logic` blocks in full-stack's flow
files as they are written today, including calls between them, and an
`order:` rule can state that the assurance screen comes before
implementation, with the checker flagging the path that skips it.

Excluded: no edits to full-stack (its maintainers adopt or decline); no
runtime enforcement (next step, SPEC 17 item 1); no change to how complete
skills validate, apart from the format version.

## Choices

| Choice | Taken | Alternative and why not |
|---|---|---|
| Where fragments declare ordering | Optional `contract` block with `order:` | A header field: fragments have no header by design. In-flow statements: the rule spans flows and paths, which is contract-level |
| Pattern language | Statement prefix, normalized, `*` wildcard | Regular expressions: harder to read in a skill. Exact text: brittle against argument changes |
| Meaning of "A before B" | Must-analysis: A completed on every path to B; failed gates establish nothing; runs count when the callee guarantees A on every return | Dominance only: a failing gate whose repair falls through would count as done. Any-path: misses exactly the G1 shape |
| Scope of checking | Per flow from its own entry | Interprocedural entry facts: a host can enter any flow directly, so assuming callers' facts would be unsound |
| Fragment inputs | Declared `inputs:`, else inferred (never bound, or presence-tested) | Always strict: every existing full-stack flow would fail on names like `subject`. Always lax: U1 would never fire |
| Cross-file run resolution | Beside the file, then parents up to the `SKILL.md` folder | Repository root: skills are installed anywhere; the skill root is the stable anchor |
| `exec` source in fragments | A place, not a binding | Binding: every `exec ... from checks` would be U1 with no way to declare a resource |
| Mode selection | Explicit `--fragment` | Auto-detect: a broken header would silently downgrade a skill to fragment checks |

## Refactor

`validator.py` (2,020 lines, `analyze_flow` 508 lines) became the
`skillwren.validator` package: `syntax`, `document`, `schema`, `flowgraph`
(with one shared must-dataflow solver), `ordering`, `analysis`
(`FlowAnalysis`, one method per verb and check), `files` (skill and fragment
validation, `Workspace` resolution), and `explain`. Public names are
re-exported, so `from skillwren.validator import ...` keeps working.

Equivalence evidence: every diagnostic (line, rule, message) for every
fixture, example, doc, benchmark file, and mutant was captured before the
split and compared after it. The only differences were the format version
in two messages and the 0.6 fixture bump; fix-hint text changed in a few
places by design.

## Checks

- 31 mutants (3 new on the `valid-order` base), 0 misses, 0 deviations.
- New fixtures under `tests/fixtures/fragments/skill/` reproduce G1,
  failed-gate, callee guarantee, unresolvable runs, declared inputs,
  correlated branches, mutating callee before an ask, and W13/W14.
- Full-stack `flows/implement.md`: clean. `flows/design.md`: one U1
  (`integration`), reported upstream.
