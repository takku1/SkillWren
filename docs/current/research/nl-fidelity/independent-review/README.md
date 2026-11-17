# Independent review of the frozen corpus (2026-11-17)

Reviewer: a fresh headless Claude session (Opus 5.5), no tools, no
repository, no user settings; harness `scripts/corpus_review.py`, following
the packet in `../FROZEN.md`. Pass 1 saw only each intent and the
deterministic `explain-workflow` output, never the flow file or the facts.
Pass 2, a separate session, checked the pass-1 notes against the facts.
This is independent of the authoring session but not of the model family,
and it is not a human review. Cost $0.95.

## Result

- Facts recovered: 82/83. The one miss (pairs16 f19, "finished
  assembly") was dropped from the reviewer's notes, not from the
  explanation.
- 59 intent-mismatch notes. Most restate limitations the explanation
  already declares (guard enforcement needs a policy; untyped `exec` is
  advisory; prose meaning is unchecked). Those confirm the limits are
  legible to a reader.

## Defects found in the corpus (frozen bytes left unchanged)

- pairs16 f17: the verify sits inside `when window is open:`, so a shut
  window skips to `return` instead of aborting as the intent says.
- pairs21 f22: restart and reload are followed by an unconditional abort,
  with no health re-check; the intent aborts only "if still unhealthy".
- 05: the intent asks for a summary; the flow returns the request with no
  summarize step.
- Unrequested `require <input> exists` gates in 03, f08, f14, f16-f18,
  f21ingest and f24: the author added them, the intents never say them.
  Model drafts show the same habit.
- pairs06 f07: the intent says "three-step" over four steps (wording).

## Defect found in the explainer (fixed in 0.9.0)

Readers could not tell what `retry` re-runs or what a gate with no
`otherwise` does (pairs06 f09, 03). The explainer now says `retry`
"re-runs the failed gate '...' (line N) after the repair steps above; no
retry limit is stated" and spells out the spec's default failure for
`require` and `verify` gates.

## Status

Corpus scores may now be cited with this reviewer's caveat. A corrected
corpus (v2) should fix the four semantic defects above and drop or
justify the extra gates; re-freeze it under a new manifest rather than
editing these bytes.
