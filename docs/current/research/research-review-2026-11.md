# SkillWren research review, November 2026

Date: 2026-11-12. Baseline: `638f9c7` (0.5.0 plus compact conversion).
Result: package 0.6.0, format 0.6. Follows the
[October review](research-review-2026-10.md), whose separation of
representation, analysis, and execution claims still governs.

This is an engineering review informed by one field report, the history of
SkillWren's one real consumer, and published work. No paid model
experiments were run for it.

## Sources

| Source | What it contributes |
|---|---|
| Full-stack field report 3 (full-stack repository, `docs/research/field-report-2026-11-12-mochios-3.md`) | First build (not design) with full-stack 0.5.0 in a large live repository; 60 guarded runs of history |
| Full-stack D-013 to D-020, FS-009, FS-015 | How the consumer adopted, then moved away from, the SkillWren header |
| SkillWren `git log`, CHANGELOG, benchmarks, October review | How SkillWren got to 0.5.0 |
| Literature (below) | Procedure-following rates, runtime enforcement, instruction density |

## How the project got here

| Date | SkillWren | Full-stack (the consumer) |
|---|---|---|
| 2026-10-01 | 0.3.0 rebrand and packaging; 0.4.0 hardening (AST, CFG, definite binding, dismissal safety); 0.4.1 | |
| 2026-10-01 to 03 | Benchmark rounds 1-2: both representations found 8/8 seeded issues; the logic skill loaded about 5-8x fewer bytes. Content and targets also changed, so no causal claim | |
| 2026-10-03 | Live-fire docs from field report 1 (`38a2da8`) | D-013 adopts a SkillWren header plus logic entrypoint; D-014 live-fire refinements |
| 2026-10-05 | 0.5.0: backfill BF-1 to BF-8 (YAML-safe headers, `else:`, `exec`, `verify ... from`, `conform`) | D-015 after a fresh-user review (NOT-YET); FS-009: a 312-token prose brief scored 8.2/8.8 against the full skill's 8.0/7.7 and plain's 7.3, at about a tenth of the skill's extra cost |
| 2026-10-21 | October review narrows claims, fixes 12 `conform` faults; compact conversion tooling | |
| 2026-11-12 | (this review) | 0.4.0 removes the header: hosts read only `name`/`description`, about 400 tokens per run for nothing. Flows keep `logic` blocks but two of four become prose. 0.5.0 adds an assurance dimension. FS-015: 7/7 hidden checks, but the stack records, assurance table, and guard were skipped. Field report 3 |

The pattern: SkillWren followed its consumer's evidence closely through
0.5.0, then the consumer's own measurements removed the part SkillWren
was built around (the header) while keeping the part SkillWren checks
(the logic). At the baseline, `skillwren check` rejected every full-stack
file with F1/F2, so the format had no checked users.

## Field report 3 mapped to SkillWren

| Finding | SkillWren reading | Change in 0.6 |
|---|---|---|
| G1: assurance screen skipped, two of two live builds | The screen runs inside `design`; `implement` calls design only `unless design is known`. A supplied design skips it. Nothing in the logic says the screen must come first, so nothing could flag it | `order:` rules and P1. `apply assurance screen before write implementation` flags exactly that path |
| Flow files cannot be checked | Full-stack keeps `logic` blocks in prose files with no header | Fragment layout, `check --fragment` |
| `run design from flows/design.md` | Full-stack already wrote cross-file runs that 0.5 called malformed | Cross-file resolution: returns bind, mutation reaches M1, order guarantees carry through |
| D3: `--each` lost inner quotes | `exec` command text had no defined semantics | SPEC Section 6 defines it as an argument list without a shell; scripts for anything more |
| D2: no interpreter guidance on Windows | `conform` allowed only `python`; on this host `python` and `python3` are Store stubs (exit 49, reproduced) | `conform` allows `python3` and `py`; guide mistake 25 |
| Guard log as handoff; failed checks kept | `conform` discarded its report with the workspace | `conform --record DIR` appends one JSON line per run, errors included |
| D1: repeated flags dropped | SkillWren's repeated options already use `append` | None needed |
| D4, G2, G3 | Full-stack guard and reference behaviour | None in SkillWren |

Running the new checker on full-stack's real flows (read-only) found one
more issue: in `flows/design.md`, `integration` is bound only under
`if subject is known:` but used under a later, un-nested `if subject has
existing contracts, providers, or registries:`. The conditions are
correlated in meaning but not in structure, so U1 flags it. It is either a
latent defect (a design with no known subject but with contracts) or a
path the checker should learn to correlate (Section 17, item 4). It is
reported to full-stack, not changed here.

## What the literature says

- **Agents finish tasks more often than they follow procedures.**
  SOPBench ([2503.08669](https://arxiv.org/abs/2503.08669)) and SOP-Bench
  ([2506.08119](https://arxiv.org/abs/2506.08119)) report roughly 27-50%
  procedure compliance. FS-015 (7/7 outcome checks, process skipped) and
  G1 are the same effect in this project.
- **Runtime ordering enforcement closes much of the gap.** Agent-C
  ([2512.23738](https://arxiv.org/abs/2512.23738)) checks Before/After
  constraints over tool calls during generation and reports conformance
  rising from 77-84% to 100% with utility preserved. AgentSpec
  ([2503.18666](https://arxiv.org/abs/2503.18666), ICSE 2026) intercepts
  actions with trigger/predicate/enforcement rules. AgentLTL
  ([2607.02599](https://huggingface.co/papers/2607.02599); the listing
  date is unusual, verify before citing) scores traces or gates each
  prefix online.
- **State routing beats one static prompt.** JourneyBench
  ([2601.00596](https://arxiv.org/abs/2601.00596)): a dynamic agent that
  routes through workflow states was more reliable than a static-prompt one.
  This supports full-stack's core-plus-flow-files layout.
- **More instructions, less adherence.** IFScale
  ([2507.11538](https://arxiv.org/abs/2507.11538), NeurIPS 2025): accuracy
  falls as simultaneous instructions grow, with a bias toward earlier ones.
  Consistent with FS-009's brief beating the full skill, and a reason not
  to grow `SKILL.md`.
- **Typestate** (Strom and Yemini, 1986) is the classical form of "this
  operation is legal only after that one", checked over control flow.
  Order rules are that idea applied to procedure steps.

## Conclusions

1. SkillWren's defensible value is checking procedure structure, not
   compressing prompts. The header and its routing protocol are optional
   conventions; no host uses them.
2. The checked unit should be the `logic` block wherever it lives. 0.6
   makes that true.
3. Static ordering checks address the failure that actually recurred
   (a skipped step), but only in the text. The literature's gains come
   from enforcement at run time. The next step is compiling order rules
   and evidence gates into hooks or guard preconditions (SPEC Section 17,
   item 1).
4. Whether the format changes agent behavior is still unmeasured. The
   October review's controlled design stands; the cheapest version is one
   added arm in full-stack's FS-016 harness: the same flows as prose
   versus as checked fragments, at least three sessions per cell,
   pre-registered.

## Limits

One field report, one repository, author-scored. The literature figures
come from abstracts and summaries, not full replications, and from
different tasks and models. The checker's new rules were validated on
fixtures, 31 mutants, and full-stack's two logic flows; they say nothing
yet about how authors will use them.
