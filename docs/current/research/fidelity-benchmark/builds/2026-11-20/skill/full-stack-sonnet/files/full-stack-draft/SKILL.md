---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation when requested. Use for changes crossing meaningful component boundaries, not isolated routine edits.
metadata:
  version: "0.2.0"
---

# Full Stack

```contract
inputs:
  request, repository, project
order:
  exec readonly repository inspection before generate scope
  exec readonly repository inspection before write work_registry
  write work_registry before write implementation
  verify #accepted before return#implemented
```

```logic
full-stack:
  require request exists
    otherwise:
      abort with "Name the software request, roadmap slice, or prototype to design."

  exec readonly repository inspection from repository as inspection
  generate scope from request, inspection as scope
  apply scope grounding with inspection as scope

  if the request is ambiguous in a way that changes the outcome or authority:
    ask user to clarify the outcome or authority
    require user clarifies the outcome or authority
      otherwise:
        abort with "Outcome or authority is unresolved; nothing was changed."

  apply assumption recording with scope as scope

  if the design needs a costly-to-reverse commitment:
    apply commitment record with scope as commitment
    write commitment with project

  generate design from scope as design
  apply design activities with design as design
  apply design bounds with design as design

  verify #designready the next increment has usable outcome, contracts, prerequisites and checks, with consequential decisions resolved from design
    otherwise:
      if the repair budget is spent:
        return #blocked design as blocker
      apply design repair with design as design
      retry

  generate registry update from design as work_registry
  write work_registry with project

  if the request authorizes implementation:
    read implementation reference from references as implementation_ref
    generate implementation from design as implementation
    apply implementation guidance with implementation_ref as implementation
    write implementation with project
    exec acceptance checks from project as checks
    verify #accepted every selected acceptance criterion is met from checks
      otherwise:
        if the repair budget is spent:
          return #blocked checks as blocker
        apply implementation repair with checks as implementation
        write implementation with project
        exec acceptance checks from project as checks
        retry
    return #implemented:
      design
      checks

  return #designed:
    design
```

| Step | Command |
|---|---|
| `exec readonly repository inspection` | list and read the repository's instructions, code, contracts, tests and prototypes without changing anything |
| `exec acceptance checks` | the project's own test and verification commands for the selected acceptance criteria |

## Step meanings

- **repository**: the subject repository. **project**: the same repository as a write target. **work_registry**: the one authoritative work registry in the subject project. **references**: this skill's `references/` folder.
- **scope grounding**: identify repository, outcome, selected work IDs, constraints and exclusions; preserve authoritative documents, IDs and project vocabulary; keep current state, target state and migration distinct (docs and mock data do not establish working behavior); classify each discovery as required now, existing dependency, unresolved prerequisite or deferred enhancement; explain prerequisites without expanding or replacing scope; keep scope disposition, evidence and completion separate; preserve settled user decisions. Load `terminology.md` for ambiguous concepts, `existing-projects.md` for design deltas or Recurspec integration, `design-method.md` for substantial decomposition, only as needed; research documents outside the package are not runtime requirements.
- **assumption recording**: resolve ambiguity from evidence; state consequential assumptions; continue on reversible ordinary choices; ask only when a missing answer changes outcome or authority.
- **commitment record**: record consequences, migration or reversal options and affected work before committing.
- **design activities**: iterate as evidence changes, without freezing requirements before exploring architecture. (1) Trace behavior: define terms and observable acceptance criteria; follow trigger, state transitions and result including failure, retry, cancellation and recovery; separate prototype appearance from simulated behavior. (2) Allocate authority: cohesive responsibilities, authoritative state, policy, invariants, readers/writers, derived views; one authority per state set or an explicit coordination protocol. (3) Resolve choices: research uncertainty using `research.md`; preserve valid existing choices; resolve reuse before custom internals; stop at adopted providers' public boundaries and allocate fit gaps. (4) Connect contracts using `artifacts.md`: match consumer assumptions to provider guarantees or explicit unresolved conditions; describe shared providers once. (5) Sequence work: link requirements, responsibilities/paths, prerequisites, the real integration path, checks and closure evidence; prefer bounded end-to-end increments; resolve shared interfaces before claiming independence; label doubles with simulated guarantees, limits and replacement conditions (doubles do not establish integration).
- **design bounds**: split only where decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling blocks an increment; screens, nouns, directories and steps do not dictate components, and components do not dictate files, packages, services, processes or teams. No target depth or artifact count; keep unavailable prerequisites explicit. Check gaps within responsibilities, across contracts and across the outcome. Apply quality concerns when triggered (trust/permissions, shared mutable state, durable data, user interaction, platform, deployment/recovery, migration, resource/latency); missing benchmarks call for targets or investigation, not exclusion; explain excluded material concerns without adding unrelated scope. Keep requirements, invariants, assumptions, inspection, executed tests, measurements and proof distinct, and mark unexecuted checks.
- **implementation guidance**: follow `references/implementation.md` and continue through the selected acceptance criteria.
- **design repair**: fix the named gap in the design; do not drop a requirement.
- **implementation repair**: fix the failing acceptance criteria shown by the checks, within the authorized scope. Design readiness or a first working increment is not milestone completion: continue through the selected acceptance criteria.
- **blocker**: the unmet gate, what each repair tried, and what is needed from the user.

## Output

**Designed** (design-only): scope, linked design, ownership/contracts, research-backed choices, ordered increments and blockers, stating what is ready versus conditional. Specifications define behavior and link work IDs; unresolved decisions, evidence needed and affected work are recorded in the work registry.

**Implemented** (authorized): the design plus the executed acceptance checks, following `references/implementation.md`. Deployment, publication, tool installation and delegation need their own permissions; task authorization already given is not asked for again.
