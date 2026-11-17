# Batch 4 intents

f16: Take the fast path only when the fast flag is set; otherwise skip
it and return the request.

f17: Act only while the window is open: verify it, abort if it shut,
and book the slot inside the window.

f18: Redact the draft and write the clean result. Redaction happens
in memory first.

f19: Build in stages: generate parts, generate the assembly from them,
verify the assembly against a fresh check, then write it. Mismatch
aborts.

f20: Show the audit report to the requester. Showing is advisory:
nothing here can be enforced.
