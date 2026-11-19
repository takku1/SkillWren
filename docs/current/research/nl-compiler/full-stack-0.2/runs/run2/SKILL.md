---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation only when asked to build or implement. Use for changes crossing meaningful component boundaries. Not for isolated routine edits, deployment, publication, tool installation, or delegation.
---

# Full Stack (SkillWren logic)

The procedure is the `logic` block below, with its `contract` rules. Execute it exactly; it is the only procedure. Meanings of each `apply` step are under `## Step meanings`.

Applies to changes crossing meaningful component boundaries, starting from a software request, roadmap slice, or prototype. It is not for isolated routine edits. Deliver a connected design across the layers the outcome needs, including native/platform systems. Planning is the default; a request to build or implement authorizes the implementation path within that scope. Deployment, publication, tool installation, and delegation follow their own permissions.

```contract
always:
  keep current state, target state, and migration distinct
  preserve authoritative documents, IDs, and project vocabulary
  preserve settled user decisions and never re-ask them
  treat documentation and mock data as not establishing working behavior
  follow existing task authorization without repeated approval
  keep scope disposition, evidence, and completion as separate axes
  keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct
  mark unexecuted checks as unexecuted
  label every test double with its simulated guarantees, limits, and replacement condition
  list only inspected paths as existing and mark proposed changes as proposed
  keep traceability tables as navigational projections with no independent status fields
  make an investigation package name its question, experiment, and unlocked decision
  reuse existing providers through their contracts at the requested scope
  treat a roadmap row marked done as a recorded claim, not independent verification
  preserve SYSTEM.md contracts, contract markers, and ROADMAP.md as work registry in Recurspec projects
  separate modules only where responsibilities and hidden decisions justify it
  maintain provenance and treat model-generated suggestions as inference
never:
  treat implementation authorization as authorizing deployment, publication, tool installation, or delegation
  expand or replace scope merely because of a discovery
  create a parallel architecture tree
  invent existing files
  substitute a double, empty method, placeholder, or visual demonstration for required behavior
  manufacture probe files, metric values, or formal-proof tags
  install tools or modify a whole tree merely to enable planning
  let an implementation package quietly require the implementer to decide unresolved product semantics
  recommend adoption of a technology candidate whose compatibility is unverified
inputs:
  request, subject, registry, checks, design_docs, cli
order:
  apply explore architecture before write#design
  apply state research question before apply gather sources
  apply connect contracts before apply sequence work
  apply investigate unresolved semantics before apply connect real path
  apply connect real path before apply finish transitions
```

