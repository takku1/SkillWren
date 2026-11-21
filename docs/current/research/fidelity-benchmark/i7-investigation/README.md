# I7 investigation (2026-11-21)

Why the compiler's I7 check ("source demands evidence, but no landed
statement records it") refused three of five builds in round 2 and blocked
builds in round 1. Investigation only: the compiler, the evidence rule and
the benchmark artifacts are unchanged; no builds, no model calls. The probe
(`probe_i7.py`, output in `probe-output.txt`) runs the unchanged checker on
small candidates.

## Short answer

Neither of the two hypotheses holds as stated.

- **The I7 check is correct for the tags it gets.** It never demanded
  runtime evidence at compile time. It demands a statement that would
  produce outside evidence when the skill runs: a `verify ... from` an
  exec/read result for `exec`, an ask or confirmation for `user`, a `write`
  or `save` for `effect`.
- **The failures are not unbacked `verify` gates either.** Not one of the
  benchmark's 18 I7 findings (9 per round) is the `exec` branch.
- **Every one is `effect`:** the inventory phase tagged a procedural
  instruction as demanding an artifact, and I7 then correctly asked for a
  write. The defect sits upstream, in evidence classification, and in a
  pipeline that freezes a wrong tag where no later phase can correct it.

So the fix is a narrower evidence contract at classification, plus two
small pipeline bugs, not a change to what I7 accepts.

## The chain, per refusal (round 2)

Evidence tags come from the I7 messages in `../builds/2026-11-21-round2-attempt2/compiler/*-stderr.txt`;
the inventories themselves were not kept (see Limits).

| Req | Source passage | Generated statement | Demand (rule) | Missing or over-demanded | Category |
|---|---|---|---|---|---|
| code-reviewer R10 | L35 "Produce a categorized report using the Output Template." | `apply report assembly ...`, `show report` | effect: a write (I7) | over-demanded: the report is the reply, no file is named | procedural (output) |
| code-reviewer R26 | L108-115 "Code review report must include: 1 Summary ... 7 Verdict" | prose section; correction gate `unless report has the seven sections ...` | effect: a write (I7) | over-demanded, and unsatisfiable in place: an output requirement lands in prose, where I7 finds no statement (probe `CR-output-in-prose`) | procedural (output shape) |
| theme-factory R3 | L23 "Display the `theme-showcase.pdf` file ... Do not make any modifications to it; simply show the file for viewing." | `show theme_showcase` (+ an invented `exec readonly showcase display check`) | effect: a write (I7) | over-demanded; the only way past it (a write) would break the source's own prohibition | procedural |
| theme-factory R11 | L53 "Read the corresponding theme file from the `themes/` directory" | `read theme file from themes as theme` | effect: a write (I7) | over-demanded: a read | procedural |
| theme-factory R17 | L59 "generate a new theme ... After generating the theme, show it for review and verification." | `generate custom theme ...`, `show custom_theme`, `ask user to review and verify the custom theme`, `require confirmation` | effect: a write (I7) | wrong class: the source's evidence is the user's review, which the draft already has; tagged `user`, it passes | verification obligation (user) |
| internal-comms R4-R7 | L22-26 "Load the appropriate guideline file from the `examples/` directory" (four routes) | `read examples/<file>.md as guideline` (+ an invented `exec guideline load check`) | effect: a write (I7) | over-demanded: a read | procedural |

Round 1's nine I7 findings are the same kind, all `effect`:
- code-reviewer: "read the PR description", the report step and the report shape;
- full-stack: "label doubles with their simulated guarantees";
- internal-comms: the four guideline loads;
- theme-factory: the showcase display.

Across both rounds:
- **Procedural instruction (17 of 18):** the source says do something (read, load, display, produce the reply) and claims no proof.
- **Verification obligation with the wrong evidence class (1 of 18):** theme-factory R17. The source wants the user to verify the custom theme, which is `user` evidence, not an artifact.
- **Completion claim (0 of 18):** I7 does not look at completion claims at all (see below).

## Why it ends in refusal, or in widening

The probe shows that only a write satisfies an `effect` tag:

| Candidate shape | Tag | Result |
|---|---|---|
| `read examples/3p-updates.md as guideline` | effect | I7 |
| same, plus `verify #loaded ... from guideline` | exec | pass: a read result already counts as evidence |
| same read | self | pass |
| same read, plus an invented `exec guideline load check` + `verify ... from loaded` | effect | **I7**: wrong class, the repair cannot converge |
| same read, plus an invented `write #copy guideline with notes` | effect | **pass**, by inventing a write |
| `show result` (the report) | effect | I7; passes only with an invented `write #report` |

