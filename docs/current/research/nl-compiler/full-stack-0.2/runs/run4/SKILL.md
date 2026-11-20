---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation when requested. Use for changes crossing meaningful component boundaries, not isolated routine edits. Not for deployment, publication, or tool installation on its own authority.
---

# Full Stack (SkillWren logic)

The procedure is the `logic` block below; execute it as written. Prose after it gives meanings and context only.

```contract
always:
  preserve authoritative documents, IDs, and project vocabulary
  keep current state, target state, and migration distinct
  treat documentation and mock data as not establishing working behavior
  keep scope disposition, evidence, and completion as separate axes
  preserve settled user decisions
  label every test double with its simulated guarantees, limits, and replacement condition
  keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct
  mark unexecuted checks and separate planned checks from executed checks
  keep requirement meaning in specifications and work status in the work registry
  reuse existing providers through their contracts
  keep conceptual precedent, technology candidates, and compatibility evidence separate
  record model-generated suggestions as inference until supported
  report what was not done and which checks were not executed
never:
  invent existing files in an implementation mapping
  let a passing double-based test close a requirement for real integration
  substitute a double, empty method, placeholder, or visual demonstration for required behavior
  let a discovery authorize expansion or replacement of scope
  create a parallel architecture tree
  treat a done roadmap row as independent verification
  let an implementation package leave unresolved product semantics to its implementer
  let composition or presentation own domain policy
  install tools or modify a whole tree merely to enable planning
  manufacture probe files, metric values, or formal-proof tags
  duplicate normative interface definitions
  keep independent status fields in derived views
  invent measured performance, people, or teams
  recommend adopting a technology whose fit check is unmet
inputs:
  request, subject
order:
  apply trace behavior before apply sequence work
  apply connect contracts before apply sequence work
  apply state research question before apply research
  apply investigate semantics before write#path
  write#path before write#completion
```

