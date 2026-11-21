# Adjudication: webapp-testing

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-20/compiler/webapp-testing-failed/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

## Requirement verdicts

- [ ] WT-4 (obligation): judge says weakened. Black-box use is required. The built skill does not say to consider a bundled script before writing custom code. Only with_server.py is used in the flow, and only when the server is not running. Quote: "run bundled scripts directly as black boxes, starting with --help"
- [ ] WT-13 (obligation): judge says weakened. This sits in a Taste section, and 'Use judgment on both' turns the source's best-practice obligation into a soft preference. It is not in the contract. Quote: "Use descriptive selectors (`text=`, `role=`, CSS selectors, or IDs). Add appropriate waits with `page.wait_for_selector()` or `page.wait_for_timeout()`. Use judgment on both."
- [ ] WT-14 (obligation): judge says weakened. Same as WT-13: the rule is softened to discretionary taste. Quote: "Add appropriate waits with `page.wait_for_selector()` or `page.wait_for_timeout()`. Use judgment on both."

## Introduced behavior that widens what the agent may do

