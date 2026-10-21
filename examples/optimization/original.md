---
name: evidence-review
description: Review a supplied code change for consequential defects with source evidence, uncertainty, and concrete verification advice.
---

# Evidence-based code review

## Establish scope

Start by reading the project's instructions, the requested target, and the
diff. Read the relevant callers or dependencies when they are necessary to
understand what the change can affect. Keep the review focused on the supplied
change. Do not turn a request for a review into permission to implement a fix,
refactor unrelated code, commit, or publish anything. Respect the project's
existing conventions rather than imposing a preferred style of your own.

## Find consequential defects

Look for defects that can affect correctness, security, or observable behavior.
A proposed finding must describe a credible failure case in the code under
review, not merely a general concern about a pattern that might be dangerous
somewhere else. Check the necessary callers before asserting that an input is
reachable or that a value is invalid. Leave style-only preferences out of the
findings unless the user explicitly requested a style review.

## Support each finding

For each confirmed finding, identify the relevant file and line span, describe
the input or state that triggers the failure, and explain its consequence.
Distinguish what the source establishes from what would need a runtime test.
Do not invent execution traces, test outputs, requirements, or environmental
assumptions to make a finding look complete. If you cannot establish an
essential fact, label the concern unverified and name the missing evidence
instead of presenting it as a confirmed defect.

## Suggest useful verification

Recommend a regression test that would distinguish the intended behavior from
the identified defect. Explain the independent specification, caller contract,
or other source for its expected result; the implementation's current output
alone is not an oracle. This review does not execute commands. Clearly say
that suggested checks were not run. A test recommendation is a proposed way to
verify a finding, not evidence that the bug has already been reproduced.

## Report results

Return a concise summary followed by confirmed findings ordered by impact.
Use high severity for a reachable security breach, data loss, or core behavior
failure; medium for a limited functional failure; low for a minor consequential
defect. Explain the impact rather than assigning severity from a keyword alone.
Each finding includes source location, trigger, consequence, and a minimal
correction direction, plus its verification suggestion. Put unverified concerns
and missing evidence in a separate limitations section. If there are no
confirmed findings, say so explicitly; that does not establish that the change
is correct. Finish by naming the checks that remain unexecuted. Keep the report
short unless the user asks for more detail.
