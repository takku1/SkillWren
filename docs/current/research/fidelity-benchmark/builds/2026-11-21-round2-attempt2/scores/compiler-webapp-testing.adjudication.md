# Adjudication: webapp-testing

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-21-round2-attempt2/compiler/webapp-testing/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

## Requirement verdicts

- [ ] WT-3 (prohibition): judge says weakened. Source read is gated only on help output being insufficient (verify usage), not on a customized solution being absolutely necessary; the 'only when necessary' is in step meaning but the gate differs. Quote: "read helper source from scripts as source"
- [ ] WT-4 (obligation): judge says weakened. Black-box use is present, but there is no step to consider whether a bundled script can do the job before writing custom code; the helper is used only in the not-running-server branch. Quote: "treat bundled scripts as black boxes and invoke them directly"

## Introduced behavior that widens what the agent may do

- [ ] Writes a screenshot file to a fixed path as a required step Quote: "write #shot inspection with inspect_png"
- [ ] Windows-specific command substitution permission Quote: "On Windows use `py -3` when `python` is a Microsoft Store stub."