```logic
design-and-deliver:
  require request exists
    otherwise:
      abort with "A software request, roadmap slice, or prototype is required."

  if request does not say whether to build or implement:
    ask user to decide whether to build or implement
    require confirmation
      otherwise:
        apply keep design-only planning with request as design_only

  if the work needs deployment, publication, tool installation, or delegation:
    ask user to grant permission for deployment, publication, tool installation, or delegation
    require confirmation
      otherwise:
        apply mark dependent work conditional with request as conditional_work

  exec readonly inspect applicable instructions and representative code, contracts, tests, and prototypes from subject as inspection
  apply ground scope with inspection as scope
  apply classify dispositions with scope as dispositions

  if ambiguity can be resolved from available evidence:
    apply state consequential assumptions with scope as scope
  else:
    if a missing answer changes the outcome or authority and the user has not already settled it:
      ask user to settle the missing answer that changes the outcome or authority
      require confirmation
        otherwise:
          apply mark dependent work conditional with scope as scope
    else:
      apply proceed on reversible ordinary choice with scope as scope

  if implementation is authorized:
    apply authorize implementation within selected scope with scope as authorization
  else:
    apply keep design-only planning with scope as authorization

  if the subject has governing documents or a work registry:
    exec readonly establish authority from subject as authority
    apply reconcile authority with authority as authority
    verify #claims every roadmap row marked done is checked against the governing architecture and current code from authority
      otherwise:
        apply record unverified claim with authority as authority

  if concepts or relations are ambiguous:
    read references/terminology.md as terminology
      otherwise:
        apply record reference gap with scope as terminology
    apply map terminology with terminology as scope

  if the work is a design delta or the subject uses Recurspec:
    read references/existing-projects.md as existing_projects
      otherwise:
        apply record reference gap with scope as existing_projects
    apply describe design delta with existing_projects as delta
    write #delta delta with design_docs

  if the decomposition is substantial:
    read references/design-method.md as design_method
      otherwise:
        apply record reference gap with scope as design_method
    apply scale design depth with design_method as scope

  if the subject uses Recurspec:
    if cli is available:
      exec readonly Recurspec status from cli as status
      apply orient with status as scope
    else:
      apply report CLI validation not performed with scope as scope
    apply map to contract nodes with scope as scope

  if a commitment is costly to reverse:
    apply record consequences, reversal options, and affected work with scope as commitment
    write #commitment commitment with registry

  apply trace behavior with scope as design
  if the subject is a prototype:
    apply separate prototype appearance from simulated behavior with design as design
  apply allocate authority with design as design
  apply explore architecture with design as design
  apply decide component boundaries with design as boundaries
  apply challenge boundaries with boundaries as boundaries

  if uncertainty could change the design:
    apply state research question with design as question
    apply gather sources with question as evidence
    exec source review from checks as source_review
    verify #sources every material claim rests on a source that was read and inaccessible full text is recorded from source_review
      otherwise:
        apply record unresolved assumption with design as design
    apply record sources with evidence as evidence
    write #sources-record evidence with design_docs
    if a technology candidate is considered for adoption:
      exec compatibility check from checks as compat
      verify #adoption runtime, target architecture, standard-library and allocator requirements, kernel interfaces, graphics and network dependencies, and license are verified from compat
        otherwise:
          apply record unresolved assumption with design as design
          apply withhold adoption recommendation with evidence as evidence
    apply compare alternatives with evidence as choices
    if the choice is consequential:
      apply seek counterexample with choices as choices
    apply record selection with choices as design
    write #selection design with design_docs
    if the consequential claim is supported, conflicts have bounded implications, and more searching is unlikely to change the decision:
      apply stop research with design as design
    else:
      apply record unresolved assumption with design as design

  if evidence changes the interpretation or a dependency lacks a feature:
    apply revisit design with design as design
  if the runtime graph has a delivery cycle:
    apply break delivery cycle with design as design

  apply connect contracts with design as contracts
  apply compose contracts with contracts as contracts
  if the flow needs identity, retries, cancellation, timeouts, ordering, or resynchronization:
    apply specify interaction details with contracts as contracts
  if the implementation is Rust or native:
    apply state resource obligations with contracts as contracts
  apply sequence work with contracts as work_plan
  if the work plan uses temporary test doubles:
    apply label test doubles with work_plan as work_plan
    write #doubles work_plan with registry

  if a quality concern is triggered by the scenario:
    apply quality concerns with design as design
  else:
    apply explain excluded concern with design as design

  exec gap review from checks as gap_review
  verify #gaps no gaps remain within responsibilities, across contracts, or across the outcome from gap_review
    otherwise:
      apply close gaps with design as design
      exec gap review from checks as gap_review
      retry

  if the next increment has usable outcome, contracts, prerequisites, and checks and its consequential decisions are resolved:
    apply label ready with design as readiness
  else:
    apply label conditional with design as readiness

  exec readiness review from checks as readiness_review
  verify #readiness origins, owners, checks, dependency availability, compatible contracts, observable failure paths, and registry links are confirmed from readiness_review
    otherwise:
      apply label conditional with design as readiness

  apply choose smallest artifact set with design as artifacts
  if the subject has no established design structure:
    apply place design under docs/design with artifacts as artifacts
    if implementation is authorized:
      write #docs-design roadmap for implementation tracking with registry
  if the artifact set includes a design brief:
    apply draft design brief with artifacts as brief
    write #design brief with design_docs
  if the artifact set includes a component specification:
    apply draft component specification with artifacts as component_spec
    write #component-spec component_spec with design_docs
  if the artifact set includes an interaction specification:
    apply draft interaction specification with artifacts as interaction_spec
    write #interaction-spec interaction_spec with design_docs
  if the artifact set includes a decision record:
    apply draft decision record with artifacts as decision_record
    write #decision-record decision_record with design_docs
  if the artifact set includes a traceability table:
    apply draft traceability table with artifacts as traceability
    write #traceability traceability with design_docs
  if the artifact set includes work packages:
    apply draft work package with work_plan as work_package
    write #work-package work_package with registry
  write #registry unresolved decisions, evidence needed, affected work, and temporary double links with registry

  if implementation is authorized:
    apply establish handoff with work_plan as handoff
    write #handoff handoff with registry
    apply investigate unresolved semantics with handoff as handoff
    apply connect real path with handoff as slice
    write #implementation slice with subject
    apply finish transitions with slice as slice
    if the slice uses temporary test doubles:
      apply label test doubles with slice as double_record
      write #double-record simulated behavior, unsupported guarantees, real provider, and removal condition of each double with registry
    exec project checks from checks as results
    apply report unavailable environments and unexecuted checks with results as results
    if a runtime claim is uncertain and a relevant check is feasible and useful:
      exec relevant check from checks as claim_check
      verify #claim the relevant check passed from claim_check
        otherwise:
          apply state inspected code and absent execution evidence with results as results
    else:
      apply state inspected code and absent execution evidence with results as results
    verify #acceptance every selected acceptance criterion is satisfied by the real user and system path, not only a first working increment, with relevant failures, independent state, cleanup, and persistence across process restart when required from results
      otherwise:
        if the failure persists with the same evidence or a concrete blocker prevents progress:
          write #blocker unfinished required work, blockers, and next resumption step with registry
          apply compile implementation report with results as report
          return report as report
        apply correction with slice as slice
        write #fix slice with subject
        exec project checks from checks as results
        apply report unavailable environments and unexecuted checks with results as results
        retry
    verify #real-integration no requirement for real integration is closed by a double-based test alone from results
      otherwise:
        write #integration-gap remaining integration work with registry
    if a boundary change is material and a focused diagnostic is useful:
      apply assess information hiding with slice as assessment
    if the subject uses Recurspec and contract edits are accepted:
      exec repository validation from checks as validation
      verify #validation repository validation passed from validation
        otherwise:
          apply record validation gap with validation as validation
    write #resume unfinished required work and next resumption step with registry
    apply compile implementation report with results as report
    write #impl-report report with registry
  else:
    apply compile design report with design as report
    write #design-report report with design_docs

  return report as report
```

