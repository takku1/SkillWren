# Logic review (converted flow only)

`require target exists`: subject present, proceeding. Read: project
instructions, caller.py diff, vulnerable.py and style_nit.py as
necessary callers/context.

`generate`: one consequential finding with a reachable failure case
(injection via CLI argument into `shell=True`); the unused variable is
style-only and excluded (no style review requested).

`verify #evidence`: the finding has location (`caller.py:7`,
`vulnerable.py:8`), trigger (crafted CLI argument), consequence
(arbitrary command execution), and supporting source (interpolation
into `shell=True` with attacker-controlled input). Verified.

`generate report`: impact-ordered (one high), minimal correction
(argument list plus input validation), independent verification
advice (regression test keyed to the argument-list convention),
limitations (style nit excluded; nothing executed), unrun checks
(regression test, wider `shell=True` grep). Severity per appendix:
reachable breach of execution boundary = high.

## Report

Summary: one confirmed high-severity reachable command injection; one
style observation excluded. Finding, correction direction, verification
advice, limitations, and unrun checks as above. No unverified concerns
required a separate section on this subject. No other findings confirmed;
that does not establish the change is otherwise correct.
