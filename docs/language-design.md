# Language direction

SkillWren is a Markdown-based instruction language for LLM readers. The
implemented 0.5 grammar in SPEC.md is authoritative. This note introduces no
syntax or runtime guarantees.

The goal is original SKILL.md → smaller, logical SkillWren SKILL.md. Preserve
decisions, requirements, authority, recovery, and context needed to act correctly.
Use existing control vocabulary rather than duplicating the original prose in
the prompt. Archive source outside the prompt for provenance; keep reference
material in the prompt when execution needs it.

Separate static validity, reviewed rule preservation, and observed behavior.
The validator supports the first; hash-bound requirement maps support review
of the second; matched task trials provide limited evidence for the third.
None establishes the others. Character reduction is not token reduction, and
token reduction alone is not lower cost per verified change.

See [compact conversion](design/compact-conversion.md) for the implemented
measurement/review contract and [compiler](compiler.md) for commands.
