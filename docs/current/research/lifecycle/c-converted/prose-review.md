# Prose review (original.md only, no SkillWren logic)

Scope: INSTRUCTIONS.md, caller.py (the change), vulnerable.py and
style_nit.py as context. Conventions: argument lists, never shell=True
with interpolation. No edits, refactors, or command execution.

## Summary

One confirmed high-severity finding: reachable command injection from
CLI input through `caller.py` into a `shell=True` call. One style-only
observation excluded.

## Findings

**[High] Command injection via `sys.argv[1]` -> `shell=True`.**
Location: `caller.py:7` passes `sys.argv[1]` to `find_user`;
`vulnerable.py:8` interpolates it into `"getent passwd " + name` run
with `shell=True`. Trigger: `tool caller.py "$(touch pwned)"`.
Consequence: arbitrary command execution as the invoking user.
Correction direction: pass an argument list (`["getent", "passwd",
name]`) and validate `name` against `^[a-z_][a-z0-9_-]*$`.
Verification suggestion: regression test calling the fixed function
with `"; touch /tmp/pwned-test"` and asserting no file is created and
the lookup still works; expected result comes from the project
convention (argument lists), not from current output.

## Limitations

`style_nit.py:2` (`_unused_default`) is style-only and excluded; no
style review was requested. I did not run any commands; the injection
is established from source (string interpolation into `shell=True`
with an attacker-controlled argument), not from execution.

## Unexecuted checks

The suggested regression test above; a grep for other `shell=True`
call sites in the wider repository.
