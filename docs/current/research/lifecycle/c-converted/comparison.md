# Conversion comparison: independent vs shipped

Compared `my-review.json` (this directory) against
`examples/optimization/review.json` (shipped with the converted skill).

## Agreement (6/6 requirement areas preserved by both)

Purpose, scope, defect selection, finding evidence, independent
verification, and report structure all survive in both conversions.
Both keep the never-rules (no editing/executing/publishing, no invented
evidence) and the reachable-failure-case standard.

## What my first draft dropped (caught by comparison)

My initial conversion carried severity and the oracle criterion only as
the adjectives "impact-ordered" and "independent verification advice".
The shipped conversion's appendix pins the severity rubric (high =
reachable breach/data loss/core failure; medium = limited; low = minor),
the independent-oracle criterion (specification/caller contract, current
output is not an oracle), the explicit no-findings statement, and the
unexecuted-tests note. I added an equivalent appendix after the
comparison. Detection worked exactly as intended: the shipped artifact
was the oracle for my draft's omissions.

## What the shipped conversion leaves implicit

Its order coverage is structural only: the flow has no `order:` rules,
so sequencing (read before generate, verify before report) rests on
written sequence, not a checked rule. Mine is identical here -- neither
conversion makes the pipeline order machine-checked. An `order:` rule
such as `verify#evidence before return#report` would require typed
return statements the vocabulary does not provide, which is itself a
finding about the DSL: terminal steps cannot be order-anchored.

## Prose review vs logic review (same reviewer, same subject)

Both reviews found the injection, excluded the style nit, and recorded
limitations and unrun checks. The logic review did not find more, but it
was checkable: every requirement in the intent maps to a flow statement,
a contract line, or an appendix line, while the prose review's
completeness rests on the reviewer's discipline. The value demonstrated
is verifiability of the procedure, not superior findings.
