# Skill C outcomes (prose import -> independent conversion -> review)

Converted `examples/optimization/original.md` (56 lines of prose) to a
check-clean fragment flow plus an appendix, with a line-mapped review
(`my-review.json`) and a comparison against the shipped conversion.

## Steps 1-4: import, convert, validate, explain, approve

- `check --fragment`: clean. `explain-workflow` saved as
  `explanation.txt`; states the gate, branches, and that nothing is
  enforced (no guard verbs bound to a policy).
- `approve --by lifecycle-probe` (no policy -- read-only skill):
  approved with `#evidence` uncovered. The uncovered list is the
  activation signal working as designed: approval alone grants no
  capability, and here there is nothing to grant.

## Steps 5-8: invoke on a real disposable repository

Subject with a reachable injection (`caller.py` CLI input into
`shell=True`) and a style-only nit, executed twice by the same
reviewer:

- Prose run (`prose-review.md`, original only): found the injection
  with location/trigger/consequence, excluded the nit, recorded
  limitations and unrun checks.
- Logic run (`logic-review.md`, converted flow only): identical
  findings. Ledger run `skill-c-review`: `valid, complete` against
  required milestone `report returned`.
- The logic review did not find more. What it adds is checkability:
  every intent requirement maps to a flow statement, contract line, or
  appendix line (`comparison.md`), while the prose review's
  completeness rests on reviewer discipline.

## Conversion fidelity (the differentiator test)

`comparison.md`: my first draft dropped the severity rubric, the
independent-oracle criterion, the explicit no-findings statement, and
the unexecuted-tests note -- all present in the shipped conversion's
appendix. The comparison caught all four; the appendix now carries
them. Both conversions leave pipeline order (read before generate,
verify before report) to written sequence rather than a checked rule,
because terminal steps have no typed-ID form for `order:` rules --
itself a DSL finding.

## Step 10

Appending `# probe` invalidated approval (exit 1, `file changed since
approval`); restoring the canonical bytes returned `approved: true`
with the original timestamp.

## Guarantee accounting

- Statically checked: gates, bindings, never-rules, appendix presence.
- Runtime-enforced: nothing -- correctly, since nothing is written.
- Agent-dependent: everything about thoroughness. The ledger proves the
  steps ran and the report exists; it cannot prove the reviewer looked.
