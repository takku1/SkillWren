# Research flow

Use research only to resolve uncertainty that could change the design. Ordinary design runs need only decision-relevant investigation.

```contract
always:
  maintain provenance: a model-generated suggestion begins as an inference, code inspection establishes only what was inspected, tests only exercised behavior under their setup, measurements only their workload and environment, formal proof only within its assumptions, and none assures overall correctness
  treat a proposed compatibility test as a test plan, not evidence of compatibility
  do not fabricate alternatives or grow the milestone by collecting optional features
  treat a standard's public abstract as insufficient for a conformance claim
never:
  recommend adoption from conceptual precedent alone
inputs:
  scope
order:
  apply state research question before exec#gather
```

```logic
research:
  apply state research question with scope as question
  if the request explicitly asks for academic or deep research:
    apply broaden research corpus with question as corpus
    apply cited synthesis with corpus as synthesis
  exec #gather gather supplied sources and current primary documentation from checks as sources
  verify #sources material claims were read from the source from sources
    otherwise:
      apply record inaccessible full text with sources as source_gaps
  apply compare alternatives with sources as comparison
  if the recommendation would adopt a technology:
    exec adoption fit check from checks as fit
    verify #adoption-fit runtime, target architecture, library, kernel, graphics, network, and license fit the platform from fit
      otherwise:
        apply record unresolved assumption with fit as unresolved
  if evidence is unavailable:
    apply record unresolved assumption with comparison as unresolved
  verify #research-sufficient the consequential claim is supported and conflicts have bounded implications from sources
    otherwise:
      apply record open conflicts with sources as open_conflicts
  apply source record with comparison as research_record
  write #research-record research_record with design_docs
  return research_record as research_record
```

## Step meanings

- **state research question**: record the affected requirement, the decision, actual platform constraints, and what finding would change the choice. Separate conceptual precedent (a design idea used elsewhere), technology candidate (an implementation considered for actual use), and compatibility evidence (proof of a supported interface or an executed integration check, with its limits). A Linux compositor can be precedent for a custom OS without being a compatible dependency.
- **broaden research corpus**: widen the corpus for the explicit academic or deep-research request.
- **cited synthesis**: produce a separate cited synthesis, apart from the design.
- **compare alternatives**: compare credible alternatives, including the existing approach when viable; no minimum option count for settled or trivial decisions; for consequential choices seek a counterexample or opposing tradeoff. Gathering starts from supplied sources and existing repository decisions; use current primary documentation for unstable versions, APIs, maintenance, licensing, support, and pricing, and original papers or author/institution copies for research claims. Search snippets are leads.
- **record inaccessible full text**: note which material claims could not be read at the source and continue.
- **record unresolved assumption**: name the unresolved assumption and the affected work, do not recommend adoption on it, and continue independent design. Source architecture and benchmark results do not transfer automatically to a different environment.
- **record open conflicts**: record the conflicts and their implications; stop searching once the consequential claim is supported, conflicts have bounded implications, and further searching is unlikely to change the decision.
- **source record**: record title, authors/publisher, publication or version date, URL, access date, relevant section, supported claim, and applicability limit; distinguish peer-reviewed results, technical reports, preprints, method descriptions, and vendor documentation. Record the selection, alternatives, fit gap, reason, and reconsideration conditions, using the project's classes if present, else reuse, adapt, build, or unresolved; classifications do not replace rationale.
