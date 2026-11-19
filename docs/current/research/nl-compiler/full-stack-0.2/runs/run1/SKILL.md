---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation when requested. Use for changes crossing meaningful component boundaries. Not for isolated routine edits; deployment, publication, tool installation, and delegation need their own permissions.
---

# Full Stack (SkillWren logic)

The procedure is the `logic` block below and its `contract`. Execute it exactly; it is the only procedure. Use it for changes crossing meaningful component boundaries, not isolated routine edits. This entrypoint owns scope, authorization, evidence, and readiness rules; scale depth to uncertainty and risk. Research documents outside this package are not runtime requirements.

```contract
always:
  preserve authoritative documents, IDs, and project vocabulary
  keep current state, target state, and migration distinct
  keep scope disposition, evidence, and completion as separate axes
  keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct, and mark unexecuted checks
  preserve settled user decisions
  preserve equivalent subject-project terms and make the mapping explicit
  treat model-generated suggestions as inference until evidence supports them
  work at the requested scope and reuse existing providers through their contracts
  replace an owner only with evidence that the selected outcome requires it
  state resource borrowing, transfer, synchronization, and unsafe obligations when relevant to Rust or native implementation
  keep traceability tables as navigational projections of the specification and the work registry
  for a temporary double, name the simulated contract and guarantees, unsupported behavior, real provider, and replacement condition, and link the remaining integration work in the same registry
  preserve SYSTEM.md contracts, contract markers and schema, and ROADMAP.md as the work registry in Recurspec projects
  follow the repository's required validation for accepted contract edits
  preserve the conventions of a subject project that has its own structure
never:
  treat documentation or mock data as establishing working behavior
  let discovery alone authorize scope expansion or replacement
  require repeated approval for already authorized work
  create a parallel architecture tree
  require a new crate merely because a specification exists
  keep independent status fields in derived views
  close a requirement for real integration on a passing double-based test
  let an implementation package require the implementer to decide unresolved product semantics
  treat a roadmap row marked done as independent verification
  mark implemented behavior missing merely because an old brainstorm omits it
  duplicate normative interface definitions when linking concept documents to the owning contract
  treat coverage suggestions as anything but proposals
  manufacture probe files, metric values, or formal-proof tags
  install tools or modify a whole tree merely to enable planning
  run expensive whole-project testing for a documentation-only comparison
  substitute a double, empty method, placeholder, or visual demonstration for required behavior
  treat a first vertical slice as permission to omit remaining requirements
  let composition or presentation own domain policy
  use source-file count or line limits as architecture criteria
  flatten containment, runtime communication, model refinement, and delivery precedence into one tree
  create a new registry file without a need for implementation tracking
inputs:
  request, subject, selected_work
order:
  apply trace behavior before apply sequence work
  apply connect contracts before apply sequence work
  apply supplied sources before exec readonly primary sources
  verify#readiness before write#design
  verify#readiness before write#registry
  write#slice before write#rest
```

