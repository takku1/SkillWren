# Requirement review: full-stack (0.2 prose)

Source: sources/full-stack/SKILL.md
Reviewed by: <your name>
Date: <YYYY-MM-DD>
Candidate status: AI-drafted, AI-reviewed twice (drafting session; external AI review
2026-11-20). Not human-approved: freezing needs the human reviewer's name and date.

**How to review.** These are model-drafted candidates. For each line: keep it
(`[x]`), drop it (change to `[ ]`), or edit the requirement text so it says
what the source really requires. Add anything missing as a new line with the
next free ID (`FS-24`, ...); quote the source span, or write `inferred` if you
accept it without one. Kinds: obligation, prohibition, exception, ordering,
authority, output. Then fill in the two lines above.

This is the densest source: it is the one you know best, so it gets the
most scrutiny from you, not from the drafter.

- [x] FS-1 | authority | Planning is the default; a request to build or implement authorizes implementation only within that scope. | "Planning is the default; a request to build or implement authorizes the implementation path within that scope."
- [x] FS-2 | authority | Follow existing task authorization without asking for approval again. | "Follow existing task authorization without repeated approval."
- [x] FS-3 | authority | Deployment, publication, tool installation and delegation are not authorized by a build request; they need their own permission. | "Deployment, publication, tool installation, and delegation follow their own applicable permissions."
- [x] FS-4 | obligation | Identify the subject repository, outcome, selected work IDs, constraints and exclusions. | "Identify the subject repository, outcome, selected work IDs, constraints, and exclusions."
- [x] FS-5 | obligation | Inspect applicable instructions and representative code, contracts, tests and prototypes. | "Inspect applicable instructions and representative code, contracts, tests, and prototypes."
- [x] FS-6 | obligation | Preserve authoritative documents, IDs and project vocabulary. | "Preserve authoritative documents, IDs, and project vocabulary."
- [x] FS-7 | obligation | Keep current state, target state and migration distinct; documentation and mock data do not establish working behavior. | "documentation and mock data do not establish working behavior"
- [x] FS-8 | obligation | Classify discoveries and proposed mechanisms as required now, existing dependency, unresolved prerequisite or deferred enhancement. | "Classify discoveries and proposed mechanisms as"
- [x] FS-9 | prohibition | Discovery does not authorize expansion or replacement. | "discovery does not authorize expansion or replacement"
- [x] FS-10 | obligation | Resolve ambiguity from evidence, state consequential assumptions, and continue with reversible ordinary choices. | "State consequential assumptions and use reversible ordinary choices to continue."
- [x] FS-11 | ordering | Before a costly-to-reverse commitment, record its consequences, migration or reversal options, and affected work. | "record consequences, migration/reversal options, and affected work before committing"
- [x] FS-12 | exception | Ask for clarification only when a missing answer changes the outcome or authority. | "seek clarification only when a missing answer changes the outcome or authority"
- [x] FS-13 | obligation | Preserve settled user decisions. | "Preserve settled user decisions."
- [x] FS-14 | obligation | Load references only as needed. | "Load references only as needed"
- [x] FS-15 | obligation | Trace behavior from trigger through state transitions to result, including failure, retry, cancellation and recovery. | "including relevant failure, retry, cancellation, and recovery"
- [x] FS-16 | obligation | Use one authority per state set, or an explicit coordination protocol. | "Use one authority per state set or an explicit coordination protocol."
- [x] FS-17 | obligation | Research uncertainty that could change the design; preserve valid existing choices. | "Research uncertainty that could change the design"
- [x] FS-18 | obligation | Label test doubles with their simulated guarantees, limits and replacement conditions; they do not establish operational integration. | "Label doubles and their simulated guarantees, limits, and replacement conditions"
- [x] FS-19 | obligation | Keep requirements, assumptions, inspection, executed tests, measurements and proof distinct, and mark unexecuted checks. | "Mark unexecuted checks"
- [x] FS-20 | obligation | Maintain one authoritative work registry in the subject project. | "Maintain one authoritative work registry in the subject project."
- [x] FS-21 | output | Design-only work delivers scope, linked design, ownership and contracts, research-backed choices, ordered increments and blockers, and says what is ready versus conditional. | "Identify what is ready versus conditional."
- [x] FS-22 | obligation | Authorized implementation continues through the selected acceptance criteria; a first working increment does not complete the milestone. | "Design readiness and a first working increment do not mean the milestone is complete."
- [x] FS-23 | obligation | Explain excluding a material quality concern, without adding unrelated scope. | "Explain excluding a material concern without adding unrelated scope."
- [x] FS-24 | obligation | Match each consumer's assumptions to provider guarantees, or record them as explicit unresolved conditions. | "Match consumer assumptions to provider guarantees or explicit unresolved conditions."
- [x] FS-25 | ordering | Resolve consequential reuse before detailing custom internals. | "resolve consequential reuse before detailing custom internals"
- [x] FS-26 | obligation | Stop at adopted providers' public boundaries and allocate the required fit gaps. | "Stop at adopted providers' public boundaries and allocate required fit gaps."
- [x] FS-27 | prohibition | Components do not dictate files, packages, services, processes or teams; screens, nouns, directories and workflow steps do not dictate components. | "components do not dictate files, packages, services, processes, or teams"
- [x] FS-28 | obligation | Split components where different decisions need hiding, authority changes hands, protection or lifecycle differs, or coupling prevents a coherent increment. | "Split where different decisions need hiding, authority changes hands, protection/lifecycle differs, or coupling prevents a coherent increment."
- [x] FS-29 | ordering | Resolve shared interface work before claiming that increments are independent. | "resolve shared interface work before claiming independence"
- [x] FS-30 | prohibition | Do not freeze requirements before exploring architecture; iterate as evidence changes. | "do not freeze requirements before exploring architecture"
- [x] FS-31 | obligation | An increment is design-ready only when its outcome, contracts, prerequisites and checks are usable and its consequential decisions are resolved. | "A next increment is design-ready when its outcome, contracts, prerequisites, and checks are usable and consequential decisions resolved."
- [x] FS-32 | obligation | Separate prototype appearance and interaction requirements from simulated behavior. | "Separate prototype appearance/interaction requirements from simulated behavior."

## Revision log

- FS-24 (consumer/provider contracts), FS-25 (resolve reuse first) and FS-27 (components are not deployment units) added from the external AI review's list of missing architectural constraints.
- FS-26, FS-28 to FS-32 added on a second reading of the source for the same reason: each can change a generated design (provider boundaries, split criteria, shared interfaces before independence, no early freeze, design readiness, prototype vs simulated behavior).