## Step meanings

- **ground scope**: identify subject repository, outcome, selected work IDs, constraints, exclusions; keep current, target, migration distinct; trace consequential terms to the request and artifacts; define identity, lifetime, transitions, cardinality, authority, observable completion where ambiguity changes behavior; map aliases without merging distinct entities.
- **classify dispositions**: label each discovery and proposed mechanism required now, existing dependency, unresolved prerequisite, or deferred enhancement. Explain necessary prerequisites; a deferred enhancement does not block required work.
- **authorize implementation within selected scope**: the build request authorizes implementation only within the selected scope, without extra approval; the host must supply repository access, execution tools, runtime; a missing capability is a concrete blocker, not completion.
- **keep design-only planning**: planning is the default; do not implement.
- **reconcile authority**: identify governing architecture, registry, glossary, conventions, code, tests; follow actual flows not directory names; preserve IDs and rationale; when documents disagree, record target design versus observed implementation.
- **record unverified claim**: keep the claim marked as recorded but not verified; do not mark implemented behavior missing because an old brainstorm omitted it.
- **record reference gap**: note that the optional reference was unavailable and continue.
- **map terminology**: use the reference vocabulary and relation names only where useful; preserve equivalent project terms and state the mapping; use stable IDs once several artifacts refer to an element; describe shared providers once; do not flatten relations into a tree.
- **describe design delta**: current behavior, desired behavior, affected boundaries, incremental migration; preserve valuable behavior; give temporary adapters removal conditions; label current and target diagrams.
- **scale design depth**: depth follows uncertainty and risk; the entrypoint owns scope, authorization, evidence, readiness.
- **orient**: use read-only status to orient the relevant tree.
- **report CLI validation not performed**: inspect the artifacts and say CLI validation was not performed.
- **map to contract nodes**: map requirements and components to existing Contract Nodes where appropriate, without assuming one-to-one with work packages; use Recurspec's evidence labels and decision classes unchanged; link concept docs to the owning contract without duplicating interface definitions; coverage suggestions stay proposals.
- **state consequential assumptions**: resolve from evidence, state the assumption, preserve settled user decisions.
- **mark dependent work conditional**: label work depending on the unanswered question or ungranted permission conditional and continue independent work.
- **proceed on reversible ordinary choice**: pick the reversible choice and continue; settled user decisions stay as the user made them.
- **record consequences, reversal options, and affected work**: state consequences, migration or reversal options, and affected work before committing.
- **trace behavior**: define ambiguous terms and observable acceptance criteria; follow trigger, state transitions, result, including failure, retry, cancellation, recovery; for each task name actor, needed information, authorized mutations, observer of completion; explore absent or stale data, duplicates, partial success, crash, restart; resolve conflicting current and target claims. Write requirements as actor, trigger, action, observable result (EARS optional, not an evidence level); never replace concrete behavior with "handles errors appropriately".
- **separate prototype appearance from simulated behavior**: distinguish appearance, demonstrated interactions, simulated behavior; link salient visual requirements; include accessibility and keyboard behavior; for nonvisual tasks use returned values, records, events, device actions, operational signals. A mock array establishes neither persistence nor lifecycle service.
- **allocate authority**: assign cohesive responsibilities, authoritative state, policy, invariants, readers, writers, derived views; one authority per state set or an explicit coordination protocol; architectural authority, resource ownership, team responsibility differ.
- **explore architecture**: iterate activities as evidence changes; do not freeze requirements first.
- **decide component boundaries**: split only where different decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling prevents a coherent increment. Ask per candidate: justifying requirement; owned state, policy, resource, private decision; what consumers must know; whether lifetime, authority, change pressure, failure behavior justify separation; split cost and whether an existing component stays cohesive. Screens, nouns, directories, workflow steps do not dictate components; components do not dictate files, packages, services, processes, teams.
- **challenge boundaries**: weigh a competing quality (information hiding versus latency or transaction colocation); record tradeoffs; map source/build, runtime, protection, deployment independently; a source module gives no fault containment; Rust borrowing does not replace architectural authority.
- **state research question**: record affected requirement, decision, platform constraints, finding that would change the choice; separate conceptual precedent, technology candidate, compatibility evidence (proof of supported interface or executed integration check, with limits). Conceptual precedent is not a compatible dependency. An explicit academic request broadens the corpus and yields a separate cited synthesis.
- **gather sources**: start from supplied sources and repository decisions; current primary docs for unstable versions, APIs, maintenance, licensing, support, pricing; original or author-hosted papers for research claims; snippets are leads, read the source for material claims; record inaccessible full text.
- **record sources**: title, authors or publisher, publication or version date, URL, access date, relevant section, supported claim, applicability limit; distinguish peer-reviewed, technical report, preprint, method description, vendor docs; a standard's abstract does not support a conformance claim.
- **compare alternatives**: compare credible alternatives including the existing approach when viable; no minimum count for settled or trivial decisions; never fabricate alternatives. Investigate choices that could invalidate boundaries; preserve valid existing choices; resolve reuse before custom internals; keep adopted providers opaque beyond contracts; assign fit gaps to owned work.
- **seek counterexample**: for a consequential choice, look for a counterexample or opposing tradeoff that could invalidate the preferred approach.
- **record selection**: selection, alternatives, fit gap, reason, reconsideration conditions; use project classes, else reuse, adapt, build, unresolved; classes do not replace rationale. A user-fixed choice records its origin and investigates integration constraints instead of reopening. Never select or recommend a technology candidate whose adoption was withheld; record it as unresolved.
- **withhold adoption recommendation**: mark the technology candidate as unverified and not recommended for adoption; it may be listed as an alternative with its unmet checks, but not selected, until the runtime, architecture, allocator, kernel, graphics, network, and license checks are verified.
- **record unresolved assumption**: name the unresolved assumption and affected work, continue independent design; a proposed compatibility test is a plan, not evidence; source benchmarks do not transfer automatically.
- **stop research**: stop; do not grow the milestone with optional features.
- **revisit design**: revisit interpretation and architecture; preserve explicit requirements and expose incompatibility and alternatives; remove invented subcomponents when an existing owner supplies the behavior; recheck generated concepts against original evidence before deriving more artifacts.
- **break delivery cycle**: resolve through a stable interface, coordinated increment, or investigation; prefer a real vertical slice with an explicit retirement path for temporary adapters.
- **connect contracts**: use the artifact patterns for consumers, providers, interface semantics, lifecycle, source mappings, checks; match consumer assumptions to provider guarantees or explicit unresolved conditions; describe shared providers once.
- **compose contracts**: check identity, schema and versioning, errors, ordering and delivery, authorization, cancellation, backpressure, recovery; exactly-once effects and lossless streams need supporting mechanisms; a transport acknowledgment does not mean the launch, save, payment, or device action completed; inspect bootstrap, shutdown, reconnection, stale derived state (resume, resynchronize, or report unknown view); choose polling or subscriptions from requirements.
- **specify interaction details**: identity and correlation, retries, duplicates, cancellation, timeouts, event ordering, reconnect and resynchronization; say where a user or operator observes failure; a sequence diagram only supplements semantics.
- **state resource obligations**: borrowing, transfer, synchronization, unsafe obligations where relevant; do not require a new crate merely because a spec exists.
- **sequence work**: link selected requirements, affected responsibilities and paths, prerequisite decisions and contracts, real integration path, checks, closure evidence; prefer bounded end-to-end increments; resolve shared interface work before claiming independence; order interface agreements before dependent integration; different files do not establish independence; mark proposed paths and unavailable prerequisites.
- **label test doubles**: name simulated contract and guarantees, unsupported behavior, real provider, replacement or check condition; doubles do not establish operational integration.
- **quality concerns**: apply when triggered by changed trust or permissions, shared mutable state, durable data, user interaction, platform constraints, deployment and recovery, migration, resource or latency demands. Missing benchmarks call for explicit targets or investigation, not exclusion; label proposed targets and never invent measured performance.
- **explain excluded concern**: explain excluding a material concern without adding unrelated scope.
- **close gaps**: repair gaps within responsibilities (states, errors, resources, lifecycle), across contracts (identity, authority, ordering, failures), across the outcome (complete task and observable result).
- **label ready** / **label conditional**: ready means outcome, contracts, prerequisites, checks usable and consequential decisions resolved; private choices may remain; keep unavailable prerequisites explicit; conditional work is delivered as conditional; sampled scenarios do not establish whole-system completeness. No target depth, artifact count, or per-component readiness checklist.
- **choose smallest artifact set**: smallest set answering the task; reuse project formats and file names; one document for a small scope; separate component or flow files when independently consumed or maintained; field names are prompts, not a schema requiring empty sections.
- **place design under docs/design**: place a design brief plus needed component and flow specs under docs/design/; use the existing roadmap or create one when implementation work needs tracking; preserve other project conventions; no dependency on Recurspec.
- **draft design brief** / **draft component specification** / **draft interaction specification** / **draft decision record** / **draft traceability table** / **draft work package**: draft the named artifact with the contents listed under Artifact patterns.
- **establish handoff**: per bounded increment, selected requirements and acceptance criteria, responsible modules and inspected or proposed paths, dependency contracts and availability, integration order, checks, closure evidence, as a work package in the existing registry; no companion plan.
- **investigate unresolved semantics**: investigate unresolved product or contract semantics before dependent implementation; continue independent work.
- **connect real path**: one real path through the required boundaries; reuse existing facilities.
- **finish transitions**: finish all selected transitions, failures, lifecycle obligations. A first vertical slice is progress, not permission to omit remaining requirements; design readiness does not mean the milestone is complete. Keep composition and presentation from owning domain policy; add packages or services only when dependencies, reuse, isolation, or delivery justify.
- **report unavailable environments and unexecuted checks**: state precisely which environments were unavailable and which checks were not executed, and why; build or type checks and isolated tests alone do not establish integrated behavior; persistence across process restart is exercised when required.
- **state inspected code and absent execution evidence**: say what code was inspected and what execution evidence is absent; avoid expensive whole-project testing for documentation-only comparison.
- **correction**: repair the failing edit; the same failure twice with the same evidence becomes a reported blocker.
- **assess information hiding**: a focused later policy change or adapter replacement; inspect which responsibilities change and whether behavior survives; diagnostic only, no file-count thresholds.
- **record validation gap**: state the repository validation that failed or did not run; never manufacture probes, metrics, or proof tags; candidate execution, checker separation, evaluation, merge authority belong to Recurspec when invoked.
- **compile design report**: scope, linked design, ownership and contracts, research-backed choices, ordered increments, blockers; identify what is ready versus conditional.
- **compile implementation report**: implemented behavior, actual checks and their limits, unavailable environments and unexecuted checks, remaining obligations; keep design assessment, runtime evidence, maintainability observations separate.

