---
name: skillwren
description: Convert an existing SKILL.md into checked SkillWren logic (a complete skill, or flow files with logic blocks) while preserving its requirements; check the flow and its ordering, review parity against the original, and measure the complete loaded prompt. Use when asked to convert, compile, shrink, or restructure a skill into SkillWren. Not for authoring a new skill from scratch, editing the original skill, running paid model evaluations, or installing the result.
---

# SkillWren conversion (SkillWren logic)

Produce a smaller, logically structured skill from an existing skill. The original stays intact. Use this repository's compiler and validator; token deletion or an expanded copy of the original is not a semantic conversion. The procedure is the `logic` block below; execute it as written.

```contract
always:
  use this repository's compiler and validator
  put repeated cross-cutting rules once in the contract and keep specialized facts and examples only where they change decisions
  the report appendix may define output shape but a second procedural glossary must not repeat the flow
  preserve authority and failure behavior
  retain concrete values, scope boundaries, and exceptions because a new name alone does not preserve a rule
  map every original nonblank line to instructions that preserve its intent and explicitly include relevant original reference files
  measure the complete expanded prompt with the same tokenizer on both sides
  character counts require an explicit metric name stated with every count
  state that structural validation and source retention do not prove semantic equivalence or model adherence
  when the size target is difficult preserve required behavior and report the tradeoff
never:
  modify the original skill
  substitute token deletion or an expanded copy of the original for a semantic conversion
  turn review into editing, optional advice into a requirement, a conditional task into unconditional work, or an unavailable check into a passing result
  weaken requirements just to silence a rule
  call character counts token savings
  silently drop content or hide it in deferred files
  publish a build that failed validation, failed the review checks, or is not strictly smaller
  run paid model evaluations or install the result unless requested
inputs:
  original, references, checks, output, review
order:
  apply inventory before apply rewrite
  write#candidate before exec#checkrun
  verify#check before write#map
  verify#parity before exec#measure
  exec#measure before exec#buildrun
  verify#final before return#result
```

```logic
convert:
  if paid model evaluation or installing the result is wanted:
    ask user to confirm paid model evaluation or installation of the result
    require confirmation
      otherwise:
        apply decline note with references as declined

  read relevant local references of the original skill as references
    otherwise:
      apply gap note with references as gaps

  if a tool you run reads the SkillWren header:
    apply complete skill layout with references as layout
  else:
    apply flow files layout with references as layout

  if a model-run mechanical accounting compile is wanted:
    exec #compile skillwren compile from checks as compiled
    verify #creview open findings, questions, and judge results of the compile are reviewed from compiled
      otherwise:
        apply inventory review with compiled as inventory
        retry
    apply inventory review with compiled as inventory
    apply rewrite review with compiled as candidate
  else:
    apply inventory with references as inventory
    write #inventory inventory with review
    apply rewrite with layout as candidate

  write #candidate candidate with output

  unless skillwren is installed:
    exec #probe interpreter probe from checks as probe
    verify #interp the interpreter that works is python3, python, or py -3 from probe
      otherwise:
        if no interpreter works and the failure persists with the same evidence:
          apply blocker record with probe as report
          return #blocked report as report
        apply local invocation with layout as invocation
        exec interpreter probe from checks as probe
        retry

  exec #checkrun skillwren check from checks as checked
  verify #check the check reports no findings from checked
    otherwise:
      if the same finding persists with the same evidence after a repair:
        apply blocker record with checked as report
        return #blocked report as report
      apply repair with candidate as candidate
      write candidate with output
      exec skillwren check from checks as checked
      retry

  if layout is flow files:
    verify #inputs the inferred inputs in the summary have no typos from checked
      otherwise:
        if the same input typo persists with the same evidence after a repair:
          apply blocker record with checked as report
          return #blocked report as report
        apply input typo repair with candidate as candidate
        write candidate with output
        exec skillwren check from checks as checked
        retry

  apply map with candidate as map
  write #map map with review
  exec #mapcheck mapping bookkeeping check from checks as mapchecked
  verify #parity every original nonblank line and relevant reference file is mapped and the mapping is reviewed semantically from mapchecked
    otherwise:
      if the same lost or invented content persists with the same evidence after an update:
        apply blocker record with mapchecked as report
        return #blocked report as report
      apply rewrite update with map as candidate
      write candidate with output
      apply map with candidate as map
      write map with review
      exec mapping bookkeeping check from checks as mapchecked
      retry

  exec #measure skillwren measure from checks as measured
  verify #metric the measure counts the complete expanded prompt with the same tokenizer on both sides and names an explicit metric for every count from measured
    otherwise:
      if the same metric failure persists with the same evidence:
        apply blocker record with measured as report
        return #blocked report as report
      apply metric repair with measured as measured
      exec skillwren measure from checks as measured
      retry

  if layout is complete skill:
    exec #buildrun skillwren build from checks as built
    verify #build the build validates the flow and passes the review checks from built
      otherwise:
        abort with "Build failed validation or review checks; nothing is published."
    if the build is not strictly smaller than the original:
      apply tradeoff record with built as limits
    else:
      apply size note with built as limits
  else:
    if the measured candidate is not strictly smaller than the original:
      apply tradeoff record with measured as limits
    else:
      apply size note with measured as limits

  apply result report with limits as report
  write #reportfile report with output
  verify #final report lists the compiled skill, retained-source manifest, requirement map, exact comparison metric and counts, and material limits, and states that structural validation and source retention do not prove semantic equivalence or model adherence from measured
  return #result report as report
```

