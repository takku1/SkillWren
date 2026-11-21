# Adjudication: webapp-testing

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-21-round2-attempt2/compiler/webapp-testing/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

Adjudicated by: ChatGPT (GPT-6), AI adjudication, 2026-11-21, relayed by the repository owner. Not independent human validation.


## Requirement verdicts

- [!] WT-3 (prohibition): judge says weakened. Source read is gated only on help output being insufficient (verify usage), not on a customized solution being absolutely necessary; the 'only when necessary' is in step meaning but the gate differs. Quote: "read helper source from scripts as source" -- Overturn (#9): WT-3 is preserved. The generated step meaning explicitly restricts reading helper source to cases where `--help` has been tried and a customized solution is absolutely necessary. The judge considered the logic branch without its qualifying step meaning.
- [x] WT-4 (obligation): judge says weakened. Black-box use is present, but there is no step to consider whether a bundled script can do the job before writing custom code; the helper is used only in the not-running-server branch. Quote: "treat bundled scripts as black boxes and invoke them directly" -- Agree (#10): WT-4 is weakened. The contract requires black-box treatment and direct invocation, but does not explicitly preserve the source's instruction to consider whether a bundled script can solve the task before developing custom code.

## Introduced behavior that widens what the agent may do

- [!] Writes a screenshot file to a fixed path as a required step Quote: "write #shot inspection with inspect_png" -- Overturn (#11): Not a widening introduction. The source explicitly demonstrates taking a full-page screenshot during rendered-state inspection. The generated fixed path `/tmp/inspect.png` is also present in the source example, so this is an authorized implementation detail rather than invented authority.
- [x] Windows-specific command substitution permission Quote: "On Windows use `py -3` when `python` is a Microsoft Store stub." -- Agree (#12): Widening introduction. The Windows-specific `py -3` substitution adds a platform-dependent command alternative not specified by the source. Although likely harmless and useful, it is still additional procedural behavior.
