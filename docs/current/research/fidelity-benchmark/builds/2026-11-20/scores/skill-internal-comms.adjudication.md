# Adjudication: internal-comms

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-20/skill/internal-comms-sonnet/files/internal-comms-logic/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

## Requirement verdicts

- [ ] IC-5 (exception): judge says weakened. The built skill asks for clarification only when the type cannot be classified at all, and that check happens before routing. Anything unclear goes to the general fallback with no question. The source asks when the format doesn't match any guideline. Quote: "if comm_type is too unclear to classify at all:"

## Introduced behavior that widens what the agent may do

