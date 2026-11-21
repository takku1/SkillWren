# Round 2 results (2026-11-21): compiler only, anchor fix

Read the provenance before the numbers:

- **Ground truth:** the same 88 requirements as round 1, frozen as an
  **AI-reviewed baseline** (not human-approved).
- **Judgments:** Sonnet judge, 12 doubtful verdicts **AI-adjudicated**
  (ChatGPT, GPT-6, as relayed by the owner, 2026-11-21): 6 agreed, 6
  overturned, each with its reason in `scores/*.adjudication.md`. Not
  independent human validation.
- **Builds:** five compiler builds, one run each, Sonnet throughout, pinned
  at `f1a87b4` (SkillWren 0.13.3). The only change from round 1 is the I13
  anchor fix; the I7 evidence rule is unchanged. Nothing was regenerated,
  repaired or rescored. Attempt 1 (`../2026-11-21-round2/`) hit a usage
  limit in every build, measured nothing, and is kept on record outside
  this denominator.
- **Published through** `scripts/lab/fidelity_report.py`:
  `report-compiler-published.json` (webapp-testing) and
  `report-compiler-diagnostic.json` (the four refused drafts).

## Results

| | Round 1 compiler (0.13.2) | Round 2 compiler (0.13.3) |
|---|---|---|
| Builds published | 0/5 | 1/5 (webapp-testing) |
| Requirements preserved, all five artifacts | 83/88 | 84/88 |
| Weakened | 5 | 4 |
| Missing | 0 | 0 |
| Widening introductions | 2 | 2 |
| Enforcement tiers of classified requirements (enforced / recorded / instructed / ambiguous) | 0 / 13 / 65 / 2 (80 classified) | 0 / 8 / 73 / 1 (82 classified) |
| Preserved but unclassified (no tier mapped; not zero enforcement) | 3 (CR-10, CR-19, FS-12) | 2 (FS-2, WT-3) |

The all-five row mixes four refused drafts with one published build, for
comparison with round 1 only. The four refused drafts are diagnostics
(code-reviewer, full-stack, theme-factory, internal-comms: 71/74
preserved). The one published build is reported separately:

| Published build | Preserved | Weakened | Widening introductions | Tiers (enforced / recorded / instructed) |
|---|---|---|---|---|
| webapp-testing | 13/14 | WT-4 | 1: a Windows `py -3` substitution | 0 / 2 / 10 |

Per source (preserved; round 1 draft / round 2): code-reviewer 22/22 /
21/22; full-stack 32/33 / 32/33; webapp-testing 11/14 / **13/14
(published)**; theme-factory 13/13 / 13/13; internal-comms 5/6 / 5/6.

Remaining weakened requirements after adjudication: CR-9 (note critical
issues immediately), FS-11 (record before committing), IC-5 (ask when the
format stays unclear), WT-4 (consider bundled scripts first). Widening
introductions: an invented guideline-load check command with its own
failure path (internal-comms, refused draft) and the `py -3` substitution
(webapp-testing, published). The adjudicator noted the two are not equally
consequential: the first adds an executable check and failure path, the
second is a narrow portability accommodation. The counts do not weight
them.

## Reading

- **The fix's supported effect is narrow: I13 is gone.** No round 2 build
  reports it.
- **Publication 0/5 to 1/5 is not attributable to the fix.** webapp-testing
  failed round 1 on U1, which the fix does not touch; full-stack now fails
  on U1 where it failed on I7. One run per cell moves with model variation.
- **Fidelity is about the same.** 84 vs 83 of 88, within what one
  re-run of five sources can move. The per-source shifts (code-reviewer
  down one, webapp-testing up two) are not tied to the fix either.
- **I7 still refuses three of five** (code-reviewer, theme-factory,
  internal-comms), the same rule that blocked round 1.
- **FS-11, IC-5 and WT-4 are weakened in both rounds** on the compiler
  path; IC-5 and WT-4 were also weakened on round 1's skill-agent path. They
  look like translation weak points in these sources, not run noise.
- **Overturns of writes are not general write authority.** The adjudicator
  overturned four write-widening verdicts (design documents and registry in
  full-stack, the styled artifact, the source's own screenshot path) because
  each implements an effect the source requires or shows; arbitrary writes
  stay unauthorized.

## Limits

One run per cell, one model, five sources, AI-reviewed ground truth and AI
adjudication, the same judge as round 1. Enforcement tiers were mapped at
scoring time for the requirements the judge called preserved. The two
requirements the adjudication moved from weakened to preserved (FS-2,
WT-3) have **missing coverage classification**: no tier was ever mapped.
They are not counted as enforced, recorded, instructed or zero
enforcement. The 82 classified and 2 unclassified preserved requirements
are different populations, and the tier counts describe only the 82.
Classifying the two would mean rerunning coverage on the artifacts, which
this round does not do. No result here
supports a claim about semantic equivalence or about agent behavior using
the output (the execution score is not yet run).

## Next (proposed, not started)

Examine the three remaining I7 refusals as a language-semantics question:
is the compiler demanding external evidence for ordinary procedural
instructions the source never claimed were externally verifiable? Any
change to the evidence rule is decided on those grounds, not by loosening
checks until builds pass, and would be measured in its own pinned round.
