# Side-by-Side Report: systematic-debugging (prose) vs systematic-debugging-logic (0.4.1)

Date: 2026-10-01. Evaluator: Muse Code session (single-blind walkthrough).
Original: user skill `systematic-debugging` (9.5 KB prose, four phases +
red flags + companion files `root-cause-tracing.md`, `defense-in-depth.md`,
`condition-based-waiting.md`).
Draft: `SKILL.md` in this directory (4.8 KB contract + gated `debug-issue` flow).

## 1. Static comparison

What the draft encodes well: the gated flow preserves the original's spine
(symptom → context → prove reproducible → investigate loop → failing test
first → single fix → verify → 3-strikes abort to architecture discussion).
The 3-strikes rule and failing-test-before-fix both survive as hard gates,
the explicit `otherwise` loopbacks improve on the original's implied flow,
and the machine-readable header (accepts/produces, authority,
effects, risk/cost) adds orchestration capability the prose version lacks.

Fidelity gaps (static read):

1. Phase 2 (Pattern Analysis) is absent from the gates. The flow jumps
   from "read recent changes" to "generate hypothesis" with no
   working-examples lookup, reference read, or differences list. The
   appendix name-checks it in one line; nothing enforces it.
2. The probe gate has no content. "Generate diagnostic instrumentation"
   is gated, but the original's per-boundary enter/exit/state checklist
   and worked example did not come along.
3. No clean exit for genuinely-external issues. The original's terminal
   handling (environmental/timing/external → document + handle + monitor)
   has no counterpart; that case burns all three attempts or loops.
4. Pressure teeth dulled: rationalizations table, partner-signal decoder,
   and "when you don't know, say so" compress to two appendix sentences.
5. Companion techniques thin to one paragraph each (acceptable; the draft
   honestly defers to the sibling directory).

Pre-install issues: the draft claims `name: systematic-debugging`,
colliding with the installed original — pilot as `systematic-debugging-logic`
(the directory name) so they coexist. `budget.body` (2500) appears
smaller than the actual body (~3700 bytes) — confirm the unit. Minor:
frontmatter carries both `skill:` and `name:` with the same value, and
"show probe" doesn't say to whom.

## 2. Live-fire test on MochiOS work

Test case (real open bug): `fetch https://api.anthropic.com` from the
MochiOS guest fails with a TLS handshake I/O error after 1 send + 7
successful reads, no second send, then close. No denials, no crash.
Reproduced across boots; the failure evolved (unimplemented → OOM →
transport-io) as earlier layers were fixed and verified.

Method: the same evaluator walked the bug through each process and recorded
the prescribed next step. Single-blind (one reader, both skills) — a
stronger design would run two agents, one per skill, on a fresh bug.

Original (prose) applied:

- Phase 1.4 (instrument boundaries) prescribed exactly the missing
  evidence: failure timing (fast vs hang) and the verbatim error line
  before any new hypothesis. It also blesses the host-vs-guest split
  (curl works on host, guest fails) as boundary instrumentation.
- Phase 2 (working examples) has been decisive twice on this bug's
  history: DNS-copy-works vs RECV-copy-fails isolated the garbage
  pointer; host-curl-works vs guest-fails frames the current question.
- Phase 3 forces one falsifiable hypothesis ("peer sent FIN/RST after a
  truncated flight-2") with the timing answer as the falsifier.
- The 3-strikes rule correctly does NOT fire: 4.5 qualifies it to the
  thrashing pattern (fixes revealing coupling elsewhere / creating new
  symptoms), and this session is a verified stack-peel (each fix
  confirmed: copy now delivers, OOM gone, records flowing).

Draft (logic gates) applied:

- Gates 1–3 (symptom → context → reproducible?) pass mechanically.
- "Generate root cause hypothesis from changes" misfires: this bug
  predates the session's changes, so deriving hypotheses from the diff
  points at our own verified fixes rather than at server/transport
  behavior. The original treats recent changes as one input among
  several; the draft makes it the hypothesis source.
- With Phase 2 absent, nothing prompts the DNS-vs-RECV or
  host-vs-guest comparisons — the steps that cracked two of three
  layers on this bug.
- The multi-component probe gate fires correctly and prescribes the
  host repro probe — same correct destination as the original.
- The 3-strikes gate false-fires: it counts three verified layer fixes
  as strikes ("attempts exhausted → abort") with no equivalent of the
  original's pattern check. Applied literally it would halt the session
  for architecture discussion at exactly the wrong moment.

| Step | Original | Draft |
|---|---|---|
| Demand missing evidence first | Yes (1.4) | No gate for it |
| Working-example comparison | Yes (Ph.2), decisive 2x | Skipped entirely |
| Hypothesis source | Evidence + changes | Changes only; misfires here |
| Repro-before-fix | Yes (4.1) | Yes (gated) |
| 3-strikes discipline | Pattern-qualified, correct no-fire | Blunt count, false-fires |

## 3. Recommendations

1. Add a Phase 2 gate (working example + reference read + differences)
   before hypothesis generation — the live fire shows this is the
   highest-value missing gate.
2. Give the probe gate content: per-boundary enter/exit/state checklist
   (port the original's, compressed).
3. Qualify the strike counter with the original's 4.5 pattern check
   (coupling? new symptoms?) so verified stack-peels don't abort.
4. Resolve the install name (`systematic-debugging-logic`), the budget
   unit, and the `skill:`/`name:` duplication before broader piloting.
5. Stronger evaluation when convenient: two agents, one skill each, on a
   fresh bug, scored on time-to-root-cause and false-fix count.
