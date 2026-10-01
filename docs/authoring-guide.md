# SkillWren Authoring Guide for Logic-First Skills (v0.4.1)

Companion to `SPEC.md` (the contract).
This guide is the procedure: follow it top to bottom to produce a conforming
skill. Audience: humans and agents authoring new skills or converting prose
skills. Prerequisite: read spec Sections 4-8 before your first skill; keep
`../examples/theme-factory.golden.md` open beside you.

## The 12 steps

### 1. Name and purpose

Pick a kebab-case id and one purpose sentence. If the purpose needs "and", you
probably have two skills; split them.

### 2. List flows

Name each runnable flow (verb-phrase, kebab-case). Most skills need 1-3. Each
flow ends in `return` or `abort`. Write the list in the header `flows`.

### 3. Declare inputs and outputs

Fill `accepts` (name, closed-set type, required flag) and `produces`. Every
`required: true` input must be checked by a leading `require` in each flow that
needs it. Every `produces` entry must be returned by at least one flow.

### 4. Duplicate entry preconditions into `requires`

Copy each entry flow's leading `require` conditions into header `requires`
under the flow's name (exact wording; labels and blank lines don't break the
leading run). This is what lets the router check preconditions without loading
your body. Every `required: true` input a flow uses must be gated by a
leading `require <name> exists` (R4) — gate what you consume.

### 5. Write trigger conditions

Add 1-4 `owns-when` lines in plain requester language ("user wants to ...").
Use words a requester would actually type; routing scores content-word overlap
after dropping stopwords.

### 6. Declare authority

Fill the four lists. Rule of thumb: anything with taste or consequence the
user decides; anything checkable the system decides; discretion goes in
`system-may` with explicit bounds; approvals live in `system-must-not`.
Structure is enforced, not just suggested: every `require user ...` must be
dominated by a decision `ask` (no `as`), every decision `ask` must be
followed by a confirmation, and bare `require confirmation` needs a
preceding `ask` (A2). Never write a user gate the flow never asks for.
Decision-`ask` lines must also share at least two content words with a
`user-decides` entry, so phrase entries in the same vocabulary as your asks
(e.g. entry "whether to approve the output" for `ask user to approve
output`). Input-`ask` lines (with `as`) fill `accepts` or locals and need
no mapping. Never mutate before a dismissible ask: writes and mutating
calls belong after the confirmation, or dismissal is not mutation-free
(M1).

### 7. Declare resources and effects

List every file, path pattern, or artifact the skill touches as a resource in
the `contract` block, with `access` and `immutable` flags. Summarize the union
in header `effects`. When in doubt, declare more: undeclared writes are
validation errors, and `mutates` must never be left implicit.

### 8. Write flows in logic blocks

One fenced `logic` block per flow (info string exactly `logic`). Allowed words
only (see reference below). Order each flow: `label` declarations, leading
`require` gates, happy-path actions, `verify` gates before `return`. Keep
conditions one line; push explanation to the appendix.

### 9. Attach local recovery

Every `require`, `verify`, `read`, and `open` that can fail gets an
`otherwise:` block nested directly beneath it (O1) and ending in `retry`,
`return to <label>`, `abort`, or `return` (W9 when it falls through).
`retry` lives only inside such repair blocks (L3) and re-executes the
failed gate. Incorporate accepted repairs into the values they repair
before retrying — a correction that is shown and approved but never
applied is the classic silent bug. Name the failure, repair or re-ask,
never leave a half-mutated artifact: `discard` derived work on the abort
path.

### 10. State invariants

Write the file's `contract` block (`resources:`, `always:`, `never:` in that
order) after you have seen every path. Each invariant must hold on happy
paths, error paths, and dismissals alike. If one needs an exception, add a
scoped `allow` inside the flow, quoting it.

### 11. Set risk, cost, and budgets

Grade `risk`/`cost` honestly (a skill that creates files is at least medium
risk). Keep the default ceilings (header 400, body 2500 cl100k tokens); raise
them only with a comment justifying why, and expect review pushback.

### 12. Validate and review

Run `skillwren check <file>`, fix every error, justify or fix every warning. Then run
the pre-submit checklist below and diff behavior against the prose original
when converting.

## Verb quick reference

Actions: `open, read, write, save, show, ask, generate, apply, run, return,
abort, discard`. Conditions: `if, unless, when, for each`. Gates: `require,
verify, allow`. Invariants: `always, never`. References: `as, with, from`.
Structure: `label, return to, retry, otherwise, return:`.
`{name}` interpolates a bound value into paths.

- `open <resource> as <var>` — open a declared resource for viewing.
- `read <path or description> [from <source>] as <var>` — load content or a
  listing into a binding.
- `write <binding> with <path>` — replace file bytes at a path. `save
  <binding> as <path>` — persist a named artifact.
- `show <binding>` — present a value to the user.
- `ask <whom> to <decision> [as <var>]` — without `as`, transfers a decision:
  pair with a confirmation `require` and a matching `user-decides` entry
  (at least two shared content words). With `as`, binds the answer; the name
  must be an `accepts` entry or a local.
