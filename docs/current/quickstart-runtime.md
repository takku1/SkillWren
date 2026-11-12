# Five-minute runtime walkthrough

SkillWren finds defects in written procedures. Its experimental guard can
also deny writes **when the host gives it exclusive control of those writes**.

Run from this checkout (replace `py -3` with `python3` on Linux/macOS):

```text
py -3 scripts/skillwren.py check --fragment tests/fixtures/fragments/skill/flows/build-gap.md
py -3 scripts/skillwren.py check --fragment --audit tests/fixtures/fragments/skill/flows/build-fixed.md
py -3 scripts/guard_demo.py
```

The first command reports P1: a path can write before its prerequisite.
The corrected flow establishes the prerequisite on every path. The demo
then really denies an unverified write, verifies a candidate with a fixed
verifier, writes it, and denies replay. It operates in a temporary directory.

## Stable references

Use `verify#security before write#config` in `order:` and statements
`verify #security ...` / `write #config ...`. The ID binds exactly; changing
incidental prose preserves it. IDs must be unique within a document (P2).
Use unique IDs across participating flow files to avoid ambiguous intent.
Text-prefix rules remain available for compatibility.

For correlated branch conditions, use an explicit verifier result or nest
the dependent operation inside the condition that establishes its input.
Do not ask the analyzer to assume natural-language implications. The guard's
verifier is an executable refinement: this example accepts only JSON objects
with literal `debug: false`, then binds approval to the exact bytes.

## Run the controller

Create an existing, host-owned output directory, then generate example policy:

```text
py -3 scripts/guard_policy.py --target /absolute/protected/config.json --out policy.json
py -3 scripts/skillwren.py guard policy.json --audit events.jsonl --checkpoint /independent/anchor.json
```

The second command reads one JSON object per line and responds in JSON:

```json
{"action":"verify","operation":"write#config","content":"{\"debug\":false}"}
{"action":"write","operation":"write#config","content":"{\"debug\":false}"}
```

Send EOF to close the session. A denied request has `ok:false`. There is no
request field for a path, command, evidence assertion, policy change or
checkpoint replacement. Restart discards approvals. Changed candidates or
targets require new verification. A failed verifier revokes old approval.

Run one controller per protected output set and audit pair. Store policy,
verifier scripts, their runtime dependencies, protected output and checkpoint
outside the agent's writable filesystem. Pins cover configured files, not
all transitive interpreter dependencies. Treat those dependencies as trusted
host software. Never expose this stdio process through an unauthenticated
network service. A same-account unrestricted shell can bypass this boundary.

The log records request digests, outcomes and start/stop events without raw
candidate content. A missing checkpoint, changed retained head or unfinished
intent fails closed. Host recovery must reconcile the actual output and
preserve the old log before starting a fresh run; do not manufacture a passing
checkpoint. Checkpoints do not provide authenticity if an attacker owns both
files. No complete-host activity coverage is claimed.

## Test the isolation boundary

```text
py -3 scripts/isolation_probe.py
```

Requires Docker and the pinned Python image named by the script. It exposes
no host mount to the attacker and checks denied direct writes, denied network,
absence of Docker socket, and the mediated write path. See the retained
[results](research/isolation-results.json). This is an adversarial mechanism
test, not evidence that any particular model follows procedures better.

`skillwren sandbox --image NAME@sha256:DIGEST --workspace DIR --allow PATTERN
-- COMMAND ARGS` runs a command in a disposable workspace copy with no network,
a read-only root, dropped capabilities and resource limits. It reports final
undeclared file changes. Allowed workspace and temporary-file transients are
not observed. `conform` remains a Claude session observer; it is not silently
routed through this offline container, which cannot call model APIs.
