# Working notes: DPCC and empirical sufficiency

## 2026-11-17: user's formula and implementation decision

Preserve the central proposal: minimize worst model-group expected loss
within a certified feasible set; constrain worst-cell CVaR; otherwise use
a certified baseline or abstain. Separate structural authority/dependency
invariants from a decision-class deficiency bound, and separate candidate,
search, estimation and distribution-shift error.

The initial equations were partly cut off. The user's subsequent full
explanation names the project **Decision-Preserving Context Compression
(DPCC)** and clarifies the total cost as sum_t c(b_t,u_t), covering the
complete information-handling strategy. [FORMULATION.md](FORMULATION.md)
incorporates that clarification, marks additional working choices, and
narrows what the implementation can honestly claim.

Decisions for version 1:

- Bound every configured risk in every required cell, with selection-valid
  allocation across the entire fixed candidate set. Keep hard risk limits
  separate from the loss objective.
- Include a conservative bounded-loss CVaR option. Lack of evidence is
  `uncertified`, not mathematical infeasibility. Abstention is explicit.
- Check declared privilege/dependency inclusions, but do not call them
  enforcement, authenticated extraction, or semantic-equivalence proofs.
- Do not replace deficiency with task success or invent a numeric regret
  bound. These remain research obligations.
- Require fixed sample sizes and IID-within-cell declarations. Adaptive
  generation needs independent certification data. Correlation across
  requirements and candidates is allowed; correlated repeats within a cell
  do not become IID merely because they are different calls.
- Missing runs, usage limits, malformed metrics and unknown cells cannot
  certify a candidate. Do not calculate confidence bounds on a filtered
  subset of completed attempts.

The historical preregistration remains unchanged. Its five-repeat 4/5 rule
is distinct from this new confidence-bound selector. The existing incomplete
150-attempt run cannot establish rare-event safety, decision deficiency,
or a minimum sufficient representation under the new rule.

Open questions: the appropriate decision class; trustworthy extraction of
effective scoped privileges and dependencies; simultaneous coverage under
adaptive generation; rare-event sample complexity; whether the tail loss
should be cost, harm, or separate budgets; and operational baseline
certification. A single scalar loss must not let cheap tokens compensate
for violation of a hard obligation.

Wilderbeast is the proposed future mathematical analysis engine for typed
expressions, legitimate rewrites and counterexamples. Its current
capabilities are user-reported, not independently verified in this work.
There is no integration or dependency on it in the empirical selector.

## Implementation evidence (2026-11-17)

Implemented `skillwren select` with strict schema-1 input, declared
structural set checks, simultaneous bounded-mean risk/objective intervals,
optional bounded-loss CVaR intervals, worst-cell selection, and explicit
abstention. Missing or error-containing cells have no confidence bounds.
The output records thresholds, cost units, allocation, input hash and
unimplemented guarantee classes.

Executed checks: 297 repository tests passed (3 skipped), including 21
selector tests; 31 existing mutation controls had no misses or deviations.
After adding stronger tail and error-report assertions, the selector tests
passed again. The initial nonisolated offline wheel attempt lacked a
build tool. An isolated build succeeded, followed by a successful offline
rebuild using locally cached build requirements. Both selection and
abstention passed through the packaged CLI in a subprocess outside the
checkout. These are implementation checks and synthetic examples, not
empirical DPCC performance or semantic-preservation results.

Full-stack run record: `20261117-180638-d9eb0b` (local `.git` evidence,
not a portable certification artifact). No agent evaluations or paid
provider calls were run for this change.
