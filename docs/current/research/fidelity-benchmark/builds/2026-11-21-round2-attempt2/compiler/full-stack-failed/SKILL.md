---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation when requested. Use for changes crossing meaningful component boundaries. Not for isolated routine edits.
---

# Full Stack (SkillWren logic)

The procedure is the `logic` block below, with its `contract` rules. Execute it exactly; it is the only procedure.

```contract
always:
  preserve authoritative documents, IDs, and project vocabulary
  keep current state, target state, and migration distinct
  explain necessary prerequisites and keep scope disposition, evidence, and completion as separate axes
  preserve settled user decisions
  label doubles with their simulated guarantees, limits, and replacement conditions
  keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct, and mark unexecuted checks
never:
  treat documentation or mock data as working behavior
  treat doubles as operational integration
  expand or replace scope because of a discovery alone
  treat design readiness or a first working increment as milestone completion
  deploy, publish, install tools, or delegate beyond their own applicable permissions
inputs:
  request, subject
order:
  exec#inspect before write#design
  apply sequence work before write#design
  write#design before write#implementation
  write#implementation before exec#acceptance
  verify#accepted before return#built
```

```logic
full-stack:
  apply authorization reading with request as mode

  if authorization is unclear:
    ask user to authorize implementation within this scope
    require confirmation
      otherwise:
        apply planning default with mode as mode

  if a missing answer changes the outcome or authority and available evidence cannot resolve it:
    ask user to clarify the outcome or authority
    require confirmation
      otherwise:
        apply assumption record with request as request

  if the request needs deployment, publication, tool installation, or delegation that existing permissions do not cover:
    ask user to approve deployment, publication, tool installation, or delegation
    require confirmation
      otherwise:
        apply hold dependent work with mode as mode

  exec #inspect inspect applicable instructions, code, contracts, tests, and prototypes from checks as inspection
  verify #inspected inspection covers applicable instructions and representative code, contracts, tests, and prototypes from inspection
    otherwise:
      apply gap note with inspection as inspection
  apply ground scope with inspection as scope
  apply classify discoveries with scope as scope
  apply resolve ambiguity with scope as scope

  if the scope has ambiguous concepts or relations:
    read references/terminology.md as terminology
      otherwise:
        apply gap note with scope as scope
    apply define terms with terminology as terms
  if the work is a design delta or Recurspec integration:
    read references/existing-projects.md as existing_projects
      otherwise:
        apply gap note with scope as scope
    apply align existing projects with existing_projects as alignment
  if the work needs substantial decomposition:
    read references/design-method.md as design_method
      otherwise:
        apply gap note with scope as scope
    apply decomposition method with design_method as method

  label iterate:
  apply trace behavior with scope as behavior
  apply allocate authority with behavior as authority
  apply resolve choices with authority as choices
  apply connect contracts with choices as contracts
  apply bound components with contracts as contracts
  apply sequence work with contracts as increments
  apply gap check with increments as gaps
  if gaps were found:
    apply gap repair with gaps as increments
  if new evidence changed the scope, behavior, or contracts:
    return to iterate

  if the scenario triggers changed trust or permissions, shared mutable state, durable data, user interaction, platform constraints, deployment or recovery, migration, or resource or latency demands:
    apply quality concerns with increments as increments
  else:
    apply exclusion explanation with increments as increments

  if a commitment is costly to reverse:
    apply commitment record with increments as commitment
    write commitment with registry

  apply design assembly with increments as design
  write #design design with design_docs
  apply registry entries with increments as work_entries
  write work_entries with registry

  if the next increment is design-ready:
    apply ready label with increments as readiness
  else:
    apply conditional label with increments as readiness

  if mode is authorized implementation:
    read references/implementation.md as implementation_guide
      otherwise:
        apply gap note with scope as scope
    apply implementation procedure with implementation_guide as procedure
    generate implementation from design and procedure as implementation
    write #implementation implementation with subject
    exec #acceptance acceptance checks from checks as results
    verify #accepted every selected acceptance criterion passed from results
      otherwise:
        if the failure persists with the same evidence:
          apply blocker record with results as blocker
          return #blocked:
            blocker
            readiness
        apply correction with implementation as implementation
        write implementation with subject
        exec acceptance checks from checks as results
        retry
    return #built:
      design
      implementation
      results
      readiness

  return #planned:
    scope
    design
    choices
    increments
    readiness
```

