# Decision-Preserving Context Compression (DPCC)

Working formulation, recorded 2026-11-17 from the user's proposed formula
and subsequent complete explanation. This is a research
design, not a replacement for the existing main-run preregistration.
Implementation: `skillwren select`, schema 1, in
`src/skillwren/selection.py`. Interpretation and open questions are in
[NOTES.md](NOTES.md).

## Scope and ownership

DPCC seeks the least expensive information-handling strategy that preserves
required decisions across evaluated models and task groups. If compression
is not demonstrably eligible, do not compress: use an independently
certified baseline or abstain.

Select a representation policy sigma from a finite, fixed candidate set
Sigma_N. A policy may eventually choose which skill units to load, retain,
resolve, or compress over a trajectory. Version 1 selects whole candidates
from supplied observations; it does not generate policies, run agents,
change guard permissions, or deploy a selected artifact.

The study owner fixes candidates, cell definitions, requirement thresholds,
loss bounds, sample size, and confidence level before certification data
are observed. The evaluator owns observations and structural manifests.
The selector validates those inputs and owns only its derived JSON report.
It cannot authenticate the evaluator's declarations or prove IID sampling.
Reports bind the input bytes with SHA-256 when called through the CLI.

## Population target

Let H = M x G contain all required model-group pairs and let
K = {safety, omission, task, proc, sem, anchor, fidelity}. Each configured
requirement has violation indicator V_(k,h)^sigma and tolerance epsilon_k.
Unmeasured requirements remain outside the empirical claim.

\[
J(\sigma)=\max_{h\in\mathcal H}\mathbb E_h[L^\sigma].
\]

The original proposal minimizes J over an empirically certified feasible
set, subject to a worst-cell population CVaR budget, and falls back when
that constrained problem has no feasible candidate. The implementable
selection rule uses upper confidence bounds for unknown population terms:

\[
\widehat{\mathcal F}_\delta=\left\{\sigma\in\Sigma_N:
 \operatorname{Cert}_{\rm structural}(\sigma)=1,\quad
 \max_h U_{k,h,\sigma}\le\epsilon_k\ \forall k\in K_{\rm measured},\quad
 \max_h U_{{\rm tail},h,\sigma}\le B_{\rm tail}
 \right\},
\]
\[
\widehat\sigma\in\arg\min_{\sigma\in\widehat{\mathcal F}_\delta}
 \max_h U_{L,h,\sigma}.
\]

The tail condition is omitted when no tail budget is configured. Empty
empirical feasibility means **no certified candidate**, not proof that the
population problem is infeasible. Version 1 abstains. A certified baseline
may be included as an ordinary candidate; a separate trusted-baseline
fallback and its operational certification remain future work.

## Selection-valid finite-sample bounds

Assume fixed candidates and fixed n, IID observations within each cell,
violation indicators in {0,1}, and known 0 <= L <= L_max. No independence
between requirements, candidates, or cells is needed for the union bound.
Do not reuse certification observations to invent new candidates or stop
early after a favorable result. Adaptive proposals require fresh holdout
data or a separately justified sequential method.

For N candidates, H cells, K measured requirements, allocate equal failure
probability eta = delta/Q, where Q = N H (K + 1 + I_tail). Allocation includes
all declared candidates, including structurally rejected candidates and
empty cells. It does not shrink after inspecting outcomes.

\[
 \gamma(n,\eta)=\sqrt{\frac{\log(2/\eta)}{2n}},\qquad
 U_{k,h,\sigma}=\min(1,\widehat p_{k,h,\sigma}+\gamma),\qquad
 U_{L,h,\sigma}=\min(L_{\max},\overline L+L_{\max}\gamma).
\]

These are conservative two-sided Hoeffding intervals, using their upper
ends for selection. Version 1 reports lower ends too, but does not equate
failure of an upper bound with proof of a violation. See
[Hoeffding (1963)](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf).
With probability at least 1-delta, all the configured population means
are covered simultaneously, under the declared assumptions.

