# Round 1 results (2026-11-20)

First comparison of the two build paths on the fidelity benchmark. Read the
provenance before the numbers:

- **Ground truth:** 88 requirements frozen as an **AI-reviewed baseline**
  (not human-approved).
- **Judgments:** Sonnet judge, 18 doubtful verdicts **AI-adjudicated**
  (ChatGPT, GPT-6, as relayed by the owner): 10 agreed, 8 overturned, each with a reason in the
  `scores/*.adjudication.md` sheets. Not independent human validation.
- **Builds:** one run per source and path, Sonnet throughout, pinned at
  `cc9b785` (SkillWren 0.13.2); nothing regenerated, repaired or rescored.
- **Published through** `scripts/lab/fidelity_report.py`
  (`report-skill.json`, `report-compiler-diagnostic.json`).

## Results

| | Skill agent (published) | Compiler (refused drafts, diagnostic only) |
|---|---|---|
| Builds published | **5/5** | **0/5** |
| Requirements preserved | 85/88 | 83/88 |
| Weakened | 3 | 5 |
| Missing | 0 | 0 |
| Widening introductions | 0 | 2 |
| Enforcement tiers (enforced / recorded / instructed / ambiguous) | 0 / 7 / 77 / 0 | 0 / 13 / 65 / 2 |

The compiler's fidelity is a diagnostic of drafts it refused to publish;
it is never combined with its 0/5 publication rate.

Per source (preserved; skill / compiler draft): code-reviewer 22/22 /
22/22; full-stack 33/33 / 32/33; webapp-testing 13/14 / 11/14;
theme-factory 12/13 / 13/13; internal-comms 5/6 / 5/6.

Remaining weakened requirements after adjudication:

- Skill agent: WT-4 (consider bundled scripts first), TF-9 (custom theme
  only when no preset fits), IC-5 (ask when the format stays unclear).
- Compiler drafts: FS-11 (record before committing), IC-5, WT-4, WT-13,
  WT-14 (selectors and waits softened to "use judgment"); widening: an
  invented showcase-check command and an artifact-file write
  (theme-factory).

## Reading

- **The compiler's refusals did not track fidelity in this round.** The
  drafts it refused preserved about as much as the published skill builds
  (83 vs 85 of 88) and were the only ones adding widening behavior. Its
  refusals came from its own evidence rule (I7), anchor friction (I13) and
  unrepaired check errors, not from requirements the judge found lost.
- **Strictness bought observability, not fidelity.** The compiler's drafts
  anchored more preserved requirements to something observable (13
  recorded vs 7), which is what I7 pushes for, at the price of publishing
  nothing.
- **Nothing is enforced on either path:** no guard policy was part of the
  task, and these sources are mostly review and authoring skills whose
  requirements are the model's to carry (77 and 65 instructed).
- IC-5 is weakened on both paths, at the requirement the reviewers marked
  as an interpretation of an ambiguous source.

## Limits

One run per cell, one model, five sources, AI-reviewed ground truth and AI
adjudication, the same judge for both paths. Enforcement tiers were mapped
at scoring time for the requirements the judge called preserved; the four
requirements the adjudication moved from weakened to preserved (CR-10,
CR-19, FS-12 on compiler drafts; FS-9 on the skill build) carry no tier, so
tier counts sum to less than the preserved counts. No result here supports
a claim about semantic equivalence or about how an agent behaves when using
either output (the execution score is not yet run).

## Next (agreed sequence)

Investigate the I13 anchor issue (a statement repeated in its own repair
branch), fix it on control-flow grounds with a regression test, and run a
separately pinned round 2 of all five compiler builds with the I7 evidence
rule unchanged, so its effect is isolated.
