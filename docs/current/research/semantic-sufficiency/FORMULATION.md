# **Decision-Preserving Context Compression (DPCC)**

## **Final Mathematical Specification v23**

Frozen normative specification, recorded 2026-11-17. It supersedes all
earlier policy- and router-centric drafts with a typed semantic
environment, action-gating invariants, evidence-reuse modes, a certified
feasible router family, deterministic selection with refusal/fallback/
denial, certificate-gated deployment, simultaneous coverage with budget
splitting, uniformity complexity, false-certification bounds, deployment
scope, operational cost, deployment metrics, three-valued proof
semantics, and the semantic-compatibility / refinement / rewrite
machinery. Sections I–XXVIII are normative. The implementation mapping
appendix records exactly what `skillwren select` (schema 2) enforces
offline and what remains deployment-side or future work.

Implementation: `skillwren select`, schema 2, in
`src/skillwren/selection.py`. Interpretation and open questions are in
[NOTES.md](NOTES.md).

### **I. Typed Semantic Environment**

\[ \boxed{ \Gamma= \left( \mathcal V_{\mathrm{obs}}, \mathcal V_{\mathrm{choice}}, \mathcal V_{\mathrm{aux}}, \mathcal V_{\mathrm{param}}, \mathcal C_{\mathrm{scope}}, \mathcal C_{\mathrm{risk}}, \mathcal O_{\mathrm{proof}} \right) } \]

\[ \boxed{ \mathcal V_i\cap\mathcal V_j=\varnothing \qquad(i\neq j) } \]

\[ \begin{aligned} &X_t,T_t,z_t\in\mathcal V_{\mathrm{obs}},\\ &z_t=\phi(X_t,T_t),\\ &\sigma,\mathcal R\in\mathcal V_{\mathrm{choice}},\\ &\eta\in\mathcal V_{\mathrm{aux}},\\ &\delta,\epsilon_k^q,B_{\mathrm{tail}}, \delta_{\mathcal D_z},\nu \in\mathcal V_{\mathrm{param}},\\ &q\in\{\mathrm{op},\mathrm{DS}\},\\ &\rho\in\{\mathrm{fresh},\mathrm{split},\mathrm{adaptive}\},\\ &0<\delta<1,\qquad0<\nu<1. \end{aligned} \]

\[ \boxed{ \Gamma\vdash\operatorname{Optimize}(v) \iff v\in\mathcal V_{\mathrm{choice}}\cup\mathcal V_{\mathrm{aux}} \land\operatorname{Authorized}(v,\Gamma) } \]

\[ \boxed{ \begin{gathered} \Gamma\not\vdash\min_{(\sigma,z)},\\ \Gamma\vdash\min_{\sigma\in\Sigma_z},\\ \Gamma\vdash\inf_{\eta\in\mathbb R},\\ \Gamma\vdash\forall z\in\mathcal Z_{\mathrm{cert}}. \end{gathered} } \]

\[ \boxed{ \operatorname{Bound}(z_t,X_t,T_t) \iff z_t=\phi(X_t,T_t) } \]

### **II. Runtime Configuration and Certificate Identity**

\[ \boxed{ \begin{aligned} \mathrm{cfg}_t=\big( &v_{\mathrm{model}}, v_{\mathrm{compressor}}, v_{\mathrm{router}}, v_{\mathrm{monitor}},\\ &\mathrm{prompts}, \mathrm{decoding}, \mathrm{retrieval}, \mathrm{tools}, \mathrm{permissions},\\ &\mathrm{bundleHash}, \mathrm{fallbackGraph} \big)_t \end{aligned} } \]

\[ \boxed{ \mathcal R_z: (X,T,H)\longrightarrow\Sigma_z\cup\{\bot\} } \]

\[ \boxed{ \begin{aligned} \operatorname{ConfigValid}(\mathrm{cfg}) \iff{}& \operatorname{HashValid}(\mathrm{cfg})\\ &\land\operatorname{VersionValid}(\mathrm{cfg})\\ &\land\operatorname{FallbackGraphValid}(\mathrm{cfg}). \end{aligned} } \]

\[ \boxed{ \begin{aligned} \operatorname{ValidCert} (\mathfrak C_{\mathcal R},z,\mathrm{cfg}) \iff{}& \operatorname{CertificateProofVerified}(\mathfrak C_{\mathcal R})\\ &\land\operatorname{ConfigBound}(\mathfrak C_{\mathcal R},\mathrm{cfg})\\ &\land\operatorname{RegimeBound}(\mathfrak C_{\mathcal R},z)\\ &\land\operatorname{EvidenceFresh}(\mathfrak C_{\mathcal R})\\ &\land\operatorname{FallbackLinksVerified}(\mathfrak C_{\mathcal R})\\ &\land\operatorname{ConfigValid}(\mathrm{cfg}). \end{aligned} } \]

\[ \boxed{ \operatorname{CertificateValid}_t(\mathcal R) = \operatorname{ValidCert} (\mathfrak C_{\mathcal R},z_t,\mathrm{cfg}_t) \land \operatorname{DeploymentScopeValid}_t } \]

\[ \boxed{ \operatorname{ValidCert}_t := \operatorname{CertificateValid}_t(\mathcal R_t) } \]

### **III. Inductive Structural Safety**

\[ \boxed{ \mathcal M_{\mathcal R,\mathrm{cfg}} = (S,S_0,\mathcal A,\operatorname{Transition}) } \]

\[ \boxed{ \forall s_0\in S_0:\ I(s_0) } \]

