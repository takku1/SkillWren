# Design flow

Deliver a connected design across all layers the outcome needs, including native/platform systems. Scale depth to uncertainty and risk; there is no target depth or artifact count.

```contract
always:
  preserve authoritative documents, IDs, and project vocabulary
  keep current state, target state, and migration distinct; documentation and mock data do not establish working behavior
  explain necessary prerequisites; discovery does not authorize expansion or replacement
  keep scope disposition, evidence, and completion as separate axes
  preserve settled user decisions
  keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct, and mark unexecuted checks
  label doubles with simulated guarantees, limits, and replacement conditions; doubles do not establish operational integration
  keep the traceability table a navigational projection: meaning in specifications, status in the work registry
  work at the requested scope, reuse existing providers through their contracts, and create no parallel architecture tree
  preserve SYSTEM.md contracts, contract markers, schema, and ROADMAP.md as the work registry in Recurspec projects
  write requirements as actor, trigger, action, and observable result
  treat research documents outside this package as not runtime requirements
never:
  treat a roadmap row marked done as independent verification
  mark implemented behavior missing before checking the governing architecture and current code
  install tools or modify a whole Recurspec tree merely to enable planning
  manufacture probe files, metric values, or formal-proof tags
  duplicate normative interface definitions when linking concept documents to the owning contract
  treat deployment, publication, tool installation, or delegation as authorized by build authorization
  close a requirement for real integration with a passing double-based test
inputs:
  request, subject
order:
  exec readonly inspect before write#design
  exec readonly inspect before write#registry
  apply trace behavior before write#design
  apply connect contracts before apply sequence work
```

```logic
design:
  apply ground scope with request as scope
  exec readonly inspect instructions, code, contracts, tests, and prototypes from checks as inspection
  verify #grounded inspection covered applicable instructions, code, contracts, tests, and prototypes from inspection
    otherwise:
      apply record inspection gap with inspection as scope
  apply classify scope disposition with scope as dispositions
  if concepts or relations are ambiguous:
    apply terminology mapping with scope as scope
  if the subject is an existing project:
    apply establish authority with scope as scope
    apply design delta with scope as delta
  if the subject repository uses Recurspec:
    exec readonly recurspec status from checks as status
    verify #recurspec-cli recurspec status was read from status
      otherwise:
        apply record cli validation not performed with scope as scope
    apply map to contract nodes with scope as scope
  if ambiguity remains after available evidence:
    apply resolve ambiguity with scope as scope
  if a missing answer would change the outcome or authority:
    ask user to decide the missing outcome or authority answer
    require confirmation
      otherwise:
        apply state consequential assumption with scope as scope
  if the task needs deployment, publication, tool installation, or delegation without existing authorization:
    ask user to approve deployment, publication, tool installation, or delegation
    require confirmation
      otherwise:
        apply mark dependent work conditional with scope as scope
  if a runtime claim is uncertain and a relevant check is feasible and useful:
    exec runtime claim check from checks as runtime_result
    verify #runtime-claim the runtime claim is supported from runtime_result
      otherwise:
        apply record absent execution evidence with runtime_result as evidence_gap
  else:
    apply record absent execution evidence with scope as evidence_gap
  if the request includes a prototype:
    apply prototype separation with scope as prototype_view
  apply trace behavior with scope as behavior
  apply allocate authority with behavior as authority
  if uncertainty could change the design:
    run research from flows/research.md with:
      scope = scope
  apply resolve choices with authority as choices
  apply bound components with choices as components
  if the design needs substantial decomposition:
    apply challenge boundaries with components as components
  apply connect contracts with components as contracts
  if consumer assumptions do not match provider guarantees or explicit unresolved conditions:
    apply mark unresolved condition with contracts as contracts
  if the flow requires identity, retries, cancellation, timeouts, ordering, or resynchronization:
    apply interaction details with behavior as interaction_notes
  apply sequence work with contracts as work_packages
  if the runtime graph has delivery cycles:
    apply resolve delivery cycle with work_packages as work_packages
  if quality concerns are triggered by the scenario:
    apply quality concerns with scope as quality_view
  if gaps remain within responsibilities, across contracts, or across the outcome:
    apply record gap with scope as gaps
  if the complete task and actor feedback do not trace to an observable result:
    apply record gap with scope as gaps
  if evidence has changed since the design began:
    apply revisit interpretation and architecture with scope as scope
  if the increment is design-ready:
    apply label ready with work_packages as readiness
  else:
    apply label conditional with work_packages as readiness
  apply choose artifact set with scope as artifact_set
  if a commitment is costly to reverse:
    apply commitment record with scope as commitment_record
    write #commitment commitment_record with registry
  if the subject has an established design structure:
    apply existing design location with subject as design_location
  else:
    apply default design location with subject as design_location
  apply compose design artifacts with artifact_set as design
  write #design design with design_location
  apply registry entries with design as registry_entries
  write #registry registry_entries with registry
  if the subject uses Recurspec and contract edits were accepted:
    exec repository validation from checks as validation
    verify #repo-validation repository validation passed from validation
      otherwise:
        apply record validation gap with validation as validation_gap
  if request asks to build or implement:
    run implement from flows/implement.md with:
      design = design
    return report as report
  else:
    apply design only delivery with design as delivery
    return delivery as delivery
```

