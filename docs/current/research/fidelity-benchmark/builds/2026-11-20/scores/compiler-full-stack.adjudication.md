# Adjudication: full-stack

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-20/compiler/full-stack-failed/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

## Requirement verdicts

- [ ] FS-11 (ordering): judge says weakened. Source requires recording before committing; built only orders the record as a step, with no explicit before-commitment ordering. Quote: "if a commitment is costly to reverse:
    apply commitment record with design as design
    write #costly design with registry"
- [ ] FS-12 (exception): judge says weakened. Condition matches, but it also adds another ask when design-only vs implementation is ambiguous, which widens asking beyond the source. Quote: "if a missing answer changes the outcome or authority:
    ask user to settle the missing outcome or authority decision"

## Introduced behavior that widens what the agent may do

