# NL compiler benchmark: full-stack 0.2.0 prose

Frozen 2026-11-18. The first full-context source for `skillwren compile`:
a real prose skill with its reference files, plus the hand conversion made
when full-stack adopted SkillWren.

## Provenance

- `source/`: `skills/full-stack/` at full-stack commit `4690106`, the last
  prose-only package (version 0.2.0): the 48-line `SKILL.md` entry and six
  on-demand references (271 lines). About 8k tokens in total.
- `reference/full-stack-logic.md`: the hand conversion from full-stack
  commit `59e1d4f` ("Add SkillWren logic pilot", SPEC 0.4.1, complete-skill
  layout), with its self-review `pilot-report.md`. It still checks clean
  under the current validator, with W12 warnings for undefined `apply` specs.

The reference is one author's conversion, not ground truth. It made design
choices the prose does not force (for example, routine edits as the first
branch, declined commitments marking the design conditional). Compare
against it; don't score against it.

## How to run

```sh
skillwren compile docs/current/research/nl-compiler/full-stack-0.2/source/SKILL.md \
  --context .../source/references/artifacts.md   # one --context per reference
  --out <new dir> -- py -3 scripts/adapters/claude_compile.py
```

Record per run: valid after repair, inventory size and non-requirements,
open findings, unbacked verifies, judge dropped/added/changed, questions,
assumptions, cost. Results go in `runs/` beside this file.

## Manifest (sha256)

359499366e2bd4e3a4c0223cd7d4c144d158cdf5ac5562d8f08b16267f90095c  source/SKILL.md
0161439f82fc4d8ff7cb02f3acf97a51d458f7c40eb28cef3d6479ed7170a211  source/references/artifacts.md
e6db97d3bff48c91cec724bac1deb789a03a0311ee484a54b394cfe58cb70261  source/references/design-method.md
4cca5ae4b198c4e689b8583ac1c8b489a849fd8f774ceb5ce464772b0dd55e26  source/references/existing-projects.md
18e631f5cfd294e8059bfce59f1e4e2bb966b0e951b9dab80ec46c1496285a57  source/references/implementation.md
9066217c6a9926bf0188416e77e7c7f4401df10327ba918f8f769ab7f57f5720  source/references/research.md
070df18b9f85f4f0432bfc8bad341afac45df85025211cca6a31482fa19f1b0f  source/references/terminology.md
4a82a9865bfff656b1dc02be62c5b07483f192978c2506ec83c999df883889f1  reference/full-stack-logic.md
2c464a907b5f1dc998b887b489da5c3ec08deead5eda13a83eb618b335433d23  reference/pilot-report.md