Three properties of the pipeline turn a wrong tag into a refusal or a widening:

1. **Tags are frozen.**
   - The inventory phase checks only line coverage. Evidence tags are never checked against the source.
   - Repair rounds get the inventory but return only files, lands and scaffolding (`nlcompile.py` `lower`), so a wrong tag cannot be corrected after the inventory phase.
2. **The I7 message doesn't say which form the tag needs.**
   - It lists every form ("a `verify ... from` an exec result, an ask/confirmation, or a write") whatever the tag.
   - Round 2's repair model added `exec ... check` + `verify ... from` pairs in internal-comms and theme-factory: the right shape for `exec`, the wrong one for `effect`. They could not clear I7, used up the three repair rounds, and stayed in the draft.
3. **The only exit is a widening.** A write landed on the requirement clears I7, and reverse traceability accepts it because a requirement names it. Both adjudicated widening introductions of that exec-check kind fit this pattern:
   - round 1 #6, the theme-factory showcase verification command;
   - round 2 #7, the internal-comms guideline-load check.

   They are consistent with I7 repair pressure, though the repair history wasn't saved to prove it.

The classification prompt invites the mistag. `scripts/adapters/claude_compile.py` defines:
- the `effect` kind as "file written, command run", so a command counts as an effect there, though for evidence a command is `exec`;
- `effect` evidence as "an artifact must exist", without saying that a reply, a displayed file or a read file is not an artifact.

It never says that an instruction to act is not, by itself, a demand for proof.

## Counterexamples: what I7 must keep

| Probe case | Source says | Draft says | I7 |
|---|---|---|---|
| `X-exec-self-report` | run the tests; do not merge unless they pass | `verify #tests the test suite passes` (no `from`) | fires: an unsupported verification claim. This is the measured silent-loss class from the 0.9 fidelity run |
| `X-effect-lost` | save the plan to docs/plan.md before migrating | the plan is computed and never written | fires: a lost artifact obligation |
| `X-user-lost` | the owner approves before deploy | the model judges approval itself | fires: a lost human decision |

Any change that lets a self-class statement satisfy `exec`, `effect` or `user` would pass all three. That includes accepting `show` or `read` for `effect`, or dropping I7 on a repair round. So the rule's satisfaction table stays as it is.

**Completion claims are a separate gap.** A `return` that states "security review completed" is not an evidence-bearing statement, and I7 does not inspect it. Today's protection comes from elsewhere: `verify` gates without `from` are listed as unbacked. Nothing here suggests I7 should take that role; it is noted so that relaxing I7 is not mistaken for touching it.

## Proposed correction (for decision; nothing implemented)

1. **Narrower evidence contract at classification** (adapter prompt; needs its own pinned round to measure):
   - `effect` only when the source requires an artifact to be created or changed: a file written, saved, edited or committed, or a named output file.
   - Reading, loading, displaying or showing a file, and producing the reply, are `self`.
   - "Check/confirm/ensure X" is `exec` only when a command or file result can show it, and `user` when a person is asked to verify.
   - State outright that an instruction to act is not a demand for proof.
   - Fix the `effect` kind wording, which counts a command run as an effect.
2. **Pipeline bug: a tag the checker can't satisfy must be correctable, not frozen.** Two options, either narrow:
   - (a) let the repair phase propose a retag. The change is recorded in the audit with the source line, and a retag that drops evidence the source states is a judge or adjudication item, never silent;
   - (b) refuse the inventory when an output, context or step-meaning requirement (prose kinds) carries `exec`, `user` or `effect` evidence. That combination can't be satisfied by construction (probe `CR-output-in-prose`).

   (b) is mechanical and closes R26's case; (a) is needed for the read/show cases.
3. **Repair message bug:** I7 should name the one form its tag needs, and say that when the source demands no such proof, the tag is the problem. Inventing a statement to satisfy it is not the fix.
4. **Keep the debugging record:** `--keep-failed` should also save the landed inventory, which holds the evidence tags. Without it this investigation had to infer the tags from the error text, and couldn't see the repair history.

Choosing between "bug fix", "narrower contract" and "no change":
- items 2b, 3 and 4 are bug fixes and don't touch what I7 accepts;
- item 1 is the narrower contract;
- the satisfaction table is the "no change" part.

## Limits

- The inventories and repair rounds of the refused builds weren't saved, so tags are known only from the I7 messages, and repair intent is inferred from the final drafts.
- One model, five sources, two runs per source in total.
- The categories in the chain table are this investigation's reading of the source passages (an AI reading, not adjudicated).
