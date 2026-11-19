# Terminology and semantic relations

Use this vocabulary to prevent consequential ambiguity. These are operational definitions for this skill, informed by established engineering usage. They are not verbatim standard definitions or a formal ontology. Preserve equivalent subject-project terms and make the mapping explicit.

## Design activities

| Term | Meaning here | Important distinction |
|---|---|---|
| Requirements elicitation | Obtaining needs, constraints, and domain information from stakeholders and evidence | A model simulating a stakeholder does not establish that stakeholder's intent |
| Requirements elaboration | Making incomplete behavior, constraints, and assumptions explicit enough to reason about | Inferred additions retain their provenance and do not silently expand scope |
| Refinement | Adding detail while preserving a justified relationship to the parent obligation | More headings alone do not demonstrate preservation or sufficiency |
| Architectural synthesis | Selecting and combining responsibilities, mechanisms, and boundaries to satisfy requirements under constraints | A candidate design needs rationale; synthesis does not imply a uniquely correct answer |
| Decomposition | Dividing a system description into coherent parts at a useful scale | Does not by itself establish coverage, independence, or delivery order |
| Responsibility allocation | Assigning behavior, state, or enforcement obligations to an accountable element | Distinct from assigning an implementation ticket to a person |
| Specification | Description of required observable semantics and applicable constraints | May be prose or formal; a document is not automatically an executable contract |
| Verification | Assessing conformance to specified properties with stated evidence limits | Passing selected tests is not general proof |
| Validation | Assessing whether the requirements/design address the intended use and needs | Internal consistency alone does not establish the right product |

## Problem and behavior

| Term | Meaning here | Important distinction |
|---|---|---|
| Outcome | Observable result the requested change should achieve | A result, not a document or technology |
| Product capability | Ability offered by the system to an actor | Not a protected authority capability |
| Requirement | Obligation on behavior or quality, with an identifiable origin | Not an observation that behavior already exists |
| Domain property | Relevant fact or constraint of the operating environment | Unknown domain claims remain assumptions |
| Assumption | Proposition relied on but not established for this decision | Record consequence if false and how to resolve it |
| Constraint | Restriction on acceptable designs, such as platform or compatibility | A user's fixed technology choice remains a constraint |
| Scenario | Concrete actor task or stimulus and its expected outcome | One example does not exhaust a requirement |
| Domain concept | Meaningful entity, value, event, or relationship in the subject matter | Not automatically a class or component |
| Goal refinement | Relating an outcome to sufficient subordinate obligations or alternatives | All required subgoals versus alternative solutions must be distinguished |
| Obstacle | Condition that can prevent a selected outcome | Not automatically a new product feature |
| Quality scenario | Stimulus, source, artifact, environment, response, and assessment measure | “Fast” and “secure” are not sufficient specifications |

## Structure and authority

| Term | Meaning here | Important distinction |
|---|---|---|
| Responsibility | Cohesive behavior, state, policy, or guarantee allocated to an owner | A workflow step may have no independent responsibility |
| Component | Architectural element with explicit responsibilities and interfaces | State its view; do not assume it is a runtime process |
| Subsystem | Coherent portion of a larger system described at a useful scale | No fixed size or depth is implied |
| Module | Source/development organization hiding implementation decisions | May not match a runtime boundary |
| Bounded context | Boundary within which a domain model and language have a consistent meaning | Not a synonym for component, service, or team |
| State authority | Component or protocol accountable for accepting a state transition | A cache or UI projection does not acquire authority by copying data |
| Resource ownership | Allocation, borrowing/sharing, lifetime, synchronization, and cleanup responsibility | Rust ownership is distinct from product authority |
| Work owner | Person or role responsible for delivery/review/operation | Do not invent people, teams, or delegate assignments |
| Policy | Rule deciding which allowed behavior should occur | Distinct from the mechanism capable of performing it |
| Interface contract | Provider/consumer semantics, assumptions, outcomes, errors, and relevant temporal rules | A signature alone is insufficient |
| Invariant | Property required to remain true across applicable states/transitions | An eventual response is generally a temporal obligation |
| Architecture view | Representation selected to answer a set of concerns | A view is not the entire system |
| Architectural decision | Choice among alternatives with rationale and consequences | A discovered fact is not a decision |

## Delivery and evidence

| Term | Meaning here | Important distinction |
|---|---|---|
| Work package | Bounded implementation or investigation assignment with dependencies and acceptance | May touch several components; not a permanent architecture node |
| Vertical slice | Small end-to-end increment spanning the layers needed for one outcome | Not all work in one horizontal layer |
| Acceptance criterion | Observable condition used to assess a requirement or increment | Label proposed targets; do not invent measured performance |
| Traceability | Links from origin through requirements, decisions, realization, and checks | A diagram without origins is insufficient |
| Current state | Behavior/structure established from available evidence | Separate read code from executed behavior |
| Target state | Intended future behavior and organization | Does not establish implementation |
| Migration | Changes connecting current and target states while respecting constraints | Temporary adapters need explicit removal conditions |
| Fit gap | Required behavior a candidate solution does not supply | Generates owned integration/custom work only if in scope |

## Relation vocabulary

Use only the distinctions useful to the task; stable IDs are helpful once several artifacts refer to the same element.

| Relation | Direction and intended meaning |
|---|---|
| `originates-from` | Requirement → request, document, finding, or explicitly stated inference |
| `refines` | More detailed requirement → parent outcome/requirement, with sufficiency rationale |
| `alternative-to` | Option ↔ mutually substitutable choice under stated constraints |
| `allocated-to` | Responsibility/requirement → accountable component |
| `owns` | Component/protocol → authoritative state, policy, or resource |
| `provides` / `consumes` | Component → named interface contract |
| `depends-on` | Work package → prerequisite work/decision; label runtime dependencies separately |
| `realized-by` | Design element → existing or proposed code location |
| `verified-by` | Requirement/contract → planned or executed check, explicitly distinguished |
| `supersedes` | Decision/definition → earlier one whose rationale remains traceable |

Containment, runtime communication, model refinement, and delivery precedence are different relations. Shared providers have one canonical description with several incoming references. Do not flatten all relations into a tree.

## Requirement wording

Prefer a defined actor/component, trigger or condition, action, and observable result. Use EARS when helpful: ubiquitous; event-driven (`WHEN`); state-driven (`WHILE`); unwanted behavior (`IF`/`THEN`); optional feature (`WHERE`). These are language patterns, not evidence levels or proof claims.

Example: “When an authorized launch request fails before an application instance is established, the apps bar clears its pending indicator and presents the reported failure.” Define the identity, reporting interface, and retry semantics elsewhere if needed. Do not replace concrete behavior with “the subsystem handles errors appropriately.”

## Scope dispositions

- **Required now:** directly necessary to deliver the selected outcome.
- **Existing dependency:** consumed through its established boundary; any needed modification becomes separately scoped work.
- **Unresolved prerequisite:** necessary, but availability, semantics, or technology remains unresolved.
- **Deferred enhancement:** optional/outside the selected milestone; does not block required work unless a documented dependency shows otherwise.

Evidence and completion are separate axes. Use the subject project's evidence labels where present; otherwise describe the evidence and its limits directly.