```logic
full-stack:
  exec readonly inspect subject instructions code contracts tests from checks as inspection
  verify #grounded scope names repository, outcome, work IDs, constraints, and exclusions from inspection
    otherwise:
      apply ground scope with inspection as scope
      exec readonly inspect subject instructions code contracts tests from checks as inspection
      retry

  if concepts or relations are ambiguous:
    read references/terminology.md as terminology
      otherwise:
        abort with "Terminology reference unavailable."
  if the request needs design deltas or Recurspec integration:
    read references/existing-projects.md as existing_projects
      otherwise:
        abort with "Existing-projects reference unavailable."
  if the request needs substantial decomposition:
    read references/design-method.md as design_method
      otherwise:
        abort with "Design-method reference unavailable."

  if subject is an existing project:
    exec readonly inspect governing architecture, work registry, glossary, conventions, and relevant code from checks as authority
    verify #authority governing documents are identified and disagreements are recorded as target design versus observed implementation from authority
      otherwise:
        apply establish authority with authority as authority
        exec readonly inspect governing architecture, work registry, glossary, conventions, and relevant code from checks as authority
        retry
    verify #claims done roadmap rows are checked against the governing architecture and current code from authority
      otherwise:
        apply establish authority with authority as authority
        exec readonly inspect governing architecture, work registry, glossary, conventions, and relevant code from checks as authority
        retry

  if subject uses Recurspec:
    read Recurspec local rules and contracts from subject as recurspec_rules
      otherwise:
        abort with "Recurspec local rules and contracts unreadable."
    if the Recurspec CLI is available:
      exec readonly recurspec status from checks as recurspec
      verify #recurspec read-only status oriented the relevant tree from recurspec
        otherwise:
          apply report validation not performed with recurspec_rules as recurspec_rules
    else:
      apply report validation not performed with recurspec_rules as recurspec_rules
    apply map contract nodes with recurspec_rules as contract_map

  apply classify dispositions with inspection as dispositions
  apply resolve ambiguity with inspection as assumptions
  show assumptions

  if a runtime claim is uncertain:
    if a relevant check is feasible and useful:
      exec readonly relevant runtime check from checks as runtime
      verify #runtime the claim rests on an executed check from runtime
        otherwise:
          apply state absent execution evidence with inspection as runtime
    else:
      apply state absent execution evidence with inspection as runtime

  if uncertainty could change the design:
    read references/research.md as research
      otherwise:
        abort with "Research reference unavailable."
    apply research question with dispositions as question
    apply supplied sources with question as sources
    exec readonly primary sources fetch from checks as evidence
    verify #sources material claims rest on primary sources that were read from evidence
      otherwise:
        apply record inaccessible sources with evidence as evidence
    apply compare alternatives with question as alternatives
    if a technology candidate is proposed for adoption:
      exec readonly adoption compatibility check from checks as compatibility
      verify #compat runtime, target architecture, allocator, kernel interfaces, graphics and network dependencies, and license are verified from compatibility
        otherwise:
          apply mark adoption unresolved with alternatives as alternatives
    verify #stop the consequential claim is supported, conflicts have bounded implications, and further searching is unlikely to change the decision from evidence
      otherwise:
        apply further research with evidence as evidence
        exec readonly primary sources fetch from checks as evidence
        retry

  label iterate:
  if the request includes a prototype:
    apply prototype split with inspection as prototype
  apply trace behavior with inspection as behavior
  apply allocate authority with behavior as allocation
  apply resolve choices with allocation as choices
  apply split components with choices as components
  apply challenge boundaries with components as boundaries
  apply connect contracts with boundaries as contracts
  if a temporary double is used:
    apply double record with contracts as contracts
  apply sequence work with contracts as sequence
  if the delivery order has a cycle:
    apply break cycle with sequence as sequence
  if a quality concern is triggered by the scenario:
    apply quality concerns with sequence as quality
  if a flow requires retries, cancellation, timeouts, event ordering, or resynchronization:
    apply interaction concerns with sequence as interactions

  exec readonly design review checks from checks as review
  verify #boundaries each candidate responsibility answers the five boundary questions from review
    otherwise:
      apply revisit design with sequence as revision
      return to iterate
  verify #gaps no gaps remain within responsibilities, across contracts, or across the outcome from review
    otherwise:
      apply revisit design with sequence as revision
      return to iterate
  verify #ready the next increment has usable outcome, contracts, prerequisites, checks, and resolved consequential decisions from review
    otherwise:
      apply revisit design with sequence as revision
      return to iterate
  verify #readiness origins, owners, checks, dependency availability, compatible authority and contracts, observable failure paths, and registry links are confirmed from review
    otherwise:
      apply revisit design with sequence as revision
      return to iterate

  if a commitment is costly to reverse:
    apply record consequences with sequence as consequences
    if a missing answer changes the outcome or authority and the user has not already settled it:
      ask user to decide the open question that changes outcome or authority
      require confirmation
        otherwise:
          abort with "Open decision not confirmed; nothing was written."
  if work involves deployment, publication, tool installation, or delegation:
    ask user to grant permission for deployment, publication, tool installation, or delegation
    require confirmation
      otherwise:
        apply mark gated work with sequence as sequence

  apply select artifacts with sequence as artifact_set
  apply requirement wording with artifact_set as artifact_set
  if subject has no established design structure:
    apply standalone placement with artifact_set as artifact_set
  generate design artifacts from artifact_set as design
  write #design design with design_docs
  if implementation work needs tracking and subject has no existing roadmap:
    write #roadmap new roadmap with registry
  write #registry unresolved decisions, evidence needed, and affected work IDs with registry
  if a temporary double is used:
    write #doubles temporary double records with registry

  if contract edits are accepted:
    exec repository required validation from checks as validation
    verify #validation the repository's required validation passed from validation
      otherwise:
        apply correction with design as design
        write #designfix design with design_docs
        exec repository required validation from checks as validation
        retry

  label build:
  if request asks to build or implement:
    require host provides repository access, execution tools, and runtime
      otherwise:
        write #blocker concrete blocker with registry
        abort with "Concrete blocker: host lacks repository access, execution tools, or runtime."
    apply handoff with selected_work as handoff
    write #handoff work package with registry
    if unresolved product or contract semantics block dependent implementation:
      apply investigate semantics with handoff as investigation
      write #investigation investigation package with registry
    generate one real path through the required boundaries from handoff as slice
    write #slice slice with subject
    exec path check from checks as path
    verify #path one real path connects the required boundaries from path
      otherwise:
        apply correction with slice as slice
        write #slicefix slice with subject
        exec path check from checks as path
        retry
    generate remaining transitions, failures, and lifecycle obligations from handoff as rest
    write #rest rest with subject
    exec project checks from checks as results
    verify #acceptance every selected acceptance criterion passed on the project checks and the real path from results
      otherwise:
        apply correction with rest as rest
        write #restfix rest with subject
        exec project checks from checks as results
        retry
    verify #nosub no double, empty method, placeholder, or visual demonstration stands in for required behavior from results
      otherwise:
        apply correction with rest as rest
        write #nosubfix rest with subject
        exec project checks from checks as results
        retry
    if a material boundary change makes a focused diagnostic useful:
      apply boundary diagnostic with rest as diagnostic
    if selected requirements remain unsatisfied and no concrete blocker prevents progress:
      return to build
    write #resume unfinished work, blockers, and next resumption step with registry
    return:
      design
      report = results
  else:
    return design as design
```