## References

The flow reads `references/terminology.md`, `references/existing-projects.md`, `references/design-method.md`, and `references/implementation.md` only when its condition holds. Consult `references/research.md` when resolving choices and `references/artifacts.md` when connecting contracts. Research documents outside this package are not runtime requirements.

## Step meanings

- **authorization reading**: planning is the default; only a request to build or implement authorizes implementation, and only within that scope. Follow existing task authorization without repeated approval.
- **planning default**: treat the work as design-only.
- **assumption record**: state the consequential assumption made in place of the missing answer, use the most reversible ordinary choice, and continue.
- **hold dependent work**: mark work needing the unapproved deployment, publication, tool installation, or delegation as conditional and continue with independent work.
- **gap note**: record which expected instructions, artifacts, or references were not found; continue with what is available.
- **ground scope**: identify the subject repository, outcome, selected work IDs, constraints, and exclusions.
- **classify discoveries**: label each discovery and proposed mechanism as exactly one of required now, existing dependency, unresolved prerequisite, or deferred enhancement.
- **resolve ambiguity**: resolve from available evidence, state consequential assumptions, and use reversible ordinary choices to continue.
- **define terms**: use the terminology reference to define ambiguous concepts and relations.
- **align existing projects**: use the existing-projects reference to express the design as a delta or Recurspec integration.
- **decomposition method**: use the design-method reference to guide substantial decomposition.
- **trace behavior**: define ambiguous terms and observable acceptance criteria; follow trigger, state transitions, and result, including relevant failure, retry, cancellation, and recovery; separate prototype appearance and interaction requirements from simulated behavior.
- **allocate authority**: assign cohesive responsibilities, authoritative state, policy, invariants, readers and writers, and derived views; one authority per state set or an explicit coordination protocol; architectural authority, resource ownership, and team responsibility differ.
- **resolve choices**: research uncertainty that could change the design; preserve valid existing choices; resolve consequential reuse before detailing custom internals; stop at adopted providers' public boundaries and allocate required fit gaps.
- **connect contracts**: use relevant artifact patterns for consumers, providers, interface semantics, lifecycle, source mappings, and checks; match consumer assumptions to provider guarantees or explicit unresolved conditions; describe shared providers once.
- **bound components**: split only where different decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling prevents a coherent increment; screens, nouns, directories, and workflow steps do not dictate components; components do not dictate files, packages, services, processes, or teams.
- **sequence work**: link selected requirements, affected responsibilities and paths, prerequisite decisions and contracts, the real integration path, checks, and closure evidence; prefer bounded end-to-end increments; resolve shared interface work before claiming independence.
- **gap check**: check gaps within responsibilities (states, errors, resources, lifecycle), across contracts (identity, authority, ordering, failures), and across the outcome (complete task and observable result).
- **gap repair**: close the gaps found, then continue.
- **quality concerns**: apply the triggered concerns; missing benchmarks call for explicit targets or investigation, not automatic exclusion of performance.
- **exclusion explanation**: explain excluding any material concern without adding unrelated scope.
- **commitment record**: record consequences, migration or reversal options, and affected work before committing.
- **design assembly**: assemble scope, linked design, ownership and contracts, research-backed choices, ordered increments, and blockers; specifications define behavior and link work IDs.
- **registry entries**: unresolved decisions, evidence needed, and affected work, for the one authoritative work registry in the subject project.
- **ready label**: mark the increment ready; outcome, contracts, prerequisites, and checks are usable and consequential decisions resolved; private implementation choices may remain; there is no target depth or artifact count.
- **conditional label**: mark what is conditional and keep unavailable prerequisites explicit.
- **implementation procedure**: follow the implementation reference and continue through the selected acceptance criteria; design readiness and a first working increment do not mean the milestone is complete.
- **correction**: repair the failing edit against the failing acceptance criterion.
- **blocker record**: state the blocker and next step.