## Step meanings

- **ground scope**: identify the subject repository, outcome, selected work IDs, constraints, and exclusions; keep the project's own documents, IDs, and vocabulary.
- **record inspection gap**: name what instructions, code, contracts, tests, or prototypes could not be inspected, and continue.
- **classify scope disposition**: label each discovery and proposed mechanism as exactly one of required now, existing dependency, unresolved prerequisite, deferred enhancement.
- **terminology mapping**: consult `references/terminology.md`; define the ambiguous term or relation and map it to the project's equivalent term.
- **establish authority**: identify the governing architecture, work registry, glossary, conventions, and relevant code and tests (consult `references/existing-projects.md`); follow actual flows, not directory names; preserve IDs and historical rationale; where documents disagree, record which claim is target design and which is observed implementation.
- **design delta**: describe current behavior, desired behavior, affected boundaries, and incremental migration; preserve valuable existing behavior; give each temporary adapter a removal condition; label current and target diagrams if both appear.
- **record cli validation not performed**: inspect the Recurspec artifacts directly and report that CLI validation was not performed.
- **map to contract nodes**: map requirements and components to existing Contract Nodes where appropriate; work packages stay delivery units, not one-to-one with nodes; keep Recurspec's evidence labels and decision classes unchanged.
- **resolve ambiguity**: decide from available evidence; state consequential assumptions; continue with reversible ordinary choices.
- **state consequential assumption**: record the assumption made in place of the missing answer and continue.
- **mark dependent work conditional**: mark work needing the declined permission as conditional and continue independent work.
- **record absent execution evidence**: state which code was inspected and what execution evidence is absent; avoid expensive whole-project testing for a documentation-only comparison.
- **prototype separation**: separate appearance, demonstrated interactions, and simulated behavior; link salient visual requirements; include accessibility and keyboard behavior where relevant. For nonvisual tasks use returned values, records, events, device actions, or operational signals. A mock array establishes neither persistence nor a lifecycle service.
- **ground representative tasks**: trace consequential terms to the request and inspected artifacts; define identity, lifetime, transitions, cardinality, authority, and observable completion where ambiguity changes behavior; map aliases without merging distinct entities (process, application instance, and window differ).
- **task walkthrough**: for each selected task identify the actor, needed information, authorized mutations, and observer of completion; explore absent or stale data, duplicates, cancellation, partial success, crash, and restart; resolve conflicting current/target claims affecting the next increment.
- **trace behavior**: define ambiguous terms and observable acceptance criteria; follow trigger, state transitions, and result including failure, retry, cancellation, and recovery. The five design activities (trace behavior, allocate authority, resolve choices, connect contracts, sequence work) iterate as evidence changes; do not freeze requirements before exploring architecture.
- **allocate authority**: assign cohesive responsibilities, authoritative state, policy, invariants, readers/writers, and derived views; one authority per state set or an explicit coordination protocol; architectural authority, resource ownership, and team responsibility differ.
- **resolve choices**: research uncertainty that could change the design (`references/research.md`); preserve valid existing choices; resolve consequential reuse before detailing custom internals; compare feasible reuse, adaptation, and build under actual constraints; keep adopted providers opaque beyond their contracts and assign required fit gaps to owned work.
- **bound components**: split only where different decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling prevents a coherent increment; screens, nouns, directories, and workflow steps do not dictate components; components do not dictate files, packages, services, processes, or teams. For each candidate ask: what justifies it, what it owns, what consumers must know versus what stays private, whether lifetime, authority, change pressure, or failure behavior justifies separation, and what the split costs.
- **challenge boundaries**: consult `references/design-method.md`; challenge consequential boundaries with a competing quality (information hiding versus latency or transaction colocation) and record tradeoffs; map source/build, runtime, protection, and deployment independently; a source module is not fault containment.
- **connect contracts**: use the artifact patterns for consumers, providers, interface semantics, lifecycle, source mappings, and checks; match consumer assumptions to provider guarantees or explicit unresolved conditions; describe shared providers once. Check identity, schema/versioning, errors, ordering/delivery, authorization, cancellation, backpressure, and recovery; exactly-once effects and lossless streams need supporting mechanisms.
- **mark unresolved condition**: record the unmatched assumption as an explicit unresolved condition.
- **interaction details**: add identity/correlation, retries/duplicates, cancellation, timeouts, event ordering, and reconnect/resynchronization; say where a user or operator observes failure; a sequence diagram supplements semantics, never replaces them.
- **sequence work**: link selected requirements, affected responsibilities and paths, prerequisite decisions and contracts, the real integration path, checks, and closure evidence; prefer bounded end-to-end increments; resolve shared interface work before claiming independence; order interface agreements before dependent integration; different files do not establish independence; label doubles and their simulated guarantees; mark proposed paths and unavailable prerequisites.
- **resolve delivery cycle**: resolve a runtime-graph cycle through a stable interface, a coordinated increment, or an investigation; prefer a real vertical slice with an explicit retirement path for temporary adapters.
- **quality concerns**: apply concerns triggered by changed trust or permissions, shared mutable state, durable data, user interaction, platform constraints, deployment/recovery, migration, or resource/latency demands. Missing benchmarks call for explicit targets or investigation, not exclusion of performance. Explain excluding a material concern without adding unrelated scope.
- **record gap**: record the gap (within responsibilities: states, errors, resources, lifecycle; across contracts: identity, authority, ordering, failures; across the outcome: complete task and observable result) and continue. A transport acknowledgment need not mean the launch, save, payment, or device action completed; inspect bootstrap, shutdown, reconnection, and stale derived state so consumers resume, resynchronize, or report an unknown view; choose polling or subscriptions from requirements and provider behavior.
- **revisit interpretation and architecture**: revisit when evidence changes; preserve explicit requirements when a dependency lacks a feature by exposing the incompatibility and alternatives; remove invented subcomponents when an existing owner supplies the behavior; recheck generated concepts against original evidence before deriving further artifacts.
- **label ready**: mark the increment ready: outcome, contracts, prerequisites, and checks are usable and consequential decisions resolved; private implementation choices may remain.
- **label conditional**: mark the work conditional and keep unavailable prerequisites explicit; deliver conditional work as conditional; sampled scenarios do not establish whole-system completeness. Confirm origins, owners, checks, dependency availability, compatible authority and contracts, observable failure paths, and registry links before calling work ready.
- **choose artifact set**: choose the smallest set that answers the task; reuse project formats and file names; one document fits a small scope; separate component and flow files when independently consumed or maintained; field names are prompts, not a schema requiring empty sections.
- **commitment record**: record consequences, migration/reversal options, and affected work for a commitment that is costly to reverse.
- **existing design location**: use the subject's existing design documents and conventions.
- **default design location**: with no established structure, use `docs/design/` for a design brief plus necessary component and flow specifications; no separate readiness checklist per component.
- **compose design artifacts**: produce the artifacts in the shapes below, with the linked design, ownership and contracts, research-backed choices, and ordered increments.
- **registry entries**: update the one authoritative work registry in the subject project (use the existing roadmap, or create one when implementation work needs tracking); specifications define behavior and link work IDs; record unresolved decisions, evidence needed, and affected work there.
- **record validation gap**: report the repository's required validation result as it is; candidate execution, checker separation, evaluation, and merge authority belong to Recurspec when invoked.
- **design only delivery**: deliver scope, linked design, ownership/contracts, research-backed choices, ordered increments, and blockers, and identify what is ready versus conditional.