For 0 < nu < 1 interpreted as a confidence level:

\[
 \operatorname{CVaR}_{\nu,h}(L)=\inf_{z\in\mathbb R}
 \left[z+\frac{\mathbb E_h[(L-z)_+]}{1-\nu}\right].
\]

The empirical value uses fractional mass at the tail boundary, including
for discrete distributions. This is the
[Rockafellar-Uryasev formulation](https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf).
For bounded loss, the DKW-Massart CDF band with radius gamma gives

\[
 U_{{\rm tail},h,\sigma}=\min\left(L_{\max},
 \widehat{\operatorname{CVaR}}_{\nu,h}
 +\frac{L_{\max}\gamma(n,\eta)}{1-\nu}\right).
\]

Derivation: for any z in [0,L_max], the expected excess is the integral
of the survival function from z to L_max; a uniform CDF error gamma changes
this integral by at most L_max gamma. Divide by 1-nu and take the infimum
over z. This is intentionally loose for small n or extreme nu. The
[DKW-Massart bound](https://doi.org/10.1214/aop/1176990746) is two-sided with
failure probability at most 2 exp(-2 n gamma^2).

## Structural invariants and decision deficiency

The proposed execution-layer obligations, for every step t, are:

\[
\operatorname{Priv}(C_t)\subseteq\operatorname{Priv}(X,T_t),\qquad
\operatorname{ReqPriv}(X,T_t)\subseteq\operatorname{Priv}(C_t),\qquad
\operatorname{ReqDeps}(C_t)\subseteq C_t\cup\operatorname{Resolved}_\sigma(X,t).
\]

Version 1 checks these set inclusions against explicit step manifests.
Privilege atoms must already encode resource, action, scope, and conditions
where relevant; strings such as `write` alone do not establish authority.
Dependencies must be stable node IDs. Resolved nodes must be available at
that step, not merely scheduled for later. Missing manifests are
uncertified. Failed inclusions reject the candidate. A supplied manifest
is evidence about declared structure, not execution-layer enforcement or
proof that the extracted privileges and dependencies are complete.

The stronger proposed certificate is:

\[
\Delta_{\mathcal D}(X\Rightarrow C_\sigma)
=\sup_{\ell\in\mathcal D}\{R_\ell(C_\sigma;T)-R_\ell(X;T)\}
\le\varepsilon_{\mathcal D},\qquad
R_\ell(Z;T)=\inf_{\pi_Z}\mathbb E[\ell(\pi_Z(Z,T),Y)\mid T].
\]

This needs a specified decision class, outcome distribution, admissible
decision rules, and a theorem or measurement design bounding the supremum.
Finite task compliance is not that theorem. It is not implemented as a
certificate. Along Z_0 -> ... -> Z_m, telescoping gives a sum of per-step
deficiency tolerances only when the same decision class, task conditioning,
and risk definitions apply at every link.

## Trajectory model

The user's follow-up supplies the trajectory objective:

\[
L^\sigma=\sum_{t=0}^{\tau-1}c(b_t,u_t).
\]

Here b_t is the information state and u_t is the chosen action. A proposed
state representation and one possible cost decomposition are:

\[
b_t=(\mathrm{context}_t,\mathrm{cache}_t,\mathrm{resolvedDeps}_t,
 \mathrm{authorityEvidence}_t,\mathrm{history}_t),\qquad u_t\sim\sigma(\cdot\mid b_t),
\]
\[
c(b_t,u_t)=c_{\rm tokens}(b_t,u_t)
 +\lambda_{\rm latency}c_{\rm latency}(b_t,u_t)
 +\lambda_{\rm compute}c_{\rm compute}(b_t,u_t).
\]

Actions may retain, retrieve, compress, resolve dependencies, verify,
repair, cache, execute, or abstain. Failure consequences, calibration, or
terminal costs may be included in c when expressed on the same scale.
Units, nonnegative weights, horizon and a valid
L_max must be fixed before data collection. Hard requirement constraints
remain separate from this scalar objective. The state is not asserted
Markov or sufficient without evidence. Version 1 consumes an already
computed bounded trajectory loss with an explicit `loss_unit`; the tail
budget uses that same unit. It does not implement these dynamics. A cap on
observed samples alone does not establish a population bound on recovery
cascades; L_max needs an independent operational justification.

For illustration only, 5,000 tokens of full context can cost more than
1,000 initial + 500 retrieval + 200 verification tokens. A 30,000-token
recovery cascade must also enter the latter policy's trajectory loss.
Neither example is benchmark evidence. An omitted approval condition
fails a hard requirement even if its removal makes the loss smaller.

## Error decomposition: conditional theorem target

The proposed form is retained as:

\[
J(\widehat\sigma)-J(\sigma^\star_{\rm all})
\le G_{\mathcal C,\gamma}+\Gamma_{\rm search}+2\gamma_L+\Gamma_{\rm shift}.
\]

For a nonempty empirical feasible set, define G_(C,gamma) as the gap between
the best population J within that set and the best admissible policy in
the full class. This includes candidate restriction and conservative
feasibility shrinkage. With a uniform objective estimation error gamma_L
and an approximate empirical minimizer within Gamma_search, the usual
add-and-subtract argument gives the first three terms. Version 1 searches
its finite set exactly (Gamma_search = 0), but minimizes upper bounds;
the 2 gamma_L argument applies because those upper bounds lie between J
and J + 2 gamma_L on the simultaneous estimation event.

If deployment and evaluation objectives differ uniformly by at most s,
comparing both endpoints adds Gamma_shift = 2s. Deployment constraint
validity additionally needs risk-shift margins; an objective shift term
alone does not preserve safety. The comparator must satisfy the same
population requirements and tail budget. No finite comparator gap is
claimed when the empirical feasible set is empty. G, deficiency, and shift
are not estimated by the implementation, and no numeric regret certificate
is emitted.

## Choices, assurance, and acceptance

Keep Python 3.9+ and the standard library. A JSON manifest plus deterministic
JSON output fits the existing CLI. Use simple, conservative concentration
bounds before adding tighter estimators. Structural and empirical reports
have separate fields. Input errors return exit 2; a valid study with no
certified candidate returns exit 1 and abstains; selection returns exit 0.

Assurance screen: verification, CLI usability, and maintainability raised;
no services, paid calls, execution permissions, deployment, or persistence
migration. Reports are recomputed on each call; no hidden mutable state.

| Claim | Failure mode | Owner/control | Acceptance |
|---|---|---|---|
| Conservative selection | multiplicity or tail mass wrong | selection bounds | analytic boundary and worst-cell tests |
| Missing data abstains | errors counted as passes or filtered samples | schema/evaluator | missing-cell and execution-error tests |
| Structural rejection | lost required authority or unresolved dependency | manifest checker | all three inclusion failures |
| Usable, stable CLI | malformed input crashes or overwrites input | CLI parser/report | subprocess exit-code and JSON tests |
| Existing tools preserved | command dispatch or packaging regression | CLI registry | full unittest suite, mutation sweep, wheel smoke |

Ready: notes, schema, structural set checks, finite selection, tail bound,
fallback, and tests. Deferred: adaptive/sequential search, authenticated
manifest extraction, trajectory control, general decision deficiency,
distribution-shift estimation, and a certified operational baseline.
The existing main run is exploratory evidence for this new design; no
post-hoc thresholds or independence declarations turn it into a
preregistered certification study.

## Possible Wilderbeast connection

The user's intended relationship is that DPCC supplies the optimization
problem and Wilderbeast could represent it as a typed expression DAG with
min/max, expectation, constraints, rewrites, proof checks and
counterexamples. Such a backend would need explicit tensor/operation
denotations and would return a verified transformation or unresolved proof
obligation. This is a future research interface. No Wilderbeast capability
was inspected or integrated here, and its reported early mathematical IR
is not treated as a DPCC theorem prover.