## Step meanings

- **ground scope**: identify the subject repository, outcome, selected work IDs, constraints, and exclusions; inspect applicable instructions and representative code, contracts, tests, and prototypes.
- **establish authority**: identify governing architecture, work registry, glossary, conventions, and relevant code and tests; follow actual flows, not directory names; preserve IDs and rationale; when documents disagree, investigate the claim and record target design versus observed implementation.
- **report validation not performed**: inspect the Recurspec artifacts and report that CLI validation was not performed.
- **map contract nodes**: map components and requirements to existing Contract Nodes where appropriate; work packages need not map one-to-one; use Recurspec evidence labels and decision classes without changing their meaning.
- **classify dispositions**: label each discovery and proposed mechanism required now, existing dependency, unresolved prerequisite, or deferred enhancement; explain necessary prerequisites.
- **resolve ambiguity**: resolve from available evidence; state consequential assumptions; use reversible ordinary choices to continue.
- **state absent execution evidence**: state what code was inspected and that execution evidence is absent; avoid expensive whole-project testing for a documentation-only comparison.
- **research question**: record the affected requirement, decision, platform constraints, and what finding would change the choice; separate conceptual precedent, technology candidate, and compatibility evidence (a supported interface or an executed integration check, with limits).
- **supplied sources**: start from supplied sources and existing repository decisions before outside material.
- **record inaccessible sources**: record inaccessible full text and the unresolved assumption with affected work; continue independent design; a proposed compatibility test is a plan, not evidence.
- **compare alternatives**: compare credible alternatives including the existing approach, and feasible reuse, adaptation, or build under actual constraints; no minimum option count for settled or trivial decisions; do not fabricate alternatives; for consequential choices seek a counterexample or opposing tradeoff.
- **mark adoption unresolved**: leave the adoption decision visibly unresolved, name the unresolved assumption and affected work.
- **further research**: continue only the investigation that could still change the decision; do not grow the milestone by collecting optional features.
- **prototype split**: distinguish appearance, demonstrated interactions, and simulated behavior; link salient visual requirements; include accessibility and keyboard behavior; for nonvisual tasks use returned values, records, events, device actions, or operational signals; a mock array establishes neither persistence nor a lifecycle service.
- **trace behavior**: define ambiguous terms and observable acceptance criteria; trace identity, lifetime, transitions, cardinality, authority, and observable completion where ambiguity changes behavior; map aliases without merging distinct entities; follow trigger, state transitions, and result, including relevant failure, retry, cancellation, and recovery; for each task identify actor, needed information, authorized mutations, and observer of completion; explore absent or stale data, duplicates, partial success, crash, and restart; resolve conflicting current and target claims; treat a transport acknowledgment as not completion, and inspect bootstrap, shutdown, reconnection, and stale derived state.
- **allocate authority**: assign cohesive responsibilities, authoritative state, policy, invariants, readers and writers, and derived views; one authority per state set or an explicit coordination protocol; architectural authority, resource ownership, and team responsibility differ.
- **resolve choices**: preserve valid existing choices; resolve consequential reuse before custom internals; stop at adopted providers' public boundaries and allocate required fit gaps to owned work; keep adopted providers opaque beyond their contracts.
- **split components**: split only where different decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling prevents a coherent increment; screens, nouns, directories, and workflow steps do not dictate components; components do not dictate files, packages, services, processes, or teams.
- **challenge boundaries**: challenge each consequential boundary with a competing quality (information hiding versus latency or transaction colocation); record tradeoffs; map source/build, runtime, protection, and deployment independently; a source module supplies no fault containment.
- **connect contracts**: use relevant artifact patterns for consumers and providers, interface semantics, lifecycle, source mappings, and checks; match consumer assumptions to provider guarantees or explicit unresolved conditions; check identity, schema and versioning, errors, ordering and delivery, authorization, cancellation, backpressure, and recovery; exactly-once effects and lossless streams need supporting mechanisms; describe shared providers once; choose polling or subscriptions from requirements and provider behavior.
- **double record**: label the double with its simulated guarantees, limits, and replacement condition; a double does not establish operational integration.
- **sequence work**: link selected requirements, affected responsibilities and paths, prerequisite decisions and contracts, the real integration path, checks, and closure evidence; prefer bounded end-to-end increments; order interface agreements before dependent integration; resolve shared interface work before claiming independence; mark proposed paths and unavailable prerequisites.
- **break cycle**: resolve a delivery cycle through a stable interface, a coordinated increment, or an investigation; prefer a real vertical slice with an explicit retirement path for temporary adapters.
- **quality concerns**: address changed trust or permissions, shared mutable state, durable data, user interaction, platform constraints, deployment and recovery, migration, and resource or latency demands; missing benchmarks call for explicit targets or investigation, not exclusion; explain excluding a material concern without adding unrelated scope.
- **interaction concerns**: add identity and correlation, retries and duplicates, cancellation, timeouts, event ordering, and reconnect or resynchronization; say where a user or operator observes failure; a sequence diagram supplements semantics.
- **revisit design**: revisit requirement interpretation and architecture when evidence changes; when a dependency lacks a feature, preserve the explicit requirement and expose the incompatibility and alternatives; remove invented subcomponents when an existing owner supplies the behavior; recheck generated concepts against original evidence before deriving further artifacts.
- **record consequences**: record consequences, migration or reversal options, and affected work before committing.
- **mark gated work**: mark work that needs the declined permission as blocked and continue the rest.
- **select artifacts**: choose the smallest set that answers the task; reuse project formats and file names; one document for a small scope, separate component and flow files when independently consumed or maintained; no per-component readiness checklist.
- **standalone placement**: no dependency on Recurspec or Architectural Reasoning; preserve another project's conventions; with no established structure place a design brief plus necessary component and flow specifications under `docs/design/`; use the existing roadmap, creating one only when implementation work needs tracking.
- **requirement wording**: prefer a defined actor or component, trigger or condition, action, and observable result; EARS patterns are optional language patterns, not evidence levels; never replace concrete behavior with "handles errors appropriately".
- **correction**: repair the failing edit and apply it to the value being repaired before the check re-runs.
- **handoff**: for the bounded increment, record selected requirements and acceptance criteria, modules and source paths, dependency contracts and availability, integration order, checks, and closure evidence in a work package in the existing registry; reuse existing facilities.
- **investigate semantics**: investigate unresolved product or contract semantics before dependent implementation, naming the question, the evidence or experiment, and the decision it unlocks; continue independent work meanwhile.
- **boundary diagnostic**: use a focused later policy change or adapter replacement to inspect which responsibilities change and whether existing behavior survives; a diagnostic, not a mandatory feature.

