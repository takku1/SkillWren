# Build flow (fragment template)

Copy this file into your skill's `flows/` folder. `SKILL.md` keeps only
`name` and `description` plus a short core that says when to read this
file. Check it with `skillwren check --fragment flows/build.md`, and add
`--summary` to see the inputs the checker inferred and `--audit` to see what
each gate and order rule rests on. Rules: SPEC Section 20. Each order rule's
earlier step should leave a signal outside the model (an `exec` result cited
with `verify ... from`, a written artifact, or a user decision); otherwise
W15 warns that the rule is a self-report.
Everything outside the fenced blocks is guidance the model reads; the
`Step meanings` list defines each `apply` step (W12).

```contract
inputs:
  request, design, subject
order:
  verify design has an assurance table before write implementation
  write implementation before exec acceptance checks
```

```logic
build:
  require request exists
    otherwise:
      abort with "A request is required."

  unless design is known:
    run design from flows/design.md with:
      request = request

  exec assurance table check from checks as screen
  verify design has an assurance table from screen
    otherwise:
      apply assurance screen with design as design
      write design with design_docs
      exec assurance table check from checks as screen
      retry

  generate implementation from design as implementation
  write implementation with subject
  exec acceptance checks from checks as results

  verify every criterion passed from results
    otherwise:
      apply correction with implementation as implementation
      write implementation with subject
      exec acceptance checks from checks as results
      retry

  return:
    implementation
    report = results
```

## Step meanings

- **assurance screen**: answer the risk questions and add the raised
  disciplines' checks to the design.
- **correction**: repair the failing edit; the same failure twice with the
  same evidence becomes a reported blocker, not another repair.

## Commands

Run acceptance checks as an argument list or a script file. Pipes,
redirects, and shell one-liners go in a script (SPEC Section 6). On Windows
use `py -3` when `python` is a Microsoft Store stub.

```sh
py -3 scripts/run_checks.py --each "unit :: pytest -q"
```