## Artifact shapes

- **Design brief**: selected outcome and roadmap IDs, explicit exclusions, actors/environment, existing constraints, relevant evidence, scope dispositions, consequential vocabulary, current/target/migration distinctions, and the increment the design prepares.
- **Component specification**: purpose and allocation (requirement IDs, responsibility, non-responsibilities, contract location); state and authority; consumers and providers; behavior, distinguishing invariants; lifecycle and resources; boundary mapping only where relevant; implementation mapping (inspected paths/symbols and explicitly proposed changes, never invented files); decisions and evidence; acceptance with planned and executed checks clearly separated.
- **Interaction specification**: task or requirement, trigger, actor, participating contracts, starting state, observable success; messages or calls in order with the mutation authority and acknowledgment semantics of each; alternate and error paths; final trustworthy state.
- **Decision record**: question, constraints, evidence, viable alternatives, choice, sacrificed qualities, fit gap, revisit condition. An unresolved decision stays visibly unresolved; a user-fixed choice records its origin and investigates integration constraints instead of reopening the selection.
- **Traceability table**: columns requirement ID, origin, responsible component, interaction/contract, implementation location, acceptance check, evidence; a row may link several components or checks; proposed locations and planned checks are distinguished from existing ones.
- **Work package**: outcome; selected requirement/contract IDs; responsible modules; inspected and proposed paths; dependency availability; real integration path; delivery prerequisites; acceptance checks; closure evidence; migration/reversal when consequential; work owner only if known; unresolved choices that block implementation. For a temporary double, name the simulated contract and guarantees, unsupported behavior, real provider, and replacement/check condition, and link its remaining integration work in the same registry.
- **Investigation package**: names the question, the evidence or experiment, and the decision it unlocks.

