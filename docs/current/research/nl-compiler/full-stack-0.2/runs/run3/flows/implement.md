# Implement flow

Use when the task requests building or implementing. Consume the scoped design and the project's existing execution workflow.

```contract
always:
  reuse existing facilities; separate modules only where responsibilities and hidden decisions justify it, and treat file count and line limits as no architecture criteria
  keep composition and presentation from becoming competing owners of domain policy
  add packages or services only when dependencies, reuse, isolation, or delivery constraints justify them
  record what a test double simulates, its unsupported guarantees, the real provider, and the check or removal condition
  keep design assessment, runtime evidence, and maintainability observations separate in the report
  let a first vertical slice never excuse omitting remaining requirements
  keep private choices such as helpers and local data representation open, and leave no unresolved product semantics to the implementer
never:
  substitute a double, empty method, placeholder, or visual demonstration for required behavior
  treat build or type checks and isolated tests alone as integrated behavior
  treat a missing capability as evidence of completion
  create a companion plan or require another approval for authorized work
inputs:
  design, subject
order:
  apply investigate unresolved semantics before write#path-slice
  verify#path-check before write#remaining
```

```logic
implement:
  if the host lacks repository access, execution tools, or runtime:
    apply blocker record with design as blocker
    write #capability-blocker blocker with registry
    return blocker as report
  apply work package with design as work_package
  write #work-package work_package with registry
  apply investigate unresolved semantics with work_package as work_package
  apply connect one real path with work_package as path_slice
  write #path-slice path_slice with subject
  exec real path check from checks as path_result
  verify #path-check the real path works through the required boundaries from path_result
    otherwise:
      if the failure persists with the same evidence:
        apply blocker record with path_result as blocker
        write #path-blocker blocker with registry
        return blocker as report
      apply correction with path_slice as path_slice
      write #path-correction path_slice with subject
      exec real path check after correction from checks as path_result
      retry
  apply finish remaining obligations with work_package as remaining
  write #remaining remaining with subject
  if a test double is used:
    apply double record with remaining as double_record
    write #double-record double_record with registry
  exec acceptance checks from checks as results
  verify #acceptance every selected acceptance criterion passed on the real path from results
    otherwise:
      if the failure persists with the same evidence:
        apply blocker record with results as blocker
        write #blocker blocker with registry
        return blocker as report
      apply correction with remaining as remaining
      write #correction remaining with subject
      exec acceptance checks after correction from checks as results
      retry
  if the change is a material boundary change:
    apply information hiding diagnostic with remaining as diagnostic
  apply final report with results as report
  write #final-report report with registry
  return report as report
```

## Step meanings

- **blocker record**: name the concrete blocker (missing capability, failing path, or a failure repeating with the same evidence), the unfinished required work, and the next resumption step; record it in the authoritative registry and return it as the report instead of claiming completion.
- **work package**: for each bounded increment record the selected requirements and observable acceptance criteria, responsible modules, inspected and proposed source paths, dependency contracts and availability, integration order, relevant checks, and closure evidence, in the existing registry.
- **investigate unresolved semantics**: investigate unresolved product or contract semantics before dependent implementation; continue independent work meanwhile; do nothing further when none are unresolved.
- **connect one real path**: connect one real path through the required boundaries, reusing existing facilities.
- **finish remaining obligations**: finish all selected transitions, failures, and lifecycle obligations; a first slice is progress, not completion.
- **double record**: record what the double simulates, unsupported guarantees, the real provider, and the check or removal condition; link remaining integration work in the same registry.
- **correction**: repair the failing edit using the failing evidence; a failure repeating with the same evidence becomes a reported blocker, not another repair.
- **information hiding diagnostic**: optionally use a focused later policy change or adapter replacement; inspect which responsibilities change and whether existing behavior survives; no arbitrary file-count thresholds. A diagnostic, not a mandatory extra feature.
- **final report**: report implemented behavior, the actual checks and their limits (match evidence to acceptance criteria: relevant failures, independent state, cleanup, persistence across restart when required), unavailable environments, unexecuted checks, and remaining obligations; keep design assessment, runtime evidence, and maintainability observations separate.