- `generate <description> from <input> as <var>` — creative/semantic step;
  give it appendix guidance when taste matters.
- `apply <spec> with <target> as <result>` — pure in-memory transform of
  a binding, binding the outcome. Never names a resource (read it into a
  binding first); performs no effects.
- `run <flow> with:` / `run <skill>.<flow> with:` — invoke by name with
  `name = value` lines; same-skill calls bind the callee flow's returned
  names into same-named caller bindings. Cross-skill calls are an
  unverified boundary (W8): keep argument names aligned with the callee's
  `accepts`, but know the single-file validator cannot check them.
- `require <condition>` — block until true; aborts quoting the condition
  unless `otherwise:` says otherwise.
- `verify <condition>` — check now and establish evidence; on failure discards
  derived artifacts and aborts unless `otherwise:` repairs.
- `return <binding> as <name>` — single-value return. Multi-value flows use a
  `return:` block with one `name` or `name = binding` line per value. Every
  returned name must be a skill `produces` entry.
- `for each <source> as <var>:` — iterates a `List`-typed binding; the
  variable is read-only and the source collection must not be rebound or
  written inside the loop.
- `retry` — re-executes the failed `require`/`verify` after the repair steps.
- `label <name>:` — declares a jump target; `return to <name>` names one in
  the same flow. Labels don't break the leading-`require` run.

## Header checklist

skill, version, purpose, accepts, produces, owns-when, requires, flows,
authority (all four lists), effects (reads/creates/mutates), risk, cost,
budget. Missing any of these fails validation.

## Skeleton template

Copy, rename, fill. Outer fence is four backticks so the inner fences stay
literal.

````markdown
---
skill: my-skill
name: my-skill
description: One sentence.
version: 0.4
purpose: One sentence.
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: [input exists]
flows: [main]
authority:
  user-decides: [whether to approve the output]
  system-decides: [whether the input is valid]
  system-may: []
  system-must-not: [infer user approval]
effects:
  reads: [input]
  creates: [output]
  mutates: []
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

```contract
resources:
  source:
    path: input
    access: read
  output:
    path: output
    access: create
always:
  leave the source unchanged
never:
  return an unapproved result
```

```logic
main:
  require input exists
    otherwise:
      abort with "An input is required."

  generate result from input as output

  verify output is valid
    otherwise:
      discard output
      abort with "Could not produce a valid result."

  show output
  ask user to approve output
  require confirmation
    otherwise:
      abort with "Dismissed; nothing changed."

  return output as output
```

## Appendix

Keep the result minimal and faithful to the input.
````

## Common mistakes

1. Prose in logic blocks outside conditions — move it to the appendix.
2. `ask` without `require confirmation` — the decision never lands.
3. `requires` wording drifting from flow-entry `require` — copy exactly.
4. Undeclared reads/writes — declare first, write second.
5. `user-decides` entries no flow exercises — delete or use them.
6. Catch-all `owns-when` ("user wants help") — triggers must discriminate.
7. Missing `otherwise` on fallible gates — decide the failure path now.
8. Appendix doing control work — if it branches, it belongs in a flow.
9. `return to` without a `label` in the same flow — declare the target.
10. Multi-value flow with a single-line return — use a `return:` block.
11. `require user ...` with no preceding decision `ask` — ask, then gate.
12. Decision `ask` with no following confirmation — the decision never lands.
13. Write or mutating call before a dismissible `ask` — confirm first.
14. Accepted correction never applied to the value it repairs — apply, then
    `retry`.
15. Required input used but never gated — add the leading `require`.
16. `for each` over a non-`List` binding — iterate lists only.
17. Writing the iterated collection inside the loop — use a new binding.

## Report-producing skills (round-2 learnings)

Report-shaped skills (reviews, audits, summaries) need four content pieces
beyond the generic flow, or runners under-grade and under-report:

1. Severity rubric in the appendix with explicit buckets and examples.
2. A `verify ... rubric ...` gate so grading is enforced, not suggested.
3. Report-shape requirements: fixed section order plus an exact verdict
   taxonomy, enforced by a `verify report contains ...` gate.
4. Praise and question generation as explicit steps, or runners skip them.

## Golden discipline

Golden means validator-clean plus manually semantic-reviewed plus
scenario-tested — never validator-clean alone. The validator proves
structure; it cannot prove that a repair reaches the value it repairs,
that a rubric grades what it claims, or that a report says what happened.
Before blessing an example as golden: read every path for provenance and
authority, confirm each repair is incorporated before its `retry`, and
walk at least one happy path and one failure path by hand.

## Pre-submit checklist

- [ ] Validator clean (zero errors; warnings justified in comments)
- [ ] Header within 400 tokens, body within 2500 (cl100k_base)
- [ ] Every flow returns or aborts on every path
- [ ] Dismissal of any `ask` mutates nothing
- [ ] Every accepted repair is applied before its `retry`
- [ ] Golden diff (conversions): same behavior as prose original
- [ ] Reviewer can answer what it touches, requires, and who decides