## Artifact contents

- **Design-only deliverable**: scope, linked design, ownership and contracts, research-backed choices, ordered increments, and blockers; identify what is ready versus conditional.
- **Design brief**: selected outcome and roadmap IDs, explicit exclusions, actors and environment, existing constraints, relevant evidence, scope dispositions, consequential vocabulary, current/target/migration distinctions, and the increment the design prepares.
- **Component specification**: purpose and allocation (requirement IDs, responsibility, non-responsibilities, contract location); state and authority; consumers and providers; behavior (triggers, outcomes, errors, temporal obligations, invariants distinguished); lifecycle and resources where consequential; boundary mapping only where relevant; implementation mapping (inspected paths and symbols, proposed changes, never invented existing files); decisions and evidence; acceptance with planned and executed checks clearly separated.
- **Interaction specification**: task or requirement, trigger, actor, participating contracts, starting state, observable success; messages or calls in order with the authority for each mutation and acknowledgment semantics; alternate and error paths; final trustworthy state.
- **Decision record**: question, constraints, evidence, viable alternatives, choice, sacrificed qualities, fit gap, revisit condition; an unresolved decision stays visibly unresolved; a user-fixed choice records its origin and investigates integration constraints instead of reopening the selection.
- **Traceability table**: columns requirement ID, origin, responsible component, interaction or contract, implementation location, acceptance check, evidence; a row may link several components and checks; distinguish proposed from existing.
- **Work package**: outcome and selected requirement and contract IDs, responsible modules and inspected or proposed paths, dependency availability, real integration path, delivery prerequisites, acceptance checks, closure evidence, migration or reversal considerations when consequential, a work owner only if known, and unresolved choices blocking implementation. An investigation package names the question, the evidence or experiment, and the decision it unlocks.
- **Design delta**: current behavior, desired behavior, affected boundaries, and an incremental migration; preserve valuable existing behavior; specify removal conditions for temporary adapters; label current versus target diagrams.
- **Source record**: title, authors or publisher, publication or version date, URL, access date, relevant section, supported claim, applicability limit; distinguish peer-reviewed results, technical reports, preprints, method descriptions, and vendor documentation; a standard's public abstract is insufficient for a conformance claim.
- **Research resolution**: selection, alternatives, fit gap, reason, and reconsideration conditions; use the project's classes if present, otherwise reuse, adapt, build, or unresolved; classifications do not replace rationale.
- **Implementation report**: implemented behavior, actual checks and their limits, remaining obligations; keep design assessment, runtime evidence, and maintainability observations separate; report unavailable environments or unexecuted checks precisely.

