---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation when requested. Use for changes crossing meaningful component boundaries. Not for isolated routine edits.
---

# Full Stack (SkillWren logic)

The procedure is the `logic` block below. Execute it exactly; it is the only procedure. Deliver a connected design across all layers the requested outcome needs, including native/platform systems. Planning is the default; a request to build or implement authorizes the implementation path within that scope. Follow existing task authorization without repeated approval.

```contract
always:
  preserve authoritative documents, IDs, and project vocabulary
  keep current state, target state, and migration distinct
  treat documentation and mock data as not establishing working behavior
  preserve settled user decisions
  keep scope disposition, evidence, and completion as separate axes
  label doubles with their simulated guarantees, limits, and replacement conditions
  keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct
  mark unexecuted checks
never:
  let discovery authorize expansion or replacement
  freeze requirements before exploring architecture
  deploy, publish, install tools, or delegate without its own applicable permission
  treat doubles as establishing operational integration
inputs:
  request, subject, registry
order:
  exec#inspect before write#registry
  write#implementation before exec#accept
```

```logic
full-stack:
  apply grounding with request as scope

  if request is ambiguous between design-only and implementation:
    ask user to decide whether to deliver design only or implement
    require confirmation
      otherwise:
        apply design-only default with scope as scope

  if a missing answer changes the outcome or authority:
    ask user to settle the missing outcome or authority decision
    require confirmation
      otherwise:
        apply assumptions with scope as scope

  if work needs deployment, publication, tool installation, or delegation:
    unless that action has its own applicable permission:
      ask user to grant permission for that action
      require confirmation
        otherwise:
          apply conditional marking with scope as scope

  exec #inspect inspect applicable instructions, code, contracts, tests, and prototypes from subject as inspection
  verify #inspected inspection covers applicable instructions, code, contracts, tests, and prototypes from inspection
    otherwise:
      apply assumptions with inspection as inspection
  apply classification with scope as scope

  if ambiguity remains after inspection:
    apply assumptions with scope as scope

  apply trace behavior with scope as design
  apply allocate authority with design as design
  apply resolve choices with design as design
  apply connect contracts with design as design
  apply sequence work with design as design
  apply double labels with design as design
  apply component boundaries with design as design
  if the scenario triggers changed trust or permissions, shared mutable state, durable data, user interaction, platform constraints, deployment or recovery, migration, or resource or latency demands:
    apply quality concerns with design as design
  apply concern exclusions with design as design
  if gaps remain within responsibilities, across contracts, or across the outcome:
    apply gap record with design as design

  if a commitment is costly to reverse:
    apply commitment record with design as design
    write #costly design with registry

  apply increment readiness with design as design
  if the next increment is design-ready:
    apply ready label with design as design
  else:
    apply conditional label with design as design
  write #registry design with registry

  if request asks to build or implement:
    read references/implementation.md as guide
      otherwise:
        apply reference gap with design as guide
    apply implementation path with guide as work
    write #implementation work with subject
    exec #accept acceptance checks for the selected criteria from checks as results
    verify #criteria every selected acceptance criterion passed from results
      otherwise:
        if the failure persists with the same evidence:
          apply blocker record with results as design
          return design as report
        apply continuation with work as work
        write #continue work with subject
        exec #recheck acceptance checks for the selected criteria from checks as results
        retry

  return design as report
```

## Step meanings

- **assumptions**: resolve ambiguity from available evidence; state consequential assumptions and use reversible ordinary choices to continue.
- **design-only default**: planning is the default; proceed design-only.
- **grounding**: identify the subject repository, outcome, selected work IDs, constraints, and exclusions; keep current state, target state, and migration distinct.
- **classification**: label each discovery and proposed mechanism as exactly one of required now, existing dependency, unresolved prerequisite, or deferred enhancement; explain necessary prerequisites.
- **conditional marking**: mark the dependent work as conditional on the missing permission and continue with independent work.
- **trace behavior**: define ambiguous terms and observable acceptance criteria; follow trigger, state transitions, and result, including relevant failure, retry, cancellation, and recovery; separate prototype appearance and interaction requirements from simulated behavior.
- **allocate authority**: assign cohesive responsibilities, authoritative state, policy, invariants, readers/writers, and derived views; one authority per state set or an explicit coordination protocol; architectural authority, resource ownership, and team responsibility differ.
- **resolve choices**: research uncertainty that could change the design using references/research.md; preserve valid existing choices; resolve consequential reuse before detailing custom internals; stop at adopted providers' public boundaries and allocate required fit gaps.
- **connect contracts**: use relevant patterns from references/artifacts.md for consumers/providers, interface semantics, lifecycle, source mappings, and checks; match consumer assumptions to provider guarantees or explicit unresolved conditions; describe shared providers once.
- **sequence work**: link selected requirements, affected responsibilities and paths, prerequisite decisions and contracts, the real integration path, checks, and closure evidence; prefer bounded end-to-end increments; resolve shared interface work before claiming independence.
- **double labels**: label each test double with its simulated guarantees, limits, and replacement conditions in the design that is written to the registry.
- **component boundaries**: split only where different decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling prevents a coherent increment; screens, nouns, directories, and workflow steps do not dictate components; components do not dictate files, packages, services, processes, or teams.
- **quality concerns**: apply the triggered concerns to the scenario; missing benchmarks call for explicit targets or investigation, not automatic exclusion of performance.
- **concern exclusions**: explain excluding any material concern without adding unrelated scope.
- **gap record**: record each remaining gap (within responsibilities: states, errors, resources, lifecycle; across contracts: identity, authority, ordering, failures; across the outcome: complete task and observable result) as an unresolved decision with the evidence needed and affected work.
- **commitment record**: record the consequences, migration or reversal options, and affected work of the costly-to-reverse commitment in the design.
- **increment readiness**: judge whether the next increment is design-ready: outcome, contracts, prerequisites, and checks usable and consequential decisions resolved. Private implementation choices may remain; there is no target depth or artifact count.
- **ready label**: label the increment ready in the delivered design.
- **conditional label**: label the increment conditional and keep unavailable prerequisites explicit; deliver the design anyway.
- **reference gap**: record that references/implementation.md was unavailable, and use that record as the guide; continue.
- **implementation path**: follow the guide and continue through the selected acceptance criteria; design readiness and a first working increment do not mean the milestone is complete.
- **blocker record**: record the blocker, its evidence, and the next step in the report.
- **continuation**: repair the failing work toward the selected acceptance criteria.

## Context

The registry is the one authoritative work registry in the subject project. Specifications define behavior and link work IDs; unresolved decisions, evidence needed, and affected work are recorded there. Subject instructions and existing authorization govern. The delivered design-only report covers scope, linked design, ownership and contracts, research-backed choices, ordered increments, and blockers, and states what is ready versus conditional.

Consult references only as needed: references/terminology.md for ambiguous concepts or relations; references/existing-projects.md for design deltas or Recurspec integration; references/design-method.md for substantial decomposition. Research documents outside this package are not runtime requirements. Iterate the design activities as evidence changes.
