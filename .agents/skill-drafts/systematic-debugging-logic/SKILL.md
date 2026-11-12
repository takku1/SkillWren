---
skill: systematic-debugging-logic
name: systematic-debugging-logic
description: Use when encountering any bug, test failure, or unexpected behavior: reproduce consistently, trace root cause, test one hypothesis at a time, and verify the fix.
version: 0.4.1
purpose: Find root cause before fixing, and prove every fix with a failing test.
accepts:
  symptom: { type: Text, required: true }
produces:
  resolution: { type: Text }
owns-when:
  - user reports a bug or test failure
  - user wants help debugging unexpected behavior
  - user asks why a test keeps failing
requires:
  debug-issue: [symptom exists]
flows: [debug-issue]
authority:
  user-decides: []
  system-decides: [what the root cause is, whether the reproduction is consistent, whether the fix resolves the symptom]
  system-may: [suggest the smallest hypothesis test]
  system-must-not: [propose fixes before root cause investigation, attempt a fourth fix without discussion]
effects:
  reads: [working tree]
  creates: [repro]
  mutates: [code]
risk: medium
cost: moderate
budget: { header: 400, body: 2500 }
---

# Systematic Debugging (logic)

Side-by-side pilot of the prose systematic-debugging skill: the same
four phases, enforced as gates instead of stated as prose.

```contract
resources:
  tree:
    path: working tree
    access: read
  repro:
    path: repro-script
    access: create
  code:
    path: fixed code
    access: read+create
always:
  find root cause before attempting fixes
  prove each fix with a failing test first
never:
  propose fixes before root cause investigation
  attempt a fourth fix without architecture discussion
```

```logic
debug-issue:
  require symptom exists
    otherwise:
      abort with "A symptom is required: what failed, and where. Nothing changed."

  read failure context for {symptom} from tree as evidence
    otherwise:
      abort with "Could not read the failure context; nothing changed."

  verify symptom is reproducible
    otherwise:
      ask user for reproduction steps as symptom
      retry

  label investigate:

  read recent changes from tree as changes
  read working example from tree as example
  read reference implementation from tree as reference
  generate differences between {example} and {reference} from evidence as gaps
  generate root cause hypothesis for {changes} from gaps as hypothesis

  if system spans multiple components:
    generate per-boundary enter-exit-state probe from evidence as probe
    show probe

  verify hypothesis explains the evidence
    otherwise:
      discard hypothesis
      return to investigate

  if cause is environmental or external:
    generate handling and monitoring plan from evidence as handling
    show handling
    return handling as resolution

  generate smallest failing test from hypothesis as repro
  save repro as repro-script
  verify test fails as predicted
    otherwise:
      discard repro
      return to investigate

  apply hypothesis with evidence as fix
  write fix with code

  verify fix resolves symptom
    otherwise:
      discard fix
      if recent fixes reveal coupling or new symptoms:
        abort with "Fix attempts show coupling or new symptoms; stopping for architecture discussion. Changed: repro script and attempted fixes; sources otherwise unchanged."
      return to investigate

  return fix as resolution
```

## Appendix: debugging guidance

Iron law: no fixes without root cause investigation. The four phases in
order: investigate (read errors, reproduce, check changes, gather
evidence), pattern analysis (working examples, full reference reads,
differences, dependencies), hypothesis (one theory, smallest test,
verify), implementation (failing test first, single fix, verify).

Pattern analysis before hypothesizing: find working code similar to
what is broken, read the reference implementation completely, list
every difference however small, and check dependencies and
assumptions. A hypothesis drawn from evidence plus comparisons beats
one drawn from the diff alone, especially when the bug predates
recent changes.

Boundary probe checklist, per component boundary: log what data
enters, log what data exits, verify environment and config
propagation, and check state at the layer. Run once to see where it
breaks, then investigate that component. Treat the host-vs-guest
split as a boundary whenever a repro works on one side only.

Backward tracing for deep-stack bugs: observe the symptom, find the
immediate cause, ask what called this, inspect the values passed, and
keep climbing to the original trigger; fix at the source, never where
the error appears. When manual tracing stalls, log before the dangerous
operation (directory, cwd, environment, stack) and capture the trace;
bisect test files one by one to find polluters.

Defense in depth after a fix: validate at entry (reject invalid input),
in business logic (check the operation makes sense), with environment
guards (refuse dangerous operations in the wrong context, such as
destructive commands outside temp dirs during tests), and with debug
instrumentation for forensics. Test each layer by trying to bypass the
one above it.

Condition-based waiting for flaky async tests: poll the actual condition
with a fresh getter roughly every 10ms and fail with a clear timeout
error instead of sleeping a guessed duration. Sleep only when testing
timing behavior itself, and document why.

Pressure discipline: simple-looking issues and emergencies still get
the full process, the test comes before the fix, one change at a time,
and an unread reference stays unread — never adapt a pattern from
memory. When you do not understand something, say so plainly instead
of guessing. Partner phrases that mean return to investigation: is
that not happening, will it show us, stop guessing, ultra-think this,
we are stuck.

Full technique docs, examples, and pressure-test drills live with the
prose original in the sibling systematic-debugging skill directory.
