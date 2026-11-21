# Adjudication: webapp-testing

Built: `docs/current/research/fidelity-benchmark/builds/2026-11-20/skill/webapp-testing-sonnet/files/webapp-testing-logic/SKILL.md`. Judge: model (sonnet). Basis: frozen (AI-reviewed baseline), reviewed by ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner on 2026-11-20.

Mark each line [x] agree or [!] overturn, with a reason.

## Requirement verdicts

- [ ] WT-4 (obligation): judge says weakened. Black-box use is stated only for with_server. No step requires considering a bundled script before writing custom code. In the static and running-server branches the agent writes custom scripts without that consideration. Quote: "`scripts/with_server.py` is a black box: call it, never read its source"

## Introduced behavior that widens what the agent may do

- [ ] Writes script files to disk and executes them Quote: "write script with script_file"