```logic
fullstack:
  apply start gap list with request as gaps
  if the request is unclear on whether to build or implement:
    ask user to choose between planning and implementation
    require confirmation
      otherwise:
        apply default to planning with request as mode
  if the request asks to build or implement:
    apply authorize implementation with request as mode
  else:
    apply default to planning with request as mode
  if the task needs deployment, publication, tool installation, or delegation:
    unless that action is already permitted:
      ask user to approve the deployment, publication, tool installation, or delegation
      require confirmation
        otherwise:
          apply record gap with gaps as gaps
  exec readonly inspect applicable instructions and representative code, contracts, tests, and prototypes from checks as inspection
  verify #inspected applicable instructions and representative artifacts were inspected from inspection
    otherwise:
      apply record gap with gaps as gaps
  apply ground scope with inspection as scope
  apply classify dispositions with scope as scope
  if ambiguity remains after reading the evidence:
    apply resolve ambiguity with scope as scope
  if a commitment is costly to reverse:
    apply record commitment with scope as scope
  if a missing answer would change the outcome or authority:
    ask user to settle the missing outcome or authority decision
    require confirmation
      otherwise:
        apply record gap with gaps as gaps
  if concepts or relations are ambiguous:
    apply define terms with scope as scope
  if the change is a design delta or the subject uses Recurspec:
    exec #authority governing architecture, work registry, and conventions inspection from checks as authority_check
    verify #authority-found governing architecture and work registry were identified from authority_check
      otherwise:
        apply record gap with gaps as gaps
    apply establish existing authority with scope as scope
  if a roadmap row or old document is cited as evidence of done or missing work:
    exec #finding governing architecture and current code check from checks as finding_check
    verify #finding-checked governing architecture and current code were checked before the finding from finding_check
      otherwise:
        apply record gap with gaps as gaps
  if the subject uses Recurspec:
    if the Recurspec CLI is available:
      exec #status recurspec read-only status from checks as status
    else:
      apply record gap with gaps as gaps
  if a runtime claim is uncertain:
    if a relevant check is feasible and useful:
      exec #claim claim check from checks as claim_result
    else:
      apply state inspection limits with gaps as gaps
  if uncertainty could change the design:
    apply state research question with scope as question
    exec #sources primary sources read for material claims from checks as sources
    verify #sources-read material claims rest on sources that were read from sources
      otherwise:
        apply record gap with gaps as gaps
    apply compare alternatives with question as alternatives
    if an alternative would be adopted as a technology:
      exec #fit runtime, architecture, interface, dependency, and license check from checks as fit
      verify #fit-ok candidate runtime, target architecture, interfaces, dependencies, and license are checked from fit
        otherwise:
          apply record gap with gaps as gaps
    apply research with alternatives as choices
    verify #enough the consequential claim is supported, conflicts are bounded, and more searching is unlikely to change the decision from sources
      otherwise:
        apply record gap with gaps as gaps
    if the request is an explicit academic or deep-research request:
      apply cited synthesis with choices as choices
  if the decomposition is substantial:
    apply challenge boundaries with scope as scope
  if the request includes a prototype:
    apply separate prototype behavior with scope as scope
  apply trace behavior with scope as behavior
  apply allocate authority with behavior as authority
  apply bound components with authority as components
  apply connect contracts with components as contracts
  apply sequence work with contracts as sequence
  if evidence changes the interpretation or architecture:
    apply revisit design with sequence as sequence
  if delivery order has a cycle:
    apply resolve delivery cycle with sequence as sequence
  exec gaps check from checks as gapcheck
  verify #gaps gaps within responsibilities, across contracts, and across the outcome are checked from gapcheck
    otherwise:
      apply record gap with gaps as gaps
  if quality concerns are triggered by the scenario:
    apply quality concerns with sequence as sequence
  if the implementation is Rust or native:
    apply state resource obligations with sequence as sequence
  if the flow requires identity, retries, cancellation, timeouts, ordering, or resynchronization:
    apply interaction semantics with sequence as sequence
  if subject has no established design structure:
    apply place under docs/design with sequence as sequence
  apply artifact patterns with sequence as design_set
  write #design design_set with subject
  if the design edits accepted contracts:
    exec #validation repository validation from checks as validation
    verify #valid repository validation passed from validation
      otherwise:
        apply record gap with gaps as gaps
  apply registry entries with design_set as registry_entries
  write #registry registry_entries with subject
  if the next increment is design-ready:
    apply label ready with sequence as readiness
  else:
    apply label conditional with sequence as readiness
  if implementation is authorized:
    apply handoff with design_set as handoff
    apply investigate semantics with handoff as handoff
    apply connect real path with handoff as path
    write #path path with subject
    apply complete selected increments with path as completion
    write #completion completion with subject
    exec #checks project checks from checks as results
    verify #accept results match acceptance criteria and exercise the real path from results
      otherwise:
        if the failure persists with the same evidence or a required capability is missing:
          apply record blocker with results as blocker
          write #blocker blocker with subject
          return:
            design = design_set
            report = blocker
        apply correction with completion as completion
        write #fix completion with subject
        exec #recheck project checks from checks as results
        retry
    if the boundary change is material and a diagnostic is useful:
      exec #diagnostic boundary diagnostic from checks as diagnostic_result
      apply boundary diagnostic with diagnostic_result as completion
    apply record unfinished work with results as remaining
    write #update remaining with subject
    apply implementation report with results as report
    return:
      design = design_set
      report
      gaps
  else:
    return:
      design = design_set
      readiness
      gaps
```

## Commands

| Flow step | Command |
|---|---|
| `exec readonly inspect` | read-only inspection of applicable instructions, code, contracts, tests, prototypes |
| `exec #authority`, `exec #finding` | read the governing architecture, registry, and current code; no whole-project tests for a documentation-only comparison |
| `exec #status` | the Recurspec CLI's read-only status command, only if installed |
| `exec #claim` | a relevant check for the uncertain claim |
| `exec #sources` | read the primary sources behind material claims |
| `exec #fit` | check runtime, architecture, interfaces, dependencies, license of a candidate, before any recommendation to adopt it |
| `exec gaps check` | review gaps within responsibilities, across contracts, across the outcome |
| `exec #validation` | the repository's required validation for accepted contract edits |
| `exec #checks`, `exec #recheck` | the project's own applicable checks, plus the real user/system path |
| `exec #diagnostic` | a focused later policy change or adapter replacement, inspected for what changes |

## Step meanings

