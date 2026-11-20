# Design note: response to the full-stack field report of 2026-11-19

Source: [field report](../research/full-stack-live-use-2026-11-19.md),
findings 5-8. Results: [three-tier report](../research/field-response-2026-11-19.md).

## 5. Exclusion order rules (`never A before B`)

**Problem.** Two fragments each checked clean, but one fragment's `write`
made a runtime gate in another fragment refuse to start. P1 can only say
"B needs A first". It has no way to say "B must not follow A".

**Decision.** Add one `order:` entry form, `never <earlier> before <later>`,
and a new rule P3. No new vocabulary: `never` already exists as a contract
word, and no logic statement can start with it, so the form is unambiguous.

- Within a file, P3 fires when a statement matching the later step is
  reachable after some path has already run a statement matching the
  earlier step. This is a may-analysis (some path), the dual of P1's
  must-analysis (every path).
- Across files, an exclusion rule declared in file F also applies to every
  flow that runs a flow of F, directly or transitively. A `run` whose callee
  may start the later step is checked like that statement. A `run` whose
  callee may run the earlier step counts as the earlier step. Callee
  summaries over-approximate: any reachable matching statement counts,
  including one only reached on paths that abort.
- `ledger start` records exclusion rules, and `ledger check` reports a
  violation when a recorded step matching the earlier step precedes one
  matching the later step. Attempts do, too: a failed write still happened.
- The guard (SPEC 22) does not enforce them. `status` lists them as
  unenforced.

**Limits.** The static check sees only composition that is written down as
`run`. Full-stack's core routes design and implement in prose, so the check
would catch its deadlock only once a flow composes them. The ledger sees
only steps recorded after `start`. Both limits are stated in SPEC 23.

**Rejected.** Attaching preconditions to `exec` (`exec ... requires no
write`) would add statement syntax and a second precondition notion beside
`order:`. A heuristic that guesses effect conflicts from prose would be
unsound.

## 6. Package provenance in the ledger

**Problem.** The agent read 0.8.0 instructions, a 0.8.0 hook enforced
them, and 0.8.2 scripts wrote a ledger that recorded only the flow file's
digest. Nothing showed the mismatch.

**Decision.** `ledger start --package DIR` records a tree digest of DIR
(sha256 over sorted `name sha256` lines of every file, skipping VCS,
caches, run state and `manifest.json`), the manifest's own digest when one
exists, and fails if the flow file's bytes differ from the package's copy.
`ledger check --loaded DIR` recomputes the tree digest of the copy the host
actually loaded (for example, the plugin cache) and fails on a mismatch, or
when the run recorded no package. The tree digest of a `build` artifact
equals that of its source, and `build` now writes it to the manifest as
`tree_sha256`.

**Limits.** The caller has to know and pass the host-loaded path, and the
ledger cannot see what the host actually put in the model's context. It
binds files, not context.

## 7. Order rules hold only inside entered fragments

No code. The authoring guide and SPEC 23 tell authors to pair a fragment's
order rules with a required milestone (`ledger start --require`) for its
entry step when skipping the fragment would matter. A skipped fragment then
shows up as `incomplete` instead of vacuously `valid`.

## 8. One typed-reference grammar

SkillWren itself had the defect: the ledger, the order matcher, the P2
checker, the return parser and the workflow renderer each carried their
own regular expression, and the renderer's (`#[A-Za-z][\w-]*`) accepted IDs
the validator ignores. The grammar now lives once in
`validator/refs.py`, and a test runs every consumer against one table of
accepted and rejected IDs.
