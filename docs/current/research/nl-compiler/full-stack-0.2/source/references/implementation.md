# Authorized implementation

Use when the task requests building or implementing. Consume the scoped design and the project's existing execution workflow; do not create a companion plan or require another approval for already authorized work. The host must provide repository access, execution tools, and any needed runtime. Missing capabilities are concrete blockers, not evidence of completion.

## Establish the handoff

For each bounded increment, identify selected requirements and observable acceptance criteria, responsible modules and inspected/proposed source paths, dependency contracts and availability, integration order, relevant checks, and evidence needed to close the work. Use the [work package](artifacts.md#work-package) in the existing registry. Investigate unresolved product or contract semantics before dependent implementation; continue independent work.

## Implement complete increments

Connect one real path through the required boundaries, then finish all selected transitions, failures, and lifecycle obligations. Reuse existing facilities. Separate modules where responsibilities and hidden decisions justify it; source-file count and line limits are not architecture criteria. Keep composition and presentation from becoming competing owners of domain policy. Add packages or services only when dependencies, reuse, isolation, or delivery constraints justify them.

Test doubles may exercise a contract early. Record what they simulate, unsupported guarantees, the real provider, and the check/removal condition for replacing them. Never substitute a double, empty method, placeholder, or visual demonstration for required behavior. A first vertical slice is progress toward the milestone, not permission to omit remaining requirements.

## Verify and close

Run the project's applicable checks and exercise the real user/system path. Match evidence to acceptance criteria: relevant failures, independent state, cleanup, and persistence across process restart when required. Build/type checks and isolated tests do not alone establish integrated behavior. Report unavailable environments or unexecuted checks precisely.

For material boundary changes, use a focused later policy change or adapter replacement when useful to assess information hiding. Inspect which responsibilities change and whether existing behavior survives; avoid arbitrary file-count thresholds. This is a diagnostic, not a mandatory extra feature for every task.

Continue until the selected requirements are satisfied or concrete blockers prevent further progress. Record unfinished required work, blockers, and the next resumption step in the authoritative registry. Report implemented behavior, actual checks and their limits, and remaining obligations. Keep design assessment, runtime evidence, and maintainability observations separate.
