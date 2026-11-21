# Adjudication: internal-comms

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-20/compiler/internal-comms-failed/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

Adjudicated by: ChatGPT (GPT-6), AI adjudication, 2026-11-20, relayed by the repository owner. Not independent human validation.


## Requirement verdicts

- [x] IC-5 (exception): judge says weakened. Clarification is asked only when the type matches neither a known guideline nor general comms. General is the catch-all, so it rarely fires. Unclear formats after routing, including the general fallback, do not trigger a question. Quote: "ask user to clarify the desired communication format" -- Agree (#5): IC-5 is weakened. The clarification condition is effectively unreachable when general communications are the catch-all, so an unclear desired format may pass through without clarification.

## Introduced behavior that widens what the agent may do