## Step meanings

- **decline note**: the user declined paid evaluation or installation; do neither, and continue with the conversion.
- **gap note**: record a missing or unreadable local reference as a gap in the comparison; continue.
- **complete skill layout**: complete skill with the SkillWren header, from `docs/current/skill-template.md`.
- **flow files layout**: a small `SKILL.md` with only `name`, `description`, and a core, plus `logic` blocks in `flows/*.md`, from `docs/current/fragment-template.md`. This is the default.
- **inventory**: establish which files belong to the comparison (the original and its relevant local references). List obligations, prohibitions, conditions, exceptions, examples that affect decisions, evidence standards, and outputs. Mark every "do X before Y" the original states or implies.
- **inventory review**: review the compile's `audit/inventory.json` and its open findings, questions, and judge results exactly as for your own conversion.
- **rewrite**: rewrite the procedure with the grammar in `docs/current/SPEC.md`: explicit branches, require/verify gates, bindings, effects, and bounded repairs. Write each marked ordering as an `order:` rule and gate the earlier step on every path, not only inside a conditionally called flow.
- **rewrite review**: take the compile's lowered candidate and `audit/review.json` and fix anything lost or invented.
- **local invocation**: without installing, set `PYTHONPATH=src` and use the interpreter that works: `python3`, `python`, or `py -3` on Windows.
- **repair**: fix the represented control flow; never weaken a requirement to silence a rule. Consult `docs/current/authoring-guide.md` for the conversion workflow and current limits.
- **input typo repair**: correct names the checker inferred as inputs that are typos.
- **map**: reviewed map in the format of `docs/current/compiler.md`, binding the original and candidate hashes. Anchor matching only checks bookkeeping, so review it semantically.
- **rewrite update**: update the rewrite for anything the review found lost or invented.
- **metric repair**: state the explicit metric and tokenizer for each count, and include the complete expanded prompt with the same tokenizer on both sides; character counts are never called token savings.
- **blocker record**: the same failure recurred with the same evidence; record the blocker, what was not done, and the next step as the report, and stop repairing.
- **tradeoff record**: the candidate is not strictly smaller; it is not published as a size win. Preserve required behavior, do not silently drop content or hide it in deferred files, and report the tradeoff in the limits.
- **size note**: no size tradeoff; the limits record only the other material limits.
- **result report**: return the compiled skill, retained-source manifest, requirement map, exact comparison metric and counts, and material limits.

## Commands

Run from the repository root; `SW` = `skillwren`, prefixed with the local invocation when not installed.

| Flow step | Command |
|---|---|
| `exec #compile` | `SW compile original.md --context ref.md ... --out candidate -- <adapter>` (writes `audit/inventory.json`, `audit/review.json`) |
| `exec #probe` | try `python3`, `python`, `py -3` with `--version`; use the one that works |
| `exec #checkrun` (flow files) | `SW check --fragment --summary flows/*.md` |
| `exec #checkrun` (complete skill) | `SW check candidate.md` |
| `exec #mapcheck` | the anchor check of the review map (the review checks of `SW build`) |
| `exec #measure` | `SW measure original.md candidate.md --json`, plus one `--original-context FILE` per selected original reference |
| `exec #buildrun` (complete skills only; flow-file sets are not built yet) | `SW build candidate.md --original original.md --review review.json --out compiled-skill`, with the same context selection |
