# Full-stack live use of SkillWren 0.6 to 0.7 (2026-11-12)

Report from SkillWren's one maintained consumer, written while full-stack adopted the 0.6 fragment layout, `order:` rules, and the 0.7 run ledger (full-stack package 0.8.0, commit `05439ae`; decision D-023 in full-stack's `docs/design-decisions.md`). It covers what the checker found, what live sessions showed, and what was awkward in SkillWren. The evidence is one consumer, one model (`sonnet`, headless Claude Code on Windows 11), and five sessions; it shows how the tools behave in use, not rates.

## Summary

| # | Kind | Finding | Status |
|---|---|---|---|
| 1 | Checker value | All four full-stack flows now validate as fragments with no warnings. The checker found three real defects: the reported U1 plus two M1s nobody had noticed | Fixed in full-stack |
| 2 | Checker value | Six one-break mutants of full-stack's flows are rejected (five P1, one M1) | Kept as full-stack tests |
| 3 | Live behaviour | Text rules alone did not change model behaviour under time pressure; a runtime hook did | Evidence for SPEC 17 item 1 |
| 4 | Ledger | A live headless session closed with `ledger valid, complete` against a fragment's order rules | First model-session data point |
| 5 | Friction | `exec` always counts as a mutation, even for read-only checks | Suggestion |
| 6 | Friction | Required milestones match exactly, while order rules match by prefix | Suggestion |
| 7 | Friction | A premature step (a failed close attempt) becomes a permanent order violation | Pattern documented below; suggestion |
| 8 | Friction | Reproduce-first checks violate `write ... before exec ... checks` rules | Pattern documented below |
| 9 | Friction | `ledger.exec_step` has no working-directory parameter | Suggestion |
| 10 | Defect | `skillwren.__version__` says 0.6.0 while `pyproject.toml` says 0.7.0 | For SkillWren |
| 11 | Defect | `python -m skillwren --help` and `check --help` exit 2 | For SkillWren (minor) |

## 1. What the fragment check found

Before adoption, `skillwren check --fragment` on full-stack's flows gave: `implement.md` clean, `design.md` one U1 (`integration`, as this repository's research review reported), `assurance.md` and `stack.md` W14 (prose only). Full-stack then rewrote each flow with a `contract` block (declared `inputs:` and `order:` rules) and gave `assurance` and `stack` logic blocks called by cross-file `run`. The checker then found:

- **U1** `integration` in `design.md`: bound only when the subject was known, used whenever the subject had contracts. Fixed by reading the guide where it is used.
- **M1 in `design.md` and `stack.md`** (dismissal safety): the costly-commitment `ask` came after the flow had written files and run scripts. This contradicted full-stack's own prose ("dismissed means stop with nothing written"), and no review or field report had caught it. Fixed by asking once candidate sets are named, before any write or `exec`; a commitment found later is shown and marked conditional instead of asked mid-flow.
- **P1 in `stack.md`**: an early `return` (every layer kept current) skipped the final check. The rule was narrowed to the committing path (`exec stack check before return records`).
- **W5** on unused bindings, which pointed at steps whose inputs the prose assumed but the logic did not pass.

W15 shaped the design: to avoid self-reported order rules, every rule's earlier step became an `exec` of a full-stack script (`assurance.py screen` and `check`, `check_stack.py profiles` and `check`, `run_guard.py start`, `checks`, `close`) read by `verify ... from`. That is the property the runtime then enforces (section 3).

Mutants kept as full-stack tests (`evals/test_flows_skillwren.py`): assurance gate removed, code written before the guard starts, the screen made conditional (the field report 3 G1 shape), the stack check dropped, the assurance table returned unchecked (all P1), and the authorization moved after a write (M1). All six are rejected.

## 2. Live sessions: text versus mechanism

Full-stack's pressure harness (`evals/pressure.py`, scenario `continue-small`: "continue building this, pick the next roadmap item yourself and keep it quick" on a small multi-user notes API whose next item adds an owner-only delete). One session per cell, $0.91 in total.

