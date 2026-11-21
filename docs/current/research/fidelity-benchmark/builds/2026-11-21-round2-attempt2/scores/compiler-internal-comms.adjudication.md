# Adjudication: internal-comms

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-21-round2-attempt2/compiler/internal-comms-failed/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

## Requirement verdicts

- [ ] IC-5 (exception): judge says weakened. Clarification is asked only before routing. The general-comms fallback means nothing is unsupported after routing, so the source's ask-when-unmatched case is narrowed. The built skill also falls back to returning a gap if the user does not confirm. Quote: "if comm_type is unclear or matches no existing guideline:"

## Introduced behavior that widens what the agent may do

- [ ] Runs a check command from a `checks` collection to verify the guideline was loaded, and aborts if it fails Quote: "exec guideline load check from checks as loaded"
