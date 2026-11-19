# Existing projects and Recurspec integration

## Establish authority

Identify the governing architecture, work registry, glossary, conventions, and relevant code/tests. Follow actual flows rather than inferring behavior from directory names. Preserve IDs and historical rationale. When documents disagree, investigate the affected claim and record which statement is target design versus observed implementation.

Work at the requested scope. Reuse existing providers through their contracts. A proposal to replace an owner needs evidence that the selected outcome requires it. Do not create a parallel architecture tree to avoid dealing with the existing one.

For uncertain runtime claims, run a relevant check when feasible and useful. Otherwise state what code was inspected and what execution evidence remains absent. Avoid expensive whole-project testing for a documentation-only comparison.

## Design deltas

Describe current behavior, desired behavior, affected boundaries, and an incremental migration. Preserve valuable existing behavior and specify temporary adapters' removal conditions. Keep current and target diagrams labeled if both are necessary.

A roadmap row marked done is evidence of a recorded claim, not independent verification. Conversely, do not mark implemented behavior missing merely because an old brainstorm omitted it. Check the governing architecture and current code before issuing a finding.

## Recurspec projects

When the subject repository uses Recurspec, read its local rules and contracts. If the CLI is available, use read-only status to orient the relevant tree; if unavailable, inspect the artifacts and report that CLI validation was not performed. Full Stack does not install tools or modify a whole tree merely to enable its own planning.

Preserve `SYSTEM.md` contracts, existing contract markers/schema, and `ROADMAP.md` as the work registry. Link user-facing concept documents to the owning contract; do not duplicate normative interface definitions. Coverage suggestions remain proposals until resolved within the subject project's workflow.

Map Full Stack's requirements/components to existing Contract Nodes where appropriate. Work packages remain delivery units; do not assume a one-to-one mapping to nodes. Use Recurspec's existing evidence labels and decision classes without silently changing their meaning.

For accepted contract edits, follow the repository's required validation. Full Stack does not manufacture probe files, metric values, or formal-proof tags to make a design appear complete. Candidate execution, checker separation, evaluation, and merge authority belong to Recurspec when that workflow is invoked.

## Standalone use

No dependency on Recurspec or Architectural Reasoning is required. Preserve another project's conventions if it uses different names or tools. If there is no established structure, place a design brief plus necessary component/flow specifications under `docs/design/`, and use the existing roadmap or create one when implementation work needs tracking. Do not generate a separate readiness checklist for every component.