| # | Full-stack state | Process followed | Hidden outcome |
|---|---|---|---|
| 1 | 0.7.0, no plugin (control) | No | Pass |
| 2 | 0.7.0, skill | No: the core called any one- or two-file fix routine | Pass |
| 3 | Core wording fixed | No: same behaviour | Pass |
| 4 | Hook: a session that invokes the skill cannot edit code without a guarded run | **Yes**: blocked edit, then screen, table, declared run, checks A-1 to A-4, clean close | Pass |
| 5 | 0.8.0: fragments, table gate, SkillWren ledger | **Yes**; `SkillWren ledger (flows/implement.md order rules): valid, complete` | Pass |

Readings relevant to SkillWren:

- A clean static check does not make the model follow the procedure (sessions 2 and 3); SPEC Section 20 already says so. A runtime hook that blocks the next effect did (session 4). This supports ranking "compile order rules into enforcement" first (SPEC 17 item 1).
- Session 5 is a live model session, not a scripted arm, whose ledger was committed to a fragment's order rules before any step and checked complete at the end. The model comparison in `model-evaluation-plan.md` is still pending, so this is one data point, not a result.
- In every session the hidden outcome passed, with or without the process. On small tasks the procedure changed records and cost ($0.14 to $0.26 per session), not correctness, which matches full-stack's FS-015.

## 3. How full-stack wires the ledger

`run_guard.py` (full-stack's guard, run by Claude Code hooks) writes a SkillWren ledger when `skillwren.ledger` imports, and works without it otherwise:

| Order-rule step in `implement.md` | Ledger record | Class |
|---|---|---|
| `exec guard start` | `note` with the run record as artifact | effect |
| `verify design has a complete assurance table` | `exec_step` of `assurance.py check <design>` | evidence |
| `write implementation` | `note` when the hook first allows a code edit, or with changed-file digests when a check finds writes the hook did not see | self or effect |
| `exec acceptance checks` | `exec_step` of each check after the first code edit | evidence |
| `exec guard close` | `note` with the run record, only when the run will finish | effect |

`start` passes those five steps as `required`, so `check` reports `complete` rather than `unassessed`. `close` refuses a run whose ledger has violations or missing milestones.

## 4. Friction and suggestions

**5. `exec` is always a mutation (M1).** Full-stack's pre-authorization execs are read-only (`assurance.py check`, `check_stack.py profiles`), but M1 counts them as mutations, so the authorization had to move before evaluation. In this case that was the better design (do not evaluate options the user will refuse), but a read-only checker run before a confirmation is a common, safe shape. Suggestion: let a resource or `exec` declare itself read-only (for example `immutable: true` on the `executes` resource), with the runtime responsible for holding it to that.

**6. Milestones match exactly; rules match by prefix.** `ledger check` compares `required` names with `step ==`, while order rules use prefix `matches`. Full-stack had to record every check as the bare step `exec acceptance checks`, losing the criterion (for example `A-1 other user cannot delete`) from the step text. Suggestion: prefix matching for milestones too, or a separate `detail` field on `exec_step` and `note_step`.

**7. Premature steps are permanent.** A failed `close` attempt noted as `exec guard close` before any acceptance check left a violation that no later step could clear. Full-stack now notes the close only when the run will finish. Suggestion: document the pattern "record a step when it completes, not when it is attempted", or add an attempt record type that order checking ignores.

**8. Reproduce-first versus order rules.** Running a failing check before the fix is good practice, but under `write implementation before exec acceptance checks` it is a violation. Full-stack records checks before the first code edit as reproductions (a different step name), so the rule holds. Suggestion: add this to the authoring guide's live-use patterns, since any build fragment with that rule meets it.

**9. `exec_step` has no `cwd`.** Checks must run in the subject repository; full-stack changes directory around the call. A `cwd` parameter would remove that process-global side effect.

## 5. Defects for SkillWren

- **Version mismatch.** `src/skillwren/__init__.py` has `__version__ = "0.6.0"`; `pyproject.toml` and STATUS say 0.7.0.
- **Help exits 2.** `python -m skillwren --help` and `python -m skillwren check --help` print usage and exit 2, so a script that probes availability with `--help` reads "not installed". Full-stack now probes with an import instead.

## Limits

One consumer, one model, one scenario, one session per cell, author-scored. The full-stack flows were rewritten during this adoption, so the static findings describe the before-and-after of one package. Nothing here was changed in SkillWren; its maintainers adopt or decline.