\[ \boxed{ \forall s,s'\in S,\ a\in\mathcal A: I(s)\land \operatorname{Transition}(s,a,s') \implies I(s') } \]

\[ \boxed{ \forall s\in S,\ a\in\mathcal A: I(s)\land \operatorname{Permit}(s,a) \land\operatorname{Consequential}(a) \implies\operatorname{SafeAction}(s,a) } \]

\[ \boxed{ \begin{aligned} \operatorname{InvVerified}(\mathcal R,\mathrm{cfg}) \iff{}& \operatorname{BaseProofVerified}\\ &\land\operatorname{PreservationProofVerified}\\ &\land\operatorname{ActionSafetyProofVerified}. \end{aligned} } \]

\[ \boxed{ \begin{aligned} \operatorname{StructOK}(C,X,T,a) \iff{}& \operatorname{Priv}(C) \subseteq\operatorname{Priv}(X,T)\\ &\land \operatorname{ReqPriv}(X,T,a) \subseteq\operatorname{Priv}(C)\\ &\land \operatorname{ReqDeps}(X,T,a) \subseteq \operatorname{Available}(C) \cup\operatorname{Resolved}_{\sigma}(X,T). \end{aligned} } \]

\[ \boxed{ \begin{aligned} \operatorname{Permit}_t(a) ={}& \operatorname{CertificateValid}_t(\mathcal R_t)\\ &\land\operatorname{MonitorPass}_t\\ &\land\operatorname{StructOK}_t(a)\\ &\land\operatorname{PolicyAllows}_t(a), \quad a\in\mathcal A_{\mathrm{consequential}}. \end{aligned} } \]

\[ \boxed{ \forall a\in\mathcal A_{\mathrm{consequential}}: \operatorname{Execute}_t(a) \implies\operatorname{Permit}_t(a)=1 } \]

### **IV. Decision-Sufficiency Certification**

\[ \boxed{ \mathcal D_{\mathrm{test},z} \subseteq\mathcal D_z } \]

\[ \boxed{ \Delta_{\mathcal D_z}(\mathcal R;P) = \sup_{\ell\in\mathcal D_z} \left[ R_\ell(C_{\mathcal R};T,P) - R_\ell(X;T,P) \right] } \]

\[ \boxed{ \operatorname{LB}_{\mathrm{test},z}(\mathcal R;P) = \sup_{\ell\in\mathcal D_{\mathrm{test},z}} \left[ R_\ell(C_{\mathcal R};T,P) - R_\ell(X;T,P) \right] } \]

\[ \boxed{ \operatorname{LB}_{\mathrm{test},z}(\mathcal R;P) \le \Delta_{\mathcal D_z}(\mathcal R;P) } \]

\[ \boxed{ \begin{aligned} \operatorname{DSCertValid}(\mathcal R,z) \iff{}& \operatorname{UpperBoundProcedureVerified} (U_z^{\Delta,\rho})\\ &\land U_z^{\Delta,\rho}(\mathcal R) \le\delta_{\mathcal D_z}. \end{aligned} } \]

\[ \boxed{ \begin{aligned} \mathcal E_\delta(P) \land\operatorname{DSCertValid}(\mathcal R,z) \implies{}& \Delta_{\mathcal D_z}(\mathcal R;P)\\ &\le U_z^{\Delta,\rho}(\mathcal R) \le\delta_{\mathcal D_z}. \end{aligned} } \]

\[ \boxed{ X\longrightarrow C_{\mathcal R} \not\implies \Delta_{\mathcal D_z}(\mathcal R;P)=0 } \]

### **V. Evidence Reuse and Statistical Validity**

\[ \boxed{ \rho\in \{\mathrm{fresh},\mathrm{split},\mathrm{adaptive}\} } \]

\[ \boxed{ \begin{aligned} \operatorname{EvidenceValid} (\mathfrak R_0^{(\rho)},D_{\mathrm{eval}},\rho) \iff{}& |D_{\mathrm{eval}}|>0\\ &\land\operatorname{EvaluationProtocolValid}\\ &\land\operatorname{ReuseModeValid}(\rho). \end{aligned} } \]

\[ \boxed{ \rho=\mathrm{fresh} \implies D_{\mathrm{eval}}\perp\mathscr H_{\mathrm{select}} } \]

\[ \boxed{ \begin{aligned} \rho=\mathrm{split} \implies{}& D_{\mathrm{select}}\cap D_{\mathrm{eval}} =\varnothing\\ &\land D_{\mathrm{eval}}\perp\mathscr H_{\mathrm{select}}\\ &\land\operatorname{PartitionRecorded}=1. \end{aligned} } \]

\[ \boxed{ \rho=\mathrm{adaptive} \implies \operatorname{AdaptiveCoverageCertified}=1 } \]

\[ \boxed{ \neg\operatorname{EvidenceValid} \implies\operatorname{CertificationDenied} } \]

### **VI. CVaR Tail-Risk Certification**

\[ \boxed{ \begin{aligned} r_{\nu,h}^{\mathrm{tail}}(\mathcal R;P) &= \operatorname{CVaR}_{\nu} (L^{\mathcal R}\mid z,h;P)\\ &= \inf_{\eta\in\mathbb R} \left[ \eta+ \frac{ \mathbb E_P[ (L^{\mathcal R}-\eta)_+\mid z,h ]}{1-\nu} \right]. \end{aligned} } \]

\[ \boxed{ \Gamma\vdash\operatorname{Optimize}(\eta), \qquad \Gamma\not\vdash\operatorname{Optimize}(z) } \]

\[ \boxed{ \mathcal E_\delta(P) \implies r_{\nu,h}^{\mathrm{tail}}(\mathcal R;P) \le U_{\nu,h}^{\mathrm{tail},\rho}(\mathcal R) } \]

\[ \boxed{ \mathcal R\in\mathfrak R_{\mathrm{cert},z}^{q,\rho} \implies \max_{h\in\mathcal H_z} U_{\nu,h}^{\mathrm{tail},\rho}(\mathcal R) \le B_{\mathrm{tail}} } \]

\[ \boxed{ \begin{aligned} \mathcal E_\delta(P) \land \mathcal R\in\mathfrak R_{\mathrm{cert},z}^{q,\rho} \implies \max_{h\in\mathcal H_z} r_{\nu,h}^{\mathrm{tail}}(\mathcal R;P) \le B_{\mathrm{tail}}. \end{aligned} } \]

### **VII. Certified Feasible Router Family**

\[ \boxed{ \begin{aligned} \mathfrak R_{\mathrm{cert},z}^{q,\rho} = \Big\{ \mathcal R\in\mathfrak R_0^{(\rho)}:\;& \operatorname{EvidenceValid}(\mathcal R,\rho)=1,\\ & \operatorname{InvVerified}(\mathcal R,\mathrm{cfg})=1,\\ & \operatorname{ConfigValid}(\mathrm{cfg})=1,\\ & \operatorname{CertificateBundleVerified} (\mathcal R,z,\mathrm{cfg})=1,\\ & \max_{h\in\mathcal H_z} U_{h,k}^{q,\rho}(\mathcal R) \le\epsilon_k^q \quad\forall k\in\mathcal K^q,\\ & \max_{h\in\mathcal H_z} U_{\nu,h}^{\mathrm{tail},\rho}(\mathcal R) \le B_{\mathrm{tail}},\\ & q=\mathrm{DS} \implies \operatorname{DSCertValid}(\mathcal R,z)=1 \Big\}. \end{aligned} } \]

### **VIII. Deterministic Selection**

\[ \boxed{ \operatorname{CandidateID}: \mathfrak R_0^{(\rho)} \longrightarrow\mathcal I } \]

\[ \boxed{ \mathcal I\ \text{totally ordered} } \]

\[ \boxed{ \mathcal R_1\neq\mathcal R_2 \implies \operatorname{CandidateID}(\mathcal R_1) \neq \operatorname{CandidateID}(\mathcal R_2) } \]

\[ \boxed{ \operatorname{TieBreak}(A) = \arg\min_{\mathcal R\in A} \operatorname{CandidateID}(\mathcal R) } \]

\[ \boxed{ \operatorname{SelectOrRefuse} (\mathfrak R_{\mathrm{cert},z}^{q,\rho},\widehat J_z) = \begin{cases} \displaystyle \operatorname{TieBreak} \left( \arg\min_{\mathcal R\in \mathfrak R_{\mathrm{cert},z}^{q,\rho}} \widehat J_z(\mathcal R) \right), & \mathfrak R_{\mathrm{cert},z}^{q,\rho} \neq\varnothing, \\\\[8pt] \mathcal R_\bot, & \text{otherwise}. \end{cases} } \]

\[ \boxed{ \mathcal R_z^\star = \operatorname{SelectOrRefuse} \left( \mathfrak R_{\mathrm{cert},z}^{q,\rho}, \widehat J_z \right) } \]

### **IX. Refusal, Fallback, and Denial**

\[ \boxed{ \mathcal O_z=\Sigma_z\cup\{\bot\}, \qquad \bot\notin\Sigma_z } \]

\[ \boxed{ \mathcal R_\bot,\mathcal R_{\mathrm{deny}}: (X,T,H)\longrightarrow\{\bot\} } \]

\[ \boxed{ \forall X,T,H: \mathcal R_\bot(X,T,H) = \mathcal R_{\mathrm{deny}}(X,T,H) = \bot } \]

\[ \boxed{ \begin{aligned} \operatorname{RefusalVerified}(\mathcal R_\bot) \iff{}& \operatorname{InvVerified}(\mathcal R_\bot,\mathrm{cfg})\\ &\land\operatorname{RefusalOnly}(\mathcal R_\bot)\\ &\land\operatorname{PolicyFree}(\mathcal R_\bot)\\ &\land \forall a\in\mathcal A_{\mathrm{consequential}}: \operatorname{Permit}_{\mathcal R_\bot}(a)=0. \end{aligned} } \]

\[ \boxed{ \begin{aligned} \mathcal F_{\mathrm{verified},t} = \big\{\mathcal R:\;& \operatorname{FallbackReachable}_t(\mathcal R)\\ &\land \operatorname{FallbackCertificateValid}_t(\mathcal R)\\ &\land \operatorname{InvVerified}(\mathcal R,\mathrm{cfg}_t) \big\}. \end{aligned} } \]

\[ \boxed{ \operatorname{VerifiedFallback}_t = \begin{cases} \operatorname{FallbackSelect} (\mathcal F_{\mathrm{verified},t}), & \mathcal F_{\mathrm{verified},t}\neq\varnothing, \\\\[5pt] \mathcal R_\bot, & \mathcal F_{\mathrm{verified},t}=\varnothing \land\operatorname{RefusalVerified}(\mathcal R_\bot), \\\\[5pt] \mathcal R_{\mathrm{deny}}, & \text{otherwise}. \end{cases} } \]

\[ \boxed{ \forall a\in\mathcal A_{\mathrm{consequential}}: \operatorname{Permit}_{\mathcal R_{\mathrm{deny}}}(a)=0 } \]

### **X. Certificate-Gated Deployment**

\[ \boxed{ z_t=\phi(X_t,T_t) } \]

\[ \boxed{ \begin{aligned} G_t(\mathcal R) :={}& z_t\in\mathcal Z_{\mathrm{cert}}\\ &\land \operatorname{CertificateValid}_t(\mathcal R). \end{aligned} } \]

\[ \boxed{ \operatorname{CertificateGate}_t(\mathcal R) = \begin{cases} \mathcal R(X_t,T_t,H_t), & G_t(\mathcal R)=1, \\\\[5pt] \operatorname{VerifiedFallback}_t(X_t,T_t,H_t), & G_t(\mathcal R)=0. \end{cases} } \]

\[ \boxed{ \sigma_t = \operatorname{CertificateGate}_t (\mathcal R_{z_t}^\star) } \]

\[ \boxed{ \neg G_t(\mathcal R_{z_t}^\star) \implies \sigma_t = \operatorname{VerifiedFallback}_t(X_t,T_t,H_t) } \]

\[ \boxed{ \operatorname{VerifiedFallback}_t \in\{\mathcal R_\bot,\mathcal R_{\mathrm{deny}}\} \implies\sigma_t=\bot } \]

### **XI. Simultaneous Statistical Coverage**

\[ \boxed{ \begin{aligned} \mathcal E_\delta(P) = \Big\{ &\forall z\in\mathcal Z_{\mathrm{cert}}, \forall\mathcal R\in\mathfrak R_0^{(\rho)}, \forall h\in\mathcal H_z: \\ & r_{h,k}^{q}(\mathcal R;P) \le U_{h,k}^{q,\rho}(\mathcal R) \quad\forall k\in\mathcal K^q, \\ & r_{\nu,h}^{\mathrm{tail}}(\mathcal R;P) \le U_{\nu,h}^{\mathrm{tail},\rho}(\mathcal R), \\ & q=\mathrm{DS} \implies \Delta_{\mathcal D_z}(\mathcal R;P) \le U_z^{\Delta,\rho}(\mathcal R) \Big\}. \end{aligned} } \]

\[ \boxed{ \Pr_{D_{\mathrm{eval}}} (\mathcal E_\delta(P)) \ge1-\delta } \]

\[ \boxed{ \Pr(E_i(P))\ge1-\delta_i } \]

\[ \boxed{ \sum_{i\in\mathcal I_{\mathrm{coverage}}} \delta_i\le\delta } \]

\[ \boxed{ \Pr\left( \bigcap_{i\in\mathcal I_{\mathrm{coverage}}} E_i(P) \right) \ge1-\sum_i\delta_i \ge1-\delta } \]

\[ \boxed{ \operatorname{JointCoverageProofVerified}(P) \implies \Pr_{D_{\mathrm{eval}}} (\mathcal E_\delta(P)) \ge1-\delta } \]

### **XII. Uniformity Complexity**

\[ \boxed{ \mathcal Q = \left\{ (z,\mathcal R,h,k): z\in\mathcal Z_{\mathrm{cert}}, \mathcal R\in\mathfrak R_0^{(\rho)}, h\in\mathcal H_z, k\in\mathcal K^q \right\} } \]

\[ \boxed{ |\mathcal Q|<\infty \implies \delta_i=\frac{\delta}{|\mathcal I_{\mathrm{coverage}}|} } \]

For bounded independent observations and a finite family of \(N\) relevant scalar risks:

\[ \boxed{ U_i = \widehat r_i+ \sqrt{ \frac{\log(N/\delta)}{2n_i} } } \]

\[ \boxed{ \Pr\left( \forall i\in\{1,\ldots,N\}: r_i\le U_i \right) \ge1-\delta } \]

For infinite families:

\[ \boxed{ \operatorname{UniformCoverageValid} \implies \operatorname{ComplexityBoundVerified} (\mathcal Q,n,\delta) } \]

\[ \boxed{ \operatorname{ComplexityBoundVerified} \in \{ \operatorname{VCBoundVerified}, \operatorname{RademacherBoundVerified}, \operatorname{BracketingBoundVerified}, \operatorname{OtherUniformBoundVerified} \} } \]

### **XIII. False Certification**

\[ \boxed{ \begin{aligned} \operatorname{FalseCert}(P) = \Big\{ \exists z\in\mathcal Z_{\mathrm{cert}}:\;& \mathcal R_z^\star \in\mathfrak R_{\mathrm{cert},z}^{q,\rho} \\ &\land \Big[ \exists h\in\mathcal H_z,\, k\in\mathcal K^q: r_{h,k}^{q}(\mathcal R_z^\star;P) >\epsilon_k^q \\ &\quad\lor \exists h\in\mathcal H_z: r_{\nu,h}^{\mathrm{tail}} (\mathcal R_z^\star;P) >B_{\mathrm{tail}} \\ &\quad\lor \left( q=\mathrm{DS} \land \Delta_{\mathcal D_z} (\mathcal R_z^\star;P) >\delta_{\mathcal D_z} \right) \Big] \Big\}. \end{aligned} } \]

\[ \boxed{ \mathcal E_\delta(P) \implies \neg\operatorname{FalseCert}(P) } \]

\[ \boxed{ \Pr_{D_{\mathrm{eval}}} (\operatorname{FalseCert}(P)) \le\delta } \]

### **XIV. Deployment Scope**

\[ \boxed{ \mathcal P_{\mathrm{cert}} = \left\{ P: \operatorname{ScopeValid}(P,\Gamma) \land \operatorname{AssumptionsValid}(P) \right\} } \]

\[ \boxed{ \begin{aligned} \operatorname{DeploymentScopeValid}_t \iff{}& \operatorname{ScopeMembershipVerified} (P_{\mathrm{deploy},t},\mathcal P_{\mathrm{cert}})\\ &\land \operatorname{ConfigCompatible} (\mathrm{cfg}_t,\mathrm{cfg}_{\mathrm{cert}}). \end{aligned} } \]

\[ \boxed{ \neg\operatorname{DeploymentScopeValid}_t \implies \operatorname{InvalidateCertificate}_t } \]

\[ \boxed{ \begin{aligned} & \Pr_{D_{\mathrm{eval}}} \left( \forall P\in\mathcal P_{\mathrm{cert}}: \mathcal E_\delta(P) \right) \ge1-\delta \\ &\implies \Pr_{D_{\mathrm{eval}}} \left( \exists P\in\mathcal P_{\mathrm{cert}}: \operatorname{FalseCert}(P) \right) \le\delta. \end{aligned} } \]

### **XV. Operational Cost**

\[ \boxed{ \begin{aligned} L^{\mathcal R}(\tau) ={}& L_{\mathrm{compression}}(\tau) + L_{\mathrm{prompt}}(\tau)\\ &+ L_{\mathrm{retrieval}}(\tau) + L_{\mathrm{verification}}(\tau)\\ &+ L_{\mathrm{repair}}(\tau) + L_{\mathrm{monitor}}(\tau)\\ &+ L_{\mathrm{terminal}}(\tau). \end{aligned} } \]

\[ \boxed{ Y_{\mathrm{terminal}} \in \{ \mathrm{completed}, \mathrm{full}, \mathrm{abstained}, \mathrm{refused} \} } \]

\[ \boxed{ L_{\mathrm{terminal}}(\tau) = \begin{cases} c_{\mathrm{completed}},& Y_{\mathrm{terminal}}=\mathrm{completed}, \\ c_{\mathrm{full}},& Y_{\mathrm{terminal}}=\mathrm{full}, \\ c_{\mathrm{abstain}},& Y_{\mathrm{terminal}}=\mathrm{abstained}, \\ c_\bot,& Y_{\mathrm{terminal}}=\mathrm{refused}. \end{cases} } \]

\[ \boxed{ \sum_y \mathbf 1\{Y_{\mathrm{terminal}}=y\} =1 } \]

\[ \boxed{ \widehat J_z(\mathcal R) = \widehat{\mathbb E} [L^{\mathcal R}(\tau)\mid z] } \]

\[ \boxed{ J_{\mathrm{effective}}(\mathcal R;P) = \mathbb E_P[L^{\mathcal R}(\tau)] } \]

### **XVI. Deployment Metrics**

\[ \boxed{ \operatorname{Coverage}_{\mathrm{compressed}} = \Pr_{\mathrm{deploy}} \left( \sigma_t\in\Sigma_{\mathrm{compressed},z_t} \right) } \]

\[ \boxed{ \operatorname{Coverage}_{\mathrm{deployable}} = \Pr_{\mathrm{deploy}}(\sigma_t\neq\bot) } \]

\[ \boxed{ \operatorname{RefusalRate} = \Pr_{\mathrm{deploy}}(\sigma_t=\bot) } \]

\[ \boxed{ \operatorname{FallbackRate} = \Pr_{\mathrm{deploy}} (\sigma_t=\sigma_{\mathrm{full}}) } \]

\[ \boxed{ \operatorname{Coverage}_{\mathrm{deployable}} + \operatorname{RefusalRate} =1 } \]

### **XVII. Three-Valued Proof Semantics**

\[ \boxed{ \operatorname{ProofState}(Q) \in \{ \mathrm{PROVEN}, \mathrm{REFUTED}, \mathrm{UNKNOWN} \} } \]

\[ \boxed{ \operatorname{ProofVerified}(Q) \implies \operatorname{ProofState}(Q)=\mathrm{PROVEN} } \]

\[ \boxed{ \operatorname{CounterexampleVerified}(Q) \implies \operatorname{ProofState}(Q)=\mathrm{REFUTED} } \]

\[ \boxed{ \operatorname{SolverTimeout} \lor\operatorname{MissingEvidence} \lor\operatorname{UnresolvedAssumption} \implies \operatorname{ProofState}(Q)=\mathrm{UNKNOWN} } \]

### **XVIII. Semantic Compatibility**

\[ \boxed{ \begin{aligned} \operatorname{Compatible}(S,S') \iff{}& \operatorname{ScopeCompatible}(S,S')\\ &\land \operatorname{RoleCompatible}(\Gamma,\Gamma')\\ &\land \operatorname{ObjectiveCompatible}(S,S'). \end{aligned} } \]

\[ \boxed{ \mathcal C_{\mathrm{compat}} = \{ \operatorname{ScopeCompatible}, \operatorname{RoleCompatible}, \operatorname{ObjectiveCompatible} \} } \]

\[ \boxed{ \operatorname{CompatibleProven}(S,S') \iff \forall Q\in\mathcal C_{\mathrm{compat}}: \operatorname{ProofState}(Q)=\mathrm{PROVEN} } \]

\[ \boxed{ \operatorname{IncompatibleProven}(S,S') \iff \exists Q\in\mathcal C_{\mathrm{compat}}: \operatorname{ProofState}(Q)=\mathrm{REFUTED} } \]

\[ \boxed{ \neg\operatorname{CompatibleProven} \land \neg\operatorname{IncompatibleProven} \implies \operatorname{CompatibilityStatus}=\mathrm{UNKNOWN} } \]

### **XIX. Common Semantic Domain**

\[ \boxed{ \mathcal U=\operatorname{SemDomain}(S) } \]

\[ \boxed{ M: \operatorname{SemDomain}(S') \longrightarrow \operatorname{SemDomain}(S) } \]

\[ \boxed{ \operatorname{MappingValid}(M,S,S')=1 } \]

\[ \boxed{ \mathcal F_S = \operatorname{Feasible}(S,\Gamma) \subseteq\mathcal U } \]

\[ \boxed{ \mathcal F_{S'}^M = M(\operatorname{Feasible}(S',\Gamma')) \subseteq\mathcal U } \]

### **XX. Refinement Relations**

\[ \boxed{ \begin{aligned} \operatorname{Equivalent}(S,S') \iff{}& \operatorname{Compatible}(S,S')\\ &\land\operatorname{MappingValid}(M,S,S')\\ &\land\mathcal F_S=\mathcal F_{S'}^M\\ &\land\operatorname{ObsSem}(S) =\operatorname{ObsSem}_M(S')\\ &\land\operatorname{ObjectiveSem}(S) =\operatorname{ObjectiveSem}_M(S'). \end{aligned} } \]

\[ \boxed{ \begin{aligned} \operatorname{Tightening}(S,S') \iff{}& \operatorname{Compatible}(S,S')\\ &\land\operatorname{MappingValid}(M,S,S')\\ &\land\mathcal F_{S'}^M\subsetneq\mathcal F_S. \end{aligned} } \]

\[ \boxed{ \begin{aligned} \operatorname{Relaxation}(S,S') \iff{}& \operatorname{Compatible}(S,S')\\ &\land\operatorname{MappingValid}(M,S,S')\\ &\land\mathcal F_S\subsetneq\mathcal F_{S'}^M. \end{aligned} } \]

\[ \boxed{ \operatorname{Redesign}(S,S') \iff \neg\operatorname{Compatible}(S,S') } \]

\[ \boxed{ \begin{aligned} \operatorname{AcceptRefinement}(S,S') \iff{}& \operatorname{CompatibleProven}(S,S')\\ &\land\operatorname{SemanticEquivalentProven}(S,S')\\ &\land\operatorname{VerifyProofObligations}(S,S')=1. \end{aligned} } \]

### **XXI. Exclusive Auditor Verdict**

\[ \boxed{ \operatorname{AuditorVerdict}(S,S',Q) = \begin{cases} \mathrm{REFUTED}, & \operatorname{CounterexampleVerified}(Q), \\\\[3pt] \mathrm{REDESIGN}, & \operatorname{IncompatibleProven}(S,S'), \\\\[3pt] \mathrm{PROVEN\_EQUIVALENT}, & \operatorname{AcceptRefinement}(S,S'), \\\\[3pt] \mathrm{CERTIFIED\_TIGHTENING}, & \operatorname{CompatibleProven}(S,S') \land \operatorname{MappingValid}(M,S,S') \land \operatorname{ProofVerified} (\mathcal F_{S'}^M\subsetneq\mathcal F_S), \\\\[3pt] \mathrm{CERTIFIED\_RELAXATION}, & \operatorname{CompatibleProven}(S,S') \land \operatorname{MappingValid}(M,S,S') \land \operatorname{ProofVerified} (\mathcal F_S\subsetneq\mathcal F_{S'}^M), \\\\[3pt] \mathrm{OPEN}, & \text{otherwise}. \end{cases} } \]

\[ \boxed{ \mathcal F_S=\mathcal F_{S'}^M \implies \operatorname{AuditorVerdict} \notin \{ \mathrm{CERTIFIED\_TIGHTENING}, \mathrm{CERTIFIED\_RELAXATION} \} } \]

### **XXII. Capture-Avoiding Theorem Substitution**

\[ \boxed{ r'=\operatorname{AlphaRename}(r,\Gamma) } \]

\[ \boxed{ B_{r'} \cap \operatorname{FreeVars}(\Gamma) =\varnothing } \]

\[ \boxed{ \operatorname{Typed}(r',\Gamma)=1 } \]

\[ \boxed{ \operatorname{VariableRolePreserved}(r',\Gamma)=1 } \]

\[ \boxed{ \begin{aligned} \operatorname{RenamingCheck}(r,\Gamma) \iff{}& \operatorname{BoundVarsRecorded}(r)\\ &\land \operatorname{FreeVarsRecorded}(\Gamma)\\ &\land \operatorname{CaptureAvoided}(r',\Gamma). \end{aligned} } \]

\[ \boxed{ \begin{aligned} \operatorname{TheoremApplicable}(r',S) \iff{}& \operatorname{RenamingCheck}(r,\Gamma)\\ &\land\operatorname{Typed}(r',\Gamma)\\ &\land\operatorname{PreconditionsVerified}(r',S). \end{aligned} } \]

### **XXIII. Rewrite Authorization**

\[ \boxed{ \begin{aligned} \operatorname{RewriteAuthorized}(S,r,\Gamma) \iff{}& \operatorname{RenamingCheck}(r,\Gamma)\\ &\land \operatorname{Typed}(r',\Gamma)\\ &\land \operatorname{PreconditionsVerified}(r',S)\\ &\land \operatorname{SemanticRelationVerified}(S,r'(S))\\ &\land \operatorname{PolicyAuthorized}(r'). \end{aligned} } \]

\[ \boxed{ \operatorname{ApplyRewrite}(S,r) \iff \operatorname{RewriteAuthorized}(S,r,\Gamma)=1 } \]

\[ \boxed{ \operatorname{DiscoverTheorem}(r) \not\implies \operatorname{ApplyRewrite}(S,r) } \]

\[ \boxed{ \begin{aligned} \operatorname{EquivalentRewriteAuthorized}(S,r) \iff{}& \operatorname{RewriteAuthorized}(S,r,\Gamma)\\ &\land \operatorname{AcceptRefinement}(S,r'(S)). \end{aligned} } \]

\[ \boxed{ \operatorname{UnverifiedRewrite}(r) \implies \operatorname{LedgerStatus}(r)=\mathrm{OPEN} } \]

### **XXIV. Proof Obligations**

\[ \boxed{ \mathcal O_{\mathrm{proof}} = \left\{ \begin{aligned} &\operatorname{VariableRolePreserved},\\ &\operatorname{ScopePreserved},\\ &\operatorname{FeasibleSetRelationVerified},\\ &\operatorname{ObjectivePreserved},\\ &\operatorname{SemanticMappingVerified},\\ &\operatorname{InductiveInvVerified},\\ &\operatorname{CertificateBindingVerified},\\ &\operatorname{CertificateFreshnessVerified},\\ &\operatorname{FallbackLinksVerified},\\ &\operatorname{EvidenceReuseValid},\\ &\operatorname{SimultaneousCoverageValid},\\ &\operatorname{UniformComplexityVerified},\\ &\operatorname{DeficiencyUpperBoundValid},\\ &\operatorname{TailBoundValid},\\ &\operatorname{TieBreakDeterministic},\\ &\operatorname{RefusalSafetyVerified},\\ &\operatorname{DeploymentScopeVerified},\\ &\operatorname{AlphaRenamingValid},\\ &\operatorname{RewritePreconditionsVerified},\\ &\operatorname{RewriteAuthorizationVerified},\\ &\operatorname{PositiveControlsPass},\\ &\operatorname{NegativeControlsPass} \end{aligned} \right\} } \]

\[ \boxed{ \operatorname{VerifyProofObligations}(S,S') = \prod_{o\in\mathcal O_{\mathrm{required}}(S,S')} \mathbf1 \left\{ \operatorname{ProofState}(o)=\mathrm{PROVEN} \right\} } \]

\[ \boxed{ \operatorname{Verified}(S) \iff \forall o\in\mathcal O_{\mathrm{required}}(S): \operatorname{ProofState}(o)=\mathrm{PROVEN} } \]

### **XXV. Normative Deployment Contract**

\[ \boxed{ \begin{gathered} z_t=\phi(X_t,T_t), \\\\[7pt] \mathcal R_z^\star = \operatorname{SelectOrRefuse} \left( \mathfrak R_{\mathrm{cert},z}^{q,\rho}, \widehat J_z \right), \\\\[7pt] \sigma_t = \operatorname{CertificateGate}_t \left( \mathcal R_{z_t}^\star \right). \end{gathered} } \]

\[ \boxed{ \forall a\in\mathcal A_{\mathrm{consequential}}: \operatorname{Execute}_t(a) \implies \operatorname{Permit}_t(a)=1 } \]

\[ \boxed{ \neg G_t(\mathcal R_{z_t}^\star) \implies \sigma_t = \operatorname{VerifiedFallback}_t(X_t,T_t,H_t) } \]

### **XXVI. Normative Statistical Contract**

\[ \boxed{ \operatorname{SimultaneousCoverageValid}(P) \implies \Pr_{D_{\mathrm{eval}}} \left( \operatorname{FalseCert}(P) \right) \le\delta } \]

\[ \boxed{ \begin{aligned} \operatorname{UniformCoverageValid} (\mathcal P_{\mathrm{cert}}) \implies \Pr_{D_{\mathrm{eval}}} \left( \exists P\in\mathcal P_{\mathrm{cert}}: \operatorname{FalseCert}(P) \right) \le\delta. \end{aligned} } \]

### **XXVII. Normative Semantic Contract**

\[ \boxed{ \begin{aligned} \operatorname{AcceptRefinement}(S,S') \iff{}& \operatorname{CompatibleProven}(S,S')\\ &\land \operatorname{SemanticEquivalentProven}(S,S')\\ &\land \operatorname{VerifyProofObligations}(S,S')=1. \end{aligned} } \]

### **XXVIII. Normative Rewrite Contract**

\[ \boxed{ \operatorname{ApplyRewrite}(S,r) \iff \operatorname{RewriteAuthorized}(S,r,\Gamma)=1 } \]

\[ \boxed{ \operatorname{DiscoverTheorem}(r) \not\implies \operatorname{ApplyRewrite}(S,r) } \]

## Appendix A. Implementation mapping (schema 2, offline selector)

The selector enforces the offline, checkable part of this contract.
Each row names the section, what the code does, and what stays outside.

| Spec | Implemented in `skillwren select` | Deployment-side / future |
|---|---|---|
| I (typed environment) | One regime per study; `fixed_candidates` is the R_0 independence claim; study-level `tier` and `reuse_mode` recorded. Joint minimization over $(\sigma,z)$ is impossible by construction; the CVaR $\inf_\eta$ is realized by finite evaluation over loss values. Regime classification $\phi$ is not run. | $\phi(X,T)$ classification; cross-regime optimization is rejected, not supported. |
| II (config/certificates) | Per-candidate `cfg_sha256` provenance recorded in certificates; per-candidate certificate carries regime, tier, bounds, thresholds, input hash, fallback link. | `ConfigValid` conjuncts, freshness checks, bundle verification, monitor/router versions. |
| III (inductive safety) | Declared-manifest proxy for `StructOK`; `inv_verified` attestation gates feasibility (missing/False leaves the candidate inadmissible). | Transition-system proofs, live permit check, `PolicyAllows`, action-specific closure at runtime. |
| IV (deficiency) | DS tier checks the evaluator's $U_z^{\Delta,\rho}$ against $\delta_{\mathcal D}$; LB-never-proves-sufficiency is documented. | `UpperBoundProcedureVerified`; deficiency estimation. |
| V (evidence reuse) | `reuse_mode` fresh/split/adaptive recorded; split requires recorded partition; adaptive requires a coverage certificate; otherwise the study is denied. | The underlying data hygiene itself; independent holdout collection. |
| VI (CVaR) | Fractional-mass empirical CVaR with DKW-Massart radius; $\Gamma\vdash\mathrm{Optimize}(\eta)$ realized by the finite infimum. | Tighter tail estimators. |
| VII (feasible family) | Evidence, invariant, risk, tail, and DS gates; `ConfigValid` and bundle verification recorded as unevaluated (certificates say what they bind, not that the binding was verified). | Config and bundle verification. |
| VIII (selection) | Cost-optimal admissible router: deployment-weighted mean of cell loss estimates (`objective_mean`, uniform by default, optional `cell_weights`); worst-cell upper retained for audit. `CandidateID` is instantiated as (fallback_rank, candidate id), injective by unique names and ranks. Candidate status is `admissible`, never deployment-`certified`: study-admissible and deployment-certified are distinct predicates. | Nothing; complete offline. |
| IX (refusal/fallback/denial) | Verified refusal router selected with `refuse` when the feasible set is empty; `abstain` without one is the offline R_deny counterpart (permits nothing, claims nothing). Refusal requires `refusal_only` and invariant verification. | `FallbackSelect` traversal, `PolicyFree` proof, live fallback reachability. |
| X (certificate gate) | `skillwren certgate` verifies the offline-checkable bundle: winner recomputed from reported bounds, artifact digests, regime and config binding, full fallback-chain walk, invariant attestation. Monitor/policy are caller-asserted flags. | Live gate invocation, per-action `StructOK`, scope invalidation at runtime. |
| XI–XII (coverage) | Finite-family equal allocation $\eta=\delta/Q$ with conservative two-sided Hoeffding intervals (the one-sided spec bound holds a fortiori from the two-sided radius). | Budget-split bookkeeping across heterogeneous estimators; infinite-family uniform bounds. |
| XIII (false cert) | The unconditional bound is exactly what the union allocation targets; no vacuous conditional is emitted. | Nothing; complete as stated. |
| XIV (scope) | Assumptions and regime recorded as the certified scope; deployment distribution is declared out of scope. | Scope-membership verification at runtime. |
| XV–XVI (cost/metrics) | Terminal costs enter through the evaluator's bounded loss samples; $c_\bot$ is recorded on the refusal object. Coverage metrics are not estimated. | Live measurement. |
| XVII (proof states) | Schema violations are REFUTED-style hard failures (exit 2); unattested evidence leaves candidates inadmissible (UNKNOWN-like abstention), never silently admitted. | A general proof-state tracker. |
| XVIII–XXIII (semantics/rewrites) | Not implemented; declared future Wilderbeast interface. Schema keys are disjoint by construction (no capture across requirement/observation namespaces). | Entirely future. |
| XXIV (obligations) | Covered now: `TailBoundValid`, `TieBreakDeterministic`, `RefusalSafetyVerified` (attestation-gated), `DeficiencyUpperBoundValid` (check, not proof), `EvidenceReuseValid`, `SimultaneousCoverageValid` (finite case). Remainder deferred. | As listed in Ready/Deferred below. |

## Appendix B. Choices, assurance, and acceptance

Keep Python 3.9+ and the standard library. A JSON manifest plus
deterministic JSON output fits the existing CLI. Use simple, conservative
concentration bounds before adding tighter estimators. Structural and
empirical reports have separate fields. Input errors return exit 2; a
valid study with no admissible candidate and no verified refusal returns
exit 1 and abstains; selection of an admissible router or of the verified
refusal router returns exit 0.

Assurance screen: verification, CLI usability, and maintainability
raised; no services, paid calls, execution permissions, deployment, or
persistence migration. Reports are recomputed on each call; no hidden
mutable state.

| Claim | Failure mode | Owner/control | Acceptance |
|---|---|---|---|
| Conservative selection | multiplicity or tail mass wrong | selection bounds | analytic boundary and worst-cell tests |
| Missing data abstains | errors counted as passes or filtered samples | schema/evaluator | missing-cell and execution-error tests |
| Structural rejection | lost required authority or unresolved dependency | manifest checker | all three inclusion failures |
| InvVerified gate | unverified router admitted | schema attestation gate | missing/false/malformed attestation tests |
| Evidence modes | reused data certified as fresh | schema evidence gate | split/adaptive denial tests |
| Refusal is verified, not a budget claim | refusal mistaken for risk-certified policy | refusal schema + report wording | refusal selection and abstain-distinction tests |
| Deficiency attestation is checked, not proved | evaluator bound mistaken for theorem | schema tier gate | DS attestation and op-rejection tests |
| Fallback order is explicit and traversable | router cannot order admissible policies | fallback ranks | deployment-order and certificate-link tests |
| Usable, stable CLI | malformed input crashes or overwrites input | CLI parser/report | subprocess exit-code and JSON tests |
| Existing tools preserved | command dispatch or packaging regression | CLI registry | full unittest suite, mutation sweep, wheel smoke |

Ready: notes, schema 2, structural set checks, two-tier finite
selection with fallback ranks, per-candidate certificates,
$\operatorname{InvVerified}$ gating, evidence-mode gating, verified
refusal selection, tail bound, and tests. Deferred: regime
classification, runtime monitor and router (including the live permit
check and certificate gate), scope-membership verification,
coverage-metric measurement, adaptive/sequential search with its own
coverage certificate, authenticated manifest extraction, trajectory
control, deficiency estimation, distribution-shift estimation,
infinite-family uniform bounds, the semantic/refinement/rewrite
machinery (XVII–XXIII, the Wilderbeast interface), and a certified
operational baseline. The existing main run is exploratory evidence
for this design; no post-hoc thresholds or independence declarations
turn it into a preregistered certification study.

## Possible Wilderbeast connection

The user's intended relationship is that DPCC supplies the optimization
problem and Wilderbeast could represent it as a typed expression DAG
(Sections I, XVII–XXIV, XXVII–XXVIII are written as its input contract:
typed variables, three-valued proof states, compatibility and refinement
relations, the exclusive auditor verdict, capture-avoiding substitution,
and rewrite authorization). Such a backend would need explicit
tensor/operation denotations and would return a verified transformation
or unresolved proof obligation. This is a future research interface. No
Wilderbeast capability was inspected or integrated here, and its reported
early mathematical IR is not treated as a DPCC theorem prover.