## Artifact patterns

Choose the smallest set. Field names are prompts.

- **Design brief**: selected outcome and roadmap IDs, exclusions, actors and environment, constraints, evidence, scope dispositions, consequential vocabulary, current/target/migration distinctions, and which increment the design prepares.
- **Component specification**: purpose and allocation (requirement IDs, responsibility, non-responsibilities, contract location); state and authority (identity, lifetime, transitions, writers, readers, derived views, persistence, reconciliation); consumers and providers; behavior (triggers, outcomes, errors, temporal obligations, invariants distinguished); lifecycle and resources where consequential; boundary mapping where relevant; implementation mapping (inspected paths and symbols, proposed changes); decisions and evidence; acceptance with planned and executed checks separated.
- **Interaction specification**: task or requirement, trigger, actor, participating contracts, starting state, observable success; messages or calls in order with mutation authority and acknowledgment semantics; alternate and error paths; final trustworthy state.
- **Decision record**: question, constraints, evidence, viable alternatives, choice, sacrificed qualities, fit gap, revisit condition; an unresolved decision stays visibly unresolved.
- **Traceability table**: requirement ID, origin, responsible component, interaction or contract, implementation location, acceptance check, evidence; distinguish proposed locations and planned checks from existing ones. Requirement meaning lives in the spec; work status lives in the registry.
- **Work package**: outcome, selected requirement and contract IDs, responsible modules and paths, dependency availability, real integration path, delivery prerequisites, acceptance checks, closure evidence, migration or reversal considerations when consequential, work owner only if known, unresolved blocking choices. An investigation package names question, experiment, and unlocked decision; private choices such as helper functions may stay open.

## Context and taste

- Terminology is operational for this skill; preserve equivalent subject-project terms and state the mapping. Do not invent people or teams; temporary adapters need removal conditions. Research documents outside this package are not runtime requirements. Consult the three references (terminology, existing projects, design method) only as the logic reads them; research and artifact guidance is summarized above.
- The subject project keeps one authoritative work registry; specifications define behavior and link work IDs. Evidence discipline: code inspection establishes only what was inspected, tests establish exercised behavior under their setup, measurements apply to their workload and environment, proof applies within its assumptions; none assures overall product correctness, and prose contracts do not enforce themselves.
- Judgments of cohesion, boundary quality, adequacy of design depth, and consequential versus private decisions are taste-based and cannot be mechanically checked; use the guidance above and state the reasoning.
