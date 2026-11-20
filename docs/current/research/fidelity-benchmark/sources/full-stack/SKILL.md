---
name: full-stack
description: Turn a software request, roadmap slice, or prototype into a scoped design with ownership, contracts, and ordered work; carry it through implementation when requested. Use for changes crossing meaningful component boundaries, not isolated routine edits.
metadata:
  version: "0.2.0"
---

# Full Stack

Deliver a connected design across the layers needed for the requested outcome, including native/platform systems. Planning is the default; a request to build or implement authorizes the implementation path within that scope. Follow existing task authorization without repeated approval. Deployment, publication, tool installation, and delegation follow their own applicable permissions.

## Ground the scope

Identify the subject repository, outcome, selected work IDs, constraints, and exclusions. Inspect applicable instructions and representative code, contracts, tests, and prototypes. Preserve authoritative documents, IDs, and project vocabulary. Keep **current state**, **target state**, and **migration** distinct; documentation and mock data do not establish working behavior.

Classify discoveries and proposed mechanisms as **required now**, **existing dependency**, **unresolved prerequisite**, or **deferred enhancement**. Explain necessary prerequisites; discovery does not authorize expansion or replacement. Scope disposition, evidence, and completion are separate axes.

Resolve ambiguity from available evidence. State consequential assumptions and use reversible ordinary choices to continue. For costly-to-reverse commitments, record consequences, migration/reversal options, and affected work before committing; seek clarification only when a missing answer changes the outcome or authority. Preserve settled user decisions.

Load references only as needed: [terminology](references/terminology.md) for ambiguous concepts/relations; [existing projects](references/existing-projects.md) for design deltas or Recurspec integration; [design method](references/design-method.md) for substantial decomposition. Research documents outside this package are not runtime requirements.

## Design the outcome

Iterate these activities as evidence changes; do not freeze requirements before exploring architecture.

1. **Trace behavior.** Define ambiguous terms and observable acceptance criteria. Follow trigger, state transitions, and result, including relevant failure, retry, cancellation, and recovery. Separate prototype appearance/interaction requirements from simulated behavior.
2. **Allocate authority.** Assign cohesive responsibilities, authoritative state, policy, invariants, readers/writers, and derived views. Use one authority per state set or an explicit coordination protocol. Architectural authority, resource ownership, and team responsibility differ.
3. **Resolve choices.** Research uncertainty that could change the design using [research](references/research.md). Preserve valid existing choices; resolve consequential reuse before detailing custom internals. Stop at adopted providers' public boundaries and allocate required fit gaps.
4. **Connect contracts.** Use relevant [artifact patterns](references/artifacts.md) for consumers/providers, interface semantics, lifecycle, source mappings, and checks. Match consumer assumptions to provider guarantees or explicit unresolved conditions. Describe shared providers once.
5. **Sequence work.** Link selected requirements, affected responsibilities/paths, prerequisite decisions/contracts, real integration path, checks, and closure evidence. Prefer bounded end-to-end increments; resolve shared interface work before claiming independence. Label doubles and their simulated guarantees, limits, and replacement conditions; they do not establish operational integration.

## Bound the design

Split where different decisions need hiding, authority changes hands, protection/lifecycle differs, or coupling prevents a coherent increment. Screens, nouns, directories, and workflow steps do not dictate components; components do not dictate files, packages, services, processes, or teams.

A next increment is design-ready when its outcome, contracts, prerequisites, and checks are usable and consequential decisions resolved. Private implementation choices may remain. Keep unavailable prerequisites explicit. There is no target depth or artifact count.

Check gaps **within responsibilities** (states, errors, resources, lifecycle), **across contracts** (identity, authority, ordering, failures), and **across the outcome** (complete task and observable result). Apply quality concerns when triggered by the scenario: changed trust/permissions, shared mutable state, durable data, user interaction, platform constraints, deployment/recovery, migration, or resource/latency demands. Missing benchmarks call for explicit targets or investigation, not automatic exclusion of performance. Explain excluding a material concern without adding unrelated scope.

## Deliver and verify

Keep requirements, invariants, assumptions, source inspection, executed tests, measurements, and proof distinct. Mark unexecuted checks; prose contracts do not enforce themselves.

Maintain one authoritative work registry in the subject project. Specifications define behavior and link work IDs; record unresolved decisions, evidence needed, and affected work there.

For **design-only** work, deliver the scope, linked design, ownership/contracts, research-backed choices, ordered increments, and blockers. Identify what is ready versus conditional.

For **authorized implementation**, follow [implementation](references/implementation.md) and continue through the selected acceptance criteria. Design readiness and a first working increment do not mean the milestone is complete.