- **start gap list**: begin an empty list of unresolved assumptions, missing references, declined permissions, and unexecuted checks.
- **authorize implementation**: the request to build or implement authorizes the implementation path within the scoped design; no repeated approval and no companion plan.
- **default to planning**: planning is the default; treat the task as design-only and do not implement.
- **record gap**: note the unresolved assumption, missing reference, declined permission, or missing evidence, the affected work, and the evidence needed; continue independent work.
- **ground scope**: identify subject repository, outcome, selected work IDs, constraints, exclusions; trace consequential terms to the request and artifacts; define identity, lifetime, transitions, cardinality, authority, and observable completion where ambiguity changes behavior; map aliases without merging distinct entities.
- **classify dispositions**: label each discovery or proposed mechanism required now, existing dependency, unresolved prerequisite, or deferred enhancement; explain necessary prerequisites.
- **resolve ambiguity**: use available evidence; state consequential assumptions; take reversible ordinary choices to continue.
- **record commitment**: before committing, record consequences, migration/reversal options, and affected work.
- **define terms**: consult references/terminology.md; keep equivalent subject-project terms and make the mapping explicit.
- **establish existing authority**: consult references/existing-projects.md. Identify governing architecture, work registry, glossary, conventions, relevant code/tests; follow actual flows, not directory names; preserve IDs and rationale; where documents disagree, investigate and record target design versus observed implementation. For Recurspec, preserve SYSTEM.md contracts and markers and ROADMAP.md as registry, link concept docs to the owning contract, map to Contract Nodes without assuming one-to-one with work packages, and keep its evidence labels and decision classes. A done roadmap row is a recorded claim; do not mark implemented behavior missing because an old brainstorm omitted it.
- **state inspection limits**: say what code was inspected and what execution evidence is absent.
- **state research question**: record the affected requirement, decision, platform constraints, and the finding that would change the choice.
- **compare alternatives**: compare credible alternatives including the existing approach, with no minimum count and no fabricated options; for consequential choices seek a counterexample or opposing tradeoff.
- **research**: consult references/research.md; separate conceptual precedent, technology candidate, compatibility evidence. Do not recommend adopting a candidate whose fit check is recorded as a gap. Start from supplied sources; use current primary documentation and original papers; read sources for material claims and record inaccessible full text; record title, authors/publisher, date, URL, access date, section, supported claim, applicability limit, source type (a standard's abstract does not support a conformance claim); record selection, alternatives, fit gap, reason, reconsideration conditions (project classes, else reuse/adapt/build/unresolved). Stop when the claim is supported, conflicts are bounded, and more searching is unlikely to change the decision.
- **cited synthesis**: a separate cited document for academic or deep-research requests.
- **challenge boundaries**: consult references/design-method.md; for each candidate responsibility ask what justifies it, what it owns, what consumers must know, whether lifetime/authority/change/failure justify separation, and its cost. Challenge with a competing quality; map source, runtime, protection, deployment separately; a module is not fault containment.
- **separate prototype behavior**: separate appearance, demonstrated interactions, simulated behavior; link salient visual requirements; include accessibility/keyboard behavior; for nonvisual tasks use returned values, records, events, device actions, or signals; a mock array establishes neither persistence nor lifecycle.
- **trace behavior**: define ambiguous terms and observable acceptance criteria; follow trigger, state transitions, result, and relevant failure, retry, cancellation, recovery; for each task name actor, needed information, authorized mutations, observer; explore absent/stale data, duplicates, partial success, crash, restart; resolve conflicting current/target claims. Iterate as evidence changes.
- **allocate authority**: assign cohesive responsibilities, authoritative state, policy, invariants, readers/writers, derived views; one authority per state set or an explicit protocol; authority, resource ownership, and team responsibility differ.
- **bound components**: split only where different decisions need hiding, authority changes hands, protection/lifecycle differs, or coupling blocks a coherent increment; screens, nouns, directories, workflow steps do not dictate components, nor components files/packages/services/processes/teams. For each candidate ask what justifies it, what it owns, what consumers must know, and what the split costs.
- **connect contracts**: match consumer assumptions to provider guarantees or explicit unresolved conditions; describe shared providers once; check identity, schema/versioning, errors, ordering/delivery, authorization, cancellation, backpressure, recovery; exactly-once effects and lossless streams need supporting mechanisms. Stop at adopted providers' public boundaries and assign fit gaps.
- **sequence work**: link requirements, responsibilities/paths, prerequisite decisions/contracts, real integration path, checks, closure evidence; prefer bounded end-to-end increments; resolve shared interface work before claiming independence and order interface agreements before dependent integration; different files are not independence; mark proposed paths and unavailable prerequisites.
- **revisit design**: revisit interpretation and architecture when evidence changes; if a dependency lacks a feature, keep the requirement and expose the incompatibility and alternatives; remove invented subcomponents an existing owner supplies; recheck generated concepts against original evidence.
- **resolve delivery cycle**: break it with a stable interface, coordinated increment, or investigation; prefer a real vertical slice with a retirement path for temporary adapters.
- **quality concerns**: apply for changed trust/permissions, shared mutable state, durable data, user interaction, platform constraints, deployment/recovery, migration, resource/latency; missing benchmarks mean explicit targets or investigation; explain excluding a material concern without adding scope.
- **state resource obligations**: state borrowing, transfer, synchronization, and unsafe obligations; do not require a new crate merely because a specification exists.
- **interaction semantics**: include identity/correlation, retries/duplicates, cancellation, timeouts, event ordering, reconnect/resync; say where a user or operator observes failure; a transport acknowledgment need not mean completion; consumers resume, resynchronize, or report an unknown view; choose polling or subscriptions from requirements; a sequence diagram supplements semantics.
- **place under docs/design**: with no established structure, put the design brief and needed component/flow specs there; no per-component readiness checklist.
- **artifact patterns**: consult references/artifacts.md; choose the smallest set, reuse project formats, no empty sections. Design brief: outcome and roadmap IDs, exclusions, actors/environment, constraints, evidence, dispositions, vocabulary, current/target/migration, increment prepared. Component specification: purpose and allocation, state and authority, consumers/providers, behavior, lifecycle/resources, boundary mapping, implementation mapping (inspected paths/symbols and proposed changes), decisions and evidence, acceptance. Interaction specification: task, trigger, actor, contracts, starting state, ordered messages with mutation authority and acknowledgment semantics, alternate/error paths, final trustworthy state. Decision record: question, constraints, evidence, alternatives, choice, sacrificed qualities, fit gap, revisit condition; unresolved stays unresolved; a user-fixed choice records its origin. Traceability table: requirement ID, origin, component, contract, implementation location, acceptance check, evidence. Work package: outcome, IDs, modules and paths, dependency availability, integration path, prerequisites, checks, closure evidence, migration/reversal, owner only if known; an investigation package names question, experiment, decision unlocked. Temporary double: simulated contract, unsupported behavior, real provider, replacement condition. Design delta: current, desired, boundaries, incremental migration, adapter removal conditions, labeled diagrams. Requirement wording: actor, trigger, action, observable result (EARS optional), never "handles errors appropriately".
- **registry entries**: one authoritative work registry in the subject; specifications define behavior and link work IDs; record unresolved decisions, evidence needed, affected work, temporary doubles and their remaining integration work; reuse an existing roadmap or create one when implementation needs tracking.
- **label ready**: next increment has usable outcome, contracts, prerequisites, checks and resolved consequential decisions (private choices may remain); there is no target depth or artifact count.
- **label conditional**: mark the work conditional; keep unavailable prerequisites explicit; confirm origins, owners, checks, dependency availability, compatible contracts, observable failure paths, registry links; sampled scenarios do not prove completeness.
- **handoff**: per increment, selected requirements, acceptance criteria, modules and paths, dependency contracts, integration order, checks, closure evidence, recorded as a work package in the registry.
- **investigate semantics**: resolve unresolved product or contract semantics before dependent implementation; continue independent work.
- **connect real path**: connect one real path through the required boundaries first; reuse existing facilities.
- **complete selected increments**: finish all selected transitions, failures, and lifecycle obligations; a first slice is not the milestone; separate modules only where hidden decisions justify; add packages or services only when justified.
- **correction**: repair the failing work; a repeated identical failure becomes a blocker.
- **record blocker**: name the concrete blocker or missing host capability, unfinished required work, and next resumption step.
- **boundary diagnostic**: optional focused later policy change or adapter replacement; inspect which responsibilities change and whether behavior survives; no file-count thresholds.
- **record unfinished work**: unfinished required work, blockers, and next resumption step go to the registry.
- **implementation report**: implemented behavior, actual checks and limits, remaining obligations; keep design assessment, runtime evidence, and maintainability observations separate.

## Context

- Planning is the default. A request to build or implement authorizes the implementation path within the scoped design, with no repeated approval or companion plan; ask only when the request does not say which. Deployment, publication, tool installation, and delegation follow their own permissions. The host must provide repository access and execution tools; missing capability is a blocker, not completion.
- Scale depth to uncertainty and risk; this entrypoint owns scope, authorization, evidence, and readiness. Research documents outside this package are not runtime requirements.
- Operational definitions, not standard definitions: elicitation, elaboration, refinement, synthesis, decomposition, specification, verification, validation. Inferred additions keep provenance; passing tests are not proof.
- Problem terms: outcome, requirement, assumption (record consequence if false), constraint (a user's fixed technology choice stays a constraint), scenario, obstacle, quality scenario ("fast" and "secure" are insufficient).
- Structure terms: responsibility, component, module, state authority, resource ownership, work owner (never invent people or teams), policy, interface contract, invariant.
- Delivery terms: work package, vertical slice, acceptance criterion (label proposed targets), traceability, fit gap.
- Relations: originates-from, refines, alternative-to, allocated-to, owns, provides/consumes, depends-on, realized-by, verified-by, supersedes. Use only useful ones, stable IDs once several artifacts refer to an element, one canonical description per shared provider, and no flattening into a tree.
