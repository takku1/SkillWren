# Bounded retry: semantics before syntax

Status: design only, 2026-11-18. No grammar change. Owner decision: settle
whether bounded retry is a missing language capability or a compiler
artifact before touching SPEC.

## Question

The NL compiler's judge flagged repair loops with no way out
(`research/nl-compiler/README.md`). Three cases need different answers:

1. the source requires a bounded retry (a count, or "at most");
2. the source requires recovery and a termination condition but no count
   ("until a blocker prevents progress", "stop when...");
3. the source requires neither, and the compiler invented the loop.

Only case 1 clearly justifies preserving a bound in the language. Case 2
needs its termination condition expressed. Case 3 is a compiler defect.

## Evidence

Every `retry` and `return to` in the three compiled outputs, classified
against its source text (script and listing reproducible from the
published runs; `research/nl-compiler/`):

| Output | Loops | Case 1 | Case 2 | Case 3: invented | Case 3: gate made a loop | Exit in repair |
|---|---|---|---|---|---|---|
| full-stack run 1 | 13 | 0 | 2 | 7 | 4 | 0 |
| full-stack run 2 | 2 | 0 | 1 | 0 | 1 | 1 |
| dogfood | 6 | 0 | 5 | 1 | 0 | 5 |

- **Case 1 never occurs.** Neither source states a count. The nearest
  wording is "bounded repairs" (SkillWren's own skill), which asks for
  termination without a number.
- **Case 2 is real and states a condition, not a count:**
  full-stack `implementation.md` "continue until the selected requirements
  are satisfied or concrete blockers prevent further progress";
  `research.md` "stop when the consequential claim is supported ... and
  further searching is unlikely to change the current decision".
- **Case 3 dominated run 1:** retries on grounding, authority, claims,
  validation, path and substitution checks the source states as checks,
  not as repeat-until-pass; and four readiness gates turned into loops back
  to design, although the source says to deliver unmet readiness "as
  conditional". The run-2 lowering rules removed almost all of them.

The idiom matters more than the compiler. Hand-written workflows:

| Source | Loops | Without an exit in the repair |
|---|---|---|
| full-stack live flows (`flows/*.md`) | 8 | 8 |
| examples (code-reviewer, theme-factory, repair-eval) | 15 | 12 |
| corpus v2 reference flows | 2 | 2 |
| `fragment-template.md` | 2 | 2 |
| test fixtures | 2 | 1 |
| **Total** | **29** | **25** |

So exitless retry is how SkillWren is normally written, including the
template the compiler is given. "Retry until it passes" is the language's
default reading of `retry`; nothing checks that a repair can end.

## Semantics, if a construct is ever added

Written so that any syntax could be judged against it. Not adopted.

**Loop.** A repair loop is an `otherwise:` block under gate G that ends in
`retry` (re-evaluates G) or `return to L` with L before G. An attempt is
one evaluation of G (or one arrival at L from inside the loop).

**Termination kinds.**

- *count*: at most N attempts, the first included;
- *no progress*: stop when G fails again with the same evidence (for a
  `verify ... from <exec>` gate, the same exec output digest);
- *external*: stop on a named blocker condition or a user decision.

**Counting scope.** The counter belongs to one entry into the loop: it
starts when G is reached from outside its own repair and resets on the
next outside entry. A nested loop's counter resets on each outer attempt.
Counters are not shared across flows or `run` calls.

**Exhaustion.** Reaching the bound is a path the author must handle
explicitly, like `otherwise:`; when unhandled it takes G's default failure
(abort quoting the condition), which is what an unrepaired gate does today.
Exhaustion never counts as G passing.

**Verification and order rules.** On the exhaustion path G has not passed,
so an order rule `verify#g before write#x` must fail any write reachable
on that path. The existing P1 analysis already treats a gate as counting
only when it passes; exhaustion becomes one more non-passing exit.

**Approval and asks.** A declined confirmation is an answer, not a failure
to repair (SPEC Section 12); a repair loop must not re-ask a decision the
user declined. A decision `ask` inside a repair loop should be flagged:
each attempt would re-ask (the over-asking failure, in loop form).

**Runtime.** A count is enforceable: the guard can count `verify`
operations per typed ID per session, and the ledger can show attempts.
"No progress" is checkable only when the evidence is an exec result
(compare output digests); otherwise it is a self-report. External
conditions stay agent judgment.

## Options

- **A. No new syntax.** Make termination visible and checked:
  `check --audit` lists every loop with whether its repair has a reachable
  exit; the compiler inventories each recovery requirement's termination
  condition (case 2) and lowers it as the existing blocker branch
  (`if <failure persists with the same evidence>: return #blocked ...`);
  invented loops (case 3) become reverse-traceability findings.
- **B. A construct** (count and/or no-progress with an exhaustion block),
  with the semantics above.

Recommendation: A now. The evidence has zero case-1 sources, case 2 is a
condition the current idiom can express, and case 3 is a compiler defect
that B would not fix. A warning on exitless loops would fire on 25 of 29
existing hand-written loops, so start with `--audit` reporting, not a
warning, and revisit after classifying those 25 against their own sources.

## Test plan before any grammar change

1. Classify the 29 hand-written loops against their workflows' own prose
   intent into cases 1-3 (full-stack's flows have source docs).
2. Search further real skills for count-bounded retry language (case 1).
   B is justified only if case 1 appears in real sources.
3. If B proceeds: mutants for counter reset, nested loops, exhaustion
   without a handler, order rules on the exhaustion path, and a decision
   ask inside a loop; guard tests for count enforcement.
