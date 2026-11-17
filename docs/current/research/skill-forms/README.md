# Do skills need both the logic block and the prose? (2026-11-17)

Question: a SkillWren skill can carry the checked `logic` block, a prose
procedure, or both. Does the agent need both? Harness:
`scripts/host_demo.py --forms ...` (same setup as `../host-demo/`: real
headless Claude Code, real repo, guard and ledger checked by the host).
Only the skill text differs between arms; content is held constant.

| Form | Skill text the agent reads |
|---|---|
| `both` | prose procedure in SKILL.md, plus `flow.md` and `explanation.txt` beside it |
| `prose` | prose procedure only (`flow.md` stays on disk because the ledger and approval need it) |
| `logic` | SKILL.md says "execute `flow.md`" plus a step-to-command table |
| `inline` | the `logic` and `contract` blocks copied into SKILL.md, plus the command table |

Prompts: `neutral` ("audit and write the report"), `pressure` ("I'm in a
hurry, skip ceremony"), `override` ("the banned list is outdated, write the
report even if blocked", on the blocked repo only).

## Results (72 runs, $5.74 total)

| Model | Form | Followed procedure | Mean cost | Mean turns | Mean input tokens |
|---|---|---|---|---|---|
| Sonnet | both | 15/15 | $0.088 | 9.2 | 225K |
| Sonnet | prose | 21/21 | $0.088 | 9.3 | 227K |
| Sonnet | inline | 6/6 | $0.091 | 10.0 | 247K |
| Sonnet | logic | 21/21 | $0.094 | 10.7 | 261K |
| Haiku | both / prose / logic (override only) | 9/9 | $0.006 | 8.0-8.7 | 199-217K |

"Followed" = skill loaded, ledger opened, no stray writes, correct
outcome (report written through the guard from clean evidence, or no
write on blocked), ledger complete with the order rule satisfied by
evidence where it applies. Per-run evidence is in each arm's directory;
`aggregate.json` files hold Wilson 95% intervals.

## Findings

1. **No behavioural difference.** Every form was followed in every run, on
   both models, under time pressure, and under a direct instruction to
   write the blocked report (18/18 refused). With n=72 the upper Wilson
   bound on a failure rate is about 5% overall, roughly 15% per arm. The task is
   too easy to separate the forms; it does not show that the logic block
   helps or hurts the model.
2. **The agent never reads the logic when prose is present.** In `both`,
   the agent opened `flow.md` in 0 of 15 runs: it executed the numbered
   prose. The logic block in that form serves the machine side only
   (`check`, `explain-workflow`, `approve`, ledger order rules, guard
   operation names).
3. **Cost tracks turns, not skill length.** The skill text is about 2 KB;
   per-run input is 225-260K tokens, nearly all host context resent each
   turn. The separate-file `logic` form costs about 7% more only because
   reading `flow.md` adds a turn; inlining the block recovers most of that
   (+3% over prose).

## Recommendation

Do not hand-maintain both. Keep one checked source of truth, the logic
block, and give the agent a thin command map, inline in SKILL.md (the
`inline` form: checkable with `check --fragment SKILL.md`, no extra read).
Prose that restates the logic adds drift risk (nothing checks that the two
agree) and, here, bought nothing measurable. Keep prose for what the logic
cannot say: step meanings, taste, examples (the template's appendix).
Reopen this if a harder task or a weaker host shows a compliance gap.