## Terminology

Operational definitions for this skill, not a formal ontology.

- Design activities: elicitation obtains needs from stakeholders and evidence; elaboration makes behavior explicit while keeping provenance; refinement adds detail preserving the parent obligation; synthesis combines responsibilities and boundaries under constraints; decomposition divides at a useful scale; allocation assigns obligations to an accountable element; specification states observable semantics; verification assesses conformance with stated limits; validation assesses fit to intended use.
- Problem and behavior: outcome (an observable result), capability, requirement (with origin), domain property, assumption (record the consequence if false), constraint, scenario, domain concept, goal refinement, obstacle, quality scenario (stimulus, source, artifact, environment, response, measure).
- Structure and authority: responsibility, component, subsystem, module, bounded context, state authority, resource ownership, work owner (do not invent people or teams), policy, interface contract, invariant, architecture view, architectural decision.
- Delivery and evidence: work package, vertical slice, acceptance criterion (label proposed targets; do not invent measured performance), traceability, current state, target state, migration, fit gap.
- Relations: originates-from, refines, alternative-to, allocated-to, owns, provides/consumes, depends-on, realized-by, verified-by, supersedes; use only the distinctions the task needs, with stable IDs once several artifacts refer to one element.

## Judgment calls

No mechanical check exists for cohesive responsibilities, valid boundary tradeoffs, the smallest sufficient artifact set, or which failure paths are relevant; decide from evidence and state the reasoning.
