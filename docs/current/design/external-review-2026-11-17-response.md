# Response to the external review of 0.9.0 (2026-11-17)

The review assessed `main` at `cd6445a` (v0.9.0). Its verdict: the static
checker is the strongest part; the guard is a careful but narrow write
mediator; the behavioural benefit of the syntax over prose is unproven.
Each finding below is matched to what changed, or why it did not.

| Finding | Assessment | Action |
|---|---|---|
| Behavioural thesis unsupported | Agreed. Every comparison so far is a ceiling tie | Preregistered harder evaluation with a host-hook baseline: `research/repair-eval/` (prereg committed before any run). README now leads with the checker and says the syntax benefit is unshown |
| Completion rewarded deviation in A/B/C protocol 1 | Agreed; already labelled an artefact | Protocol 2 states the format and counts continue-after-failed-gate; rerun: 90/90 complete, 0 deviations, tie (`research/model-evaluation-plan.md`) |
| Guard does not enforce the whole procedure | Agreed, and the README claim "the guard denies what the structure forbids" was too broad | README rewritten. New workflow binding (SPEC Section 22): the guard pins the flow, requires the host approval of its exact bytes at start and on every write, and enforces typed order rules between guard operations as write preconditions; unenforceable rules are listed, not implied |
| Approval never consulted by the controller | Agreed | Same change: an unapproved or edited flow stops the guard (tests `test_guard_workflow.py`; mutant `ignore-workflow-approval` killed) |
| Verifier-pinning footgun (unpinned script argument) | Reproduced and fixed | Every absolute path argument must be pinned, relative script paths are refused; regression test reproduces the swap; mutant `pin-only-executable` killed |
| Security depends on deployment | Agreed; unchanged by design | README states isolation is the host's job. A real-agent isolated run is still open: it needs credentials inside the isolated account or container, which is the owner's decision |
| Validation can certify a faithfully wrong procedure | Agreed | `draft`/`approve` list verify gates without recorded evidence; drafter prompt 2 cut requirement defects 19 to 7 on corpus v2. Human approval stays mandatory |
| "Independent" reviews are model sessions | Agreed; labelled so everywhere | Human review remains open; the repair evaluation uses deterministic host scoring instead of model judges |
| Adoption cost | Agreed | `skillwren policy` generates the pinned, workflow-bound policy from the flow and an operation map, validating it before saving |
| README drift (v0.7 title, pending A/B/C, stale counts) | Agreed | README corrected; `tests/test_readme_sync.py` fails the build when the title carries a version, the status misses the package version, counts are hard-coded, a CLI command is undocumented, or a "pending" claim lingers |

Not adopted: compiling every branch and prose step into guard
preconditions. Only typed steps that are guard operations have a trusted
observation to bind to; the rest would turn self-reports into apparent
enforcement, which is what the review warned against.