For Rust or native implementation, state resource borrowing, transfer, synchronization, and unsafe obligations when relevant; do not require a new crate merely because a specification exists.

## Context

- **Terminology**: operational meanings for this skill, not standard definitions or a formal ontology. Preserve equivalent subject-project terms and make the mapping explicit. Key distinctions: a requirement is an obligation with an origin, not an observation of existing behavior; a state authority is accountable for accepting transitions, and a cache or UI projection does not acquire authority by copying data; resource ownership differs from product authority; a work owner is never invented; acceptance criteria are labeled proposed, with no invented measurements; a fit gap is required behavior a candidate does not supply; a work package may touch several components; a vertical slice is small and end to end.
- **Relations**: originates-from, refines, alternative-to, allocated-to, owns, provides/consumes, depends-on, realized-by, verified-by, supersedes. Use only the useful ones. Containment, runtime communication, refinement, and delivery precedence are different relations. A shared provider has one canonical description with several incoming references; do not flatten relations into a tree.
- **Scope dispositions**: required now (directly necessary for the selected outcome); existing dependency (consumed through its boundary; modification is separate scope); unresolved prerequisite (necessary, but availability, semantics, or technology unresolved); deferred enhancement (optional or outside the milestone; blocks nothing unless a documented dependency shows otherwise). Evidence and completion are separate axes; use the project's evidence labels if present, else describe the evidence and its limits. Requirement wording may follow EARS patterns, which are language patterns, not evidence levels.
