# Design method

Use for substantial decomposition. The entrypoint owns scope, authorization, evidence, and readiness rules; this reference adds boundary analysis. Scale depth to uncertainty and risk.

## Ground representative tasks

Trace consequential terms to the request and inspected artifacts. Define identity, lifetime, transitions, cardinality, authority, and observable completion where ambiguity changes behavior. Map aliases without merging distinct entities: a process, application instance, and window can have different lifetimes.

For each selected task, identify the actor, needed information, authorized mutations, and observer of completion. Explore relevant absent/stale data, duplicates, cancellation, partial success, crash, and restart. Resolve conflicting current/target claims that affect the next increment.

For prototypes, distinguish appearance, demonstrated interactions, and simulated behavior; link salient visual requirements and include relevant accessibility/keyboard behavior. For nonvisual tasks, use returned values, records, events, device actions, or operational signals. A mock array establishes neither persistence nor a lifecycle service.

## Allocate and challenge boundaries

For each candidate responsibility ask:

1. Which requirement or necessary dependency justifies it?
2. Which state, policy, resource, or private decision does it own?
3. What must consumers know, and what stays private?
4. Does lifetime, authority, change pressure, or failure behavior justify separation?
5. What does the split cost, and can an existing component remain cohesive?

Challenge consequential boundaries with a competing quality: information hiding may favor separation while latency or transaction semantics favor colocation. Record tradeoffs that affect the choice. Map source/build, runtime, protection, and deployment independently. A source module does not supply fault containment; actual isolation and recovery must support it. Rust borrowing and resource lifetime constrain implementation without replacing architectural authority.

## Resolve and revise

Investigate choices that could invalidate boundaries or substantial custom work. Compare feasible reuse/adaptation/build under actual constraints. Keep adopted providers opaque beyond their contracts; assign required fit gaps to owned work.

Revisit requirement interpretation and architecture when evidence changes. Preserve explicit requirements when a dependency lacks a feature: expose the incompatibility and alternatives. Remove invented subcomponents when an existing owner supplies the behavior. Recheck generated concepts against original evidence before deriving further artifacts.

## Compose contracts

Match consumer assumptions to provider guarantees or unresolved conditions. Where relevant, check identity, schema/versioning, errors, ordering/delivery, authorization, cancellation, backpressure, and recovery. Exactly-once effects and lossless streams require supporting mechanisms.

Trace the complete task and actor feedback. A transport acknowledgment need not mean a launch, save, payment, or device action completed. Inspect bootstrap, shutdown, reconnection, and stale derived state: consumers must resume, resynchronize, or report an unknown view. Choose polling or subscriptions from requirements and provider behavior.

## Sequence delivery

Use [work packages](artifacts.md#work-package) to connect design to execution. Mark proposed paths and unavailable prerequisites. Order interface agreements before dependent integration; different files do not establish independence.

Runtime graphs can contain cycles. Delivery still needs a workable order: resolve cycles through a stable interface, coordinated increment, or investigation. Prefer a real vertical slice with an explicit retirement path for temporary adapters.

Apply the entrypoint's readiness review across responsibilities, interactions, and the selected outcome. Confirm origins/owners/checks, dependency availability, compatible authority and contracts, observable failure paths, resolved consequential decisions, and links to the existing registry. Deliver conditional work as conditional; sampled scenarios do not establish whole-system completeness.
