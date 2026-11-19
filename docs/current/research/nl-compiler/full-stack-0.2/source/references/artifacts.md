# Artifact patterns

Choose the smallest set that answers the task. Reuse project formats and file names. A small scope can fit in one document; separate component and flow files when independently consumed or maintained. Field names below are prompts, not a schema requiring empty sections.

## Design brief

Capture the selected outcome and roadmap IDs, explicit exclusions, actors/environment, existing constraints, relevant evidence, and scope dispositions. Include the consequential vocabulary and current/target/migration distinctions. State which increment the design prepares.

## Component specification

Include:

- **Purpose and allocation:** requirement IDs, responsibility, non-responsibilities, authoritative contract location.
- **State and authority:** identity, lifetime, transitions, accepted writers, readers, derived views, persistence and reconciliation.
- **Consumers and providers:** named interfaces and required semantics.
- **Behavior:** triggers, outcomes, errors, and relevant temporal obligations; distinguish invariants.
- **Lifecycle and resources:** initialization, cancellation, cleanup, restart, bounds, and concurrency where consequential.
- **Boundary mapping:** source/build, runtime, protection, and deployment decisions only where relevant.
- **Implementation mapping:** inspected paths/symbols and explicitly proposed changes; never invent existing files.
- **Decisions and evidence:** alternatives, fit gaps, source links, assumptions, and affected unresolved work IDs.
- **Acceptance:** externally observable criteria and planned/executed checks, clearly separated.

State resource borrowing, transfer, synchronization, and unsafe obligations when relevant to Rust/native implementation. Do not require a new crate merely because a specification exists.

## Interaction specification

Name the task/requirement, trigger, actor, participating contracts, starting state, and observable success. Describe messages/calls in order, with the authority for each mutation and the semantics of acknowledgments. Add relevant alternate/error paths and final trustworthy state.

Include identity/correlation, retries/duplicates, cancellation, timeouts, event ordering, and reconnect/resynchronization when the flow requires them. Clarify where a user or operator observes failure. A short sequence diagram can help; it supplements semantics rather than replacing them.

## Decision record

Record the question, constraints, evidence, viable alternatives, choice, sacrificed qualities, fit gap, and revisit condition. Keep a decision that is unresolved visibly unresolved. If a choice is fixed by the user, record its origin and investigate integration constraints instead of reopening the selection.

## Traceability table

Use columns for requirement ID, origin, responsible component, interaction/contract, implementation location, acceptance check, and evidence. A row may link several components/checks. Distinguish proposed locations and planned checks from existing artifacts.

This table is a navigational projection. Requirement meaning belongs in the specification; work status belongs in the project's work registry. Do not maintain independent status fields in every derived view.

## Work package

Record the outcome and selected requirement/contract IDs, responsible modules and inspected/proposed paths, dependency availability, real integration path, delivery prerequisites, acceptance checks, and closure evidence. Include migration/reversal considerations when consequential and a work owner only if known. State unresolved choices that block implementation.

For a temporary double, name the simulated contract and guarantees, unsupported behavior, real provider, and replacement/check condition. Link its remaining integration work in the same registry. A passing double-based test cannot close a requirement for real integration.

An investigation package names the question, evidence/experiment, and decision it unlocks. An implementation package must not quietly require its implementer to decide unresolved product semantics. Private choices such as helper functions or local data representation can remain open.
