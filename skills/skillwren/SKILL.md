---
name: skillwren
description: Convert an existing SKILL.md into checked SkillWren logic (a complete skill, or flow files with logic blocks) while preserving its requirements; validate the flow and its ordering, review parity, and measure the complete loaded prompt.
---

# SkillWren conversion

Produce a smaller, logically structured skill from an existing skill. Keep the
original intact. Use this repository's compiler and validator; do not substitute
token deletion or an expanded copy of the original for a semantic conversion.

1. Read the original and its relevant local references. Establish which files
   belong to the comparison. Inventory obligations, prohibitions, conditions,
   exceptions, examples that affect decisions, evidence standards, and outputs.
   Mark every "do X before Y" the original states or implies.
   Choose the target layout: flow files (a small `SKILL.md` with only `name`,
   `description`, and a core, plus `logic` blocks in `flows/*.md`; start from
   `docs/current/fragment-template.md`) unless a tool you run reads the
   SkillWren header, in which case a complete skill
   (`docs/current/skill-template.md`).
2. Rewrite the procedure using the grammar in `docs/current/SPEC.md`: explicit branches,
   require/verify gates, bindings, effects, and bounded repairs. Put repeated
   cross-cutting rules once in the contract. Keep specialized facts/examples
   only where they change decisions. The report appendix may define output
   shape; a second procedural glossary should not repeat the flow.
   Write each marked ordering as an `order:` rule, and gate the earlier step
   on every path rather than only inside a conditionally called flow.
3. Preserve authority and failure behavior. Do not turn review into editing,
   optional advice into a requirement, a conditional task into unconditional
   work, or an unavailable check into a passing result. Retain concrete values,
   scope boundaries, and exceptions. A new name alone does not preserve a rule.
4. Run `skillwren check candidate.md` (flow files: `skillwren check
   --fragment --summary flows/*.md`, and review the inferred inputs for
   typos). Without installing, use `PYTHONPATH=src` and the interpreter that
   works: `python3`, `python`, or `py -3` on Windows. Repair the represented control flow,
   rather than weakening requirements just to silence a rule. Consult
   `docs/current/authoring-guide.md` for the conversion workflow and current limits.
5. Create a reviewed map in the format documented in `docs/current/compiler.md`.
   Bind the original and candidate hashes; map every original nonblank line to
   instructions that preserve its intent. Explicitly include relevant original
   reference files. Review the mapping semantically; anchor matching only
   checks bookkeeping. Update the rewrite if anything is lost or invented.
6. Run `skillwren measure original.md candidate.md --json`, adding one
   `--original-context FILE` for each selected original reference. Measure the
   complete expanded prompt using the same tokenizer on both sides. Character
   counts require an explicit metric and must not be called token savings.
7. Complete skills only (flow-file sets are not built yet): run `skillwren build candidate.md --original original.md --review review.json
   --out compiled-skill` with the same context selection. It must validate the
   flow, pass the review checks, and be strictly smaller before publication.
   Preserve required behavior if the size target is difficult; report the
   tradeoff instead of silently dropping content or hiding it in deferred files.

Return the compiled skill, retained-source manifest, requirement map, exact
comparison metric and counts, and material limits. Structural validation and
source retention do not prove semantic equivalence or model adherence. Do not
run paid model evaluations or install the result unless requested.
