# Pilot report: full-stack logic conversion

Status: draft self-review. This report records a SkillWren logic-first
pilot of the prose full-stack skill plus author dogfooding. It is
self-review evidence, not independent evaluation (see follow-ups).

Subject: [full-stack-logic.md](full-stack-logic.md) (`full-stack-logic`,
v0.4.1) in this directory. The installed prose package under
`skills/full-stack/` is untouched. Method: SkillWren SPEC v0.4.1 plus
authoring guide, both read in full; conversion kept under a distinct
`-logic` skill id with the prose original installed, per the guide's
piloting rule.

## Baseline (prose)

`skillwren check skills/full-stack/SKILL.md`: 2 errors (F1 missing
contract header, F2 missing contract block), 1 warning (W7 `metadata`
field). Token counts below use ceil(chars/4), the validator's
approximation, since tiktoken is not installed here.

| File | Bytes | ~Tokens |
|---|---|---|
| SKILL.md (entrypoint, loads every activation) | 5825 | 1445 |
| references/terminology.md | 9136 | 2275 |
| references/design-method.md | 4283 | 1060 |
| references/artifacts.md | 4166 | 1042 |
| references/existing-projects.md | 3125 | 782 |
| references/implementation.md | 2847 | 712 |
| references/research.md | 3274 | 819 |
| Total portable package | 32656 | 8135 |

## Conversion design

Two flows. `design` covers prose ground/design/bound/deliver;
`implement` runs `design` first, then builds (matches "consume the
scoped design"). The six prose references stay in place and load
through one immutable `references` resource; each load is gated by a
branch condition taken from the prose entrypoint's own loading rules
("when terms are ambiguous", "when decomposition is substantial", and
so on). Methodology detail was not duplicated into the draft; the
appendix carries only generate-step guidance, the fixed design-package
shape, readiness criteria, and retry discipline.

Key control decisions:

- E06-style routine edits are the first branch and return a minimal
  note with no reference loads. The prose skill buries this in its
  description; the logic draft makes it explicit control.
- Declined costly-to-reverse commitments mark the design conditional
  and continue (see dogfood finding D1), instead of aborting.
- Clarification asks come before all writes on every path, so
  dismissal is mutation-free (M1, mechanically checked).
- Effects declare reads of subject/references/registry, creation of
  design documents, and mutation of subject code and the registry.
  Same-path read/write lands under `mutates` as required.

## Validation

- `skillwren check full-stack-logic.md`: clean, zero errors, zero
  warnings. Header ~375/400 tokens, body ~2087/2500.
- Per-block cost: contract 206, design flow 585, implement flow 284,
  appendix 935 (~tokens).
- `python evals/check_artifacts.py`: 0 errors after this report was
  added (the draft links here and to the prose SKILL.md).

## Cost comparison (per-route accounting, D-012)

Routing (is this skill relevant?): header 375 vs prose entrypoint
1445, about 3.9x cheaper, and unselected bodies never load. This is
the main context win and it applies to every activation decision.

Active design run, typical route (terms + patterns refs): logic
375 + 206 + 585 + 935 + 2275 + 1042 = ~5418 vs prose
1445 + 2275 + 1042 = ~4762, about 14% more context. The logic draft
adds control framing while reusing the same meaning corpus, so a full
run costs slightly more. Trivial route (E06, appendix skipped): logic
375 + 585 = 960 vs prose 1445, about 1.5x cheaper.

The SPEC Section 14 "at most half the tokens" criterion applies to
full conversions; this pilot is a control-plane conversion over a
shared meaning corpus, so that criterion is out of scope and no
compression claim is made beyond the routes above. Precision gains
(explicit branches, gates, authority structure, dismissal safety,
pre-execution effects audit) are self-review observations, not
measured outcomes.

## Dogfooding with full-stack (self-review simulation)

The draft was walked through the eval cases in `evals/cases.json`
against `evals/rubric.md` by the author, simulating what each flow
prescribes. Findings and adjustments:

- D1 (fixed): the costly-commitment branch aborted on declined
  authorization, which fails E04/E03 (rubric requires completing the
  independent design and marking the selection conditional). Fixed:
  the repair path applies a conditional mark and returns to a finish
  label, then writes and returns. This uses an explicit `otherwise`
  repair, which the spec permits to override the default abort; the
  mechanical dismissal guarantee (no write before any ask) still
  holds. The prior abort message also claimed the design was
  "recorded as conditional" while recording nothing; the fix makes
  the record real.
- D2 (fixed): the implement flow never loaded the prose
  implementation reference. Fixed: unconditional read plus apply.
  All six references are now reachable: terminology, design-method,
  research, artifacts, existing-projects (design); implementation
  (implement).
- D3 (fixed): the integration-load condition ("shared providers or
  existing contracts") was narrower than the prose rule (design
  deltas or Recurspec integration). Fixed: "existing contracts,
  providers, or registries".
- D4 (fixed): missing prose behaviors found by diffing: deployment /
  publication / tool-install authorization (added to `never`),
  preserving settled user decisions (added to `always`), requests
  without a repository carrying pasted context (appendix section),
  retry discipline (appendix: same failure twice with the same
  evidence becomes a recorded blocker, not a loop).
- D5 (noted, no change): implement re-runs design including its
  asks, so a build after a separate design-only run asks again. The
  prose skill also grounds every run fresh, so this preserves
  behavior; cross-run memory would be a new feature.

Case walkthrough results after fixes: E01 routes and grounds with
exclusions in scope; E02 skips research when supplied contracts
resolve the decision and loads the integration reference for server
authority; E03/E04 deliver conditional designs instead of inventing
or abandoning; E05 loads terminology for the authority conflict and
treats reassignment as a gated commitment; E06 returns the minimal
note with no reference loads; E07 loads the integration reference
for the shared registry. These are author simulations, retained as
hypotheses for independent runs, not as results.

## Limits and follow-ups

- Independent forward evaluation on the supplied cases (isolated
  per-case runs, independent scoring, disagreements retained) is
  still required; it falls under the existing roadmap item FS-001
  and no new roadmap row was added.
- Distribution condition: the draft adapts full-stack prose, which
  itself adapts Recurspec and Architectural Reasoning material under
  MIT terms. The draft points to the prose NOTICE file; if the
  single file is ever distributed alone, the upstream notices must
  travel with it.
- Risk is graded medium (bounded, authorized subject mutation) and
  cost expensive (design plus implementation runs are heavy); both
  are author judgments open to review.

## Attribution

Conversion method: SkillWren v0.4.1 (MIT, `Z:\skilldesigner`). No
SkillWren text is copied into the draft; only the format is
followed. Full-stack prose remains the behavior authority; upstream
MIT notices are retained in
[NOTICE.md](../../../skills/full-stack/NOTICE.md).
