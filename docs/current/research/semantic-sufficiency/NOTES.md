# Working notes: DPCC and empirical sufficiency

## 2026-11-18: deployment bridge — `skillwren certgate`

Broader audit asked for the authenticated deployment pipeline (build →
measure → admit → verify → check context → authorize). Implemented the
offline-verifiable core as `src/skillwren/certgate.py` + `tests/test_certgate.py`:
winner recomputed from reported evidence (tampered reports denied),
artifact-byte binding for the selected router and its whole fallback
chain, regime and config binding, invariant attestation, refusal routers
verified but never allowed. `--monitor-pass` and `--policy-allows` are
caller-asserted runtime inputs; per-action `StructOK`, live scope
invalidation, and guard wiring stay deployment-side. Negative tests cover
altered/missing artifacts, revoked evidence, regime and config mismatch,
unbound configs, broken fallback links, and failing monitor/policy.
Verdicts: `allow`/`refuse` exit 0, `deny` exit 1, invalid input exit 2.

## 2026-11-17: re-audit P1s — admissible verdicts, deployment-weighted objective

External re-audit accepted with two corrections. (1) Terminology:
candidate verdicts are study-`admissible` / `inadmissible`, and the empty
outcome is `no_admissible_candidate`. The report no longer says
`certified` about anything the selector itself establishes; only the
normative spec's deployment predicates (`ValidCert`, `RefusalVerified`)
and explicit denials (`not certified`) keep the word. (2) Objective:
optional study-level `cell_weights` (every cell exactly once, sum to 1,
default uniform) weight the mean cost estimate toward the intended
deployment distribution, answering the uniform-weighting caveat. Weights
change only the objective aggregation — per-cell bounds and their
multiplicity cost are untouched — and are recorded in scope and
certificates. Covered by a flip test (weights reverse the uniform
optimum) and fail-closed validation.

## 2026-11-17: objective corrected to mean estimate (audit finding)

External audit confirmed by construction: the selector minimized worst-cell
upper loss while v23 Section VIII specifies argmin J-hat (mean cost
estimate) over the feasible set. Reproduced with flat-0.4 vs split-0.0/0.7
candidates (old rule picks the flat one, J-hat picks the split one).
Fixed: `objective_mean` (uniform mean of cell loss estimates) now drives
selection with (fallback_rank, name) tie-breaks; `objective_upper`
(worst-cell upper) is retained in the report for audit. Safety is
unchanged — it lives in the per-cell requirement, tail, and deficiency
bounds, never in the objective. Covered by a divergence test asserting
both directions (lower mean wins despite a higher worst-cell upper).

## 2026-11-17: v23 frozen spec — typed environment, evidence modes, denial

The user froze v23: a typed semantic environment (obs/choice/aux/param
classes with optimization authorization), config-identity and six-conjunct
certificate validity, inductive structural safety, rho-indexed deficiency
and tail bounds, evidence-reuse modes, the certified router family,
CandidateID deterministic tie-break, refusal/fallback/denial with a
four-conjunct RefusalVerified, certificate-gated deployment, budget-split
simultaneous coverage, uniformity complexity, false-certification bounds,
deployment scope, terminal-cost decomposition, deployment metrics,
three-valued proof semantics, and the semantic/refinement/rewrite/auditor
machinery (the Wilderbeast input contract).

Implemented on top of schema 2 without a version bump (all additive):
study-level `evidence` (`reuse_mode` fresh/split/adaptive; split needs
`partition_recorded: true`; adaptive needs an `adaptive_coverage`
procedure + digest certificate; anything else denies the study);
`refusal_only: true` required on the refusal router; reuse mode recorded
in scope and certificates. Offline `abstain` with no verified refusal is
documented as the R_deny counterpart. Tie-break by (fallback_rank, name)
is the documented CandidateID instantiation. XVIII–XXIII stay entirely
future; XVII is approximated by exit-2/input-error vs inadmissible
handling.

## 2026-11-17: frozen router-certification spec (schema 2, additive)

The user froze the end-to-end router-certification architecture with four
structural corrections: (1) action-gating — every consequential task
action needs ValidCert + MonitorPass + StructOK, not just policy
selection; (2) an unconditional risk-violation bound over the evaluation
distribution instead of a conditional implication; (3) candidate-class
independence — R_0 fixed before data (exactly the `fixed_candidates`
assumption; adaptive evaluation needs a fresh holdout study);
(4) rigorous refusal semantics — empty feasible set defaults to a
verified refusal-only R_bot that is not asserted to satisfy risk
budgets, with c_bot accounted in evaluation loss.

Implemented: per-candidate `inv_verified` attestation is now a
feasibility gate (missing/False leaves the candidate inadmissible with
reason `router:unverified`; non-boolean fails closed); optional
`cfg_sha256` provenance is recorded in certificates; an optional
study-level `refusal` object selects a verified refusal router with
action `refuse` (exit 0) when nothing is admissible, carrying an explicit
no-budget-claim note and costing no multiplicity allocation. The static
manifest check remains the offline proxy for StructOK; action-specific
closure, the live permit check, regime classification, and
coverage-metric measurement stay deployment-side and unimplemented.

## 2026-11-17: regime/tier/admissibility revision (schema 2)

The user's deployment-regime design replaces the v1 single-tier
min-loss formulation. Regimes $z$ partition the deployment space; each
study declares one regime and a candidate portfolio ranked by a strict
fallback preference hierarchy. Feasibility splits into an operational
tier (structure + risk + tail) and a decision-sufficiency tier (plus an
evaluator-attested deficiency upper bound). Membership collapses into
one admissibility predicate per tier; offline compilation emits the
cost-optimal admissible policy plus a fallback-ordered admissible list
with per-candidate certificates for a future deployment-side router.

Deliberate limits, unchanged in spirit from v1:

- The deficiency bound is evaluator evidence, checked against a
  threshold, never estimated or proved by the selector. Under the op
  tier any deficiency attestation is an input error (fail closed
  against silently ignored evidence); under DS a missing attestation
  leaves the candidate uncertified, not invalid.
- Regime classification, the runtime monitor, the certified router,
  and the coverage/cost deployment metrics are specified but not
  implemented. Certificates carry scope and fallback links so a
  router can traverse them later.
- The structural checker already enforces the three v2 invariants as
  declared-set proxies; that mapping is now explicit in FORMULATION.md.

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
