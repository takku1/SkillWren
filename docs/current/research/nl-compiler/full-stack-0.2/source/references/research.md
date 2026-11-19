# Decision-directed research

Use research to resolve uncertainty that could change the design. For an explicit academic/deep-research request, broaden the corpus and produce a separate cited synthesis; ordinary design runs need only decision-relevant investigation.

## State the question first

Record the affected requirement, decision, actual platform constraints, and what finding would change the choice. Separate:

- **Conceptual precedent:** a design idea or decomposition used elsewhere.
- **Technology candidate:** an implementation being considered for actual use.
- **Compatibility evidence:** proof of a supported interface or an executed integration check, with its limits.

A Linux compositor can provide conceptual precedent for a custom OS without being a compatible dependency. Verify runtime, target architecture, standard-library/allocator requirements, kernel interfaces, graphics or network dependencies, and license before recommending adoption.

## Gather and assess

Start from supplied sources and existing repository decisions. Use current primary documentation for unstable versions, APIs, maintenance, licensing, support, and pricing. Use original papers or author/institution-hosted copies for research claims. Search result snippets are leads; read the source for material claims and record inaccessible full text.

Compare credible alternatives, including the existing approach when viable. Do not impose a minimum option count on settled or trivial decisions, and do not fabricate alternatives to fill a table. For consequential choices, seek a counterexample or opposing tradeoff that could invalidate the preferred approach.

Record title, authors/publisher, publication or version date, URL, access date, relevant section, supported claim, and applicability limit. Distinguish peer-reviewed results, technical reports, preprints, method descriptions, and vendor documentation. A standard's public abstract is insufficient for a conformance claim.

## Resolve without false certainty

Record the selection, alternatives, fit gap, reason, and conditions for reconsideration. Use the subject project's classes if present. Otherwise plain outcomes such as reuse, adapt, build, or unresolved are sufficient. These classifications do not replace rationale.

For unavailable evidence, identify the unresolved assumption and affected work; continue independent design. A proposed compatibility test is a test plan, not evidence that compatibility exists. A source's architecture and benchmark results do not transfer automatically to a different environment.

Stop when the consequential claim is supported, conflicts have bounded implications, and further searching is unlikely to change the current decision. Research should not grow the milestone by collecting optional features.

## Evidence discipline

Maintain provenance through derived design decisions. A model-generated suggestion begins as an inference, not an observed requirement. Code inspection establishes only what was inspected. Tests establish exercised behavior under their setup. Measurements establish results for their workload/environment. Formal proof applies within its assumptions and model. Keep all of these distinct from an assurance of overall product correctness.
