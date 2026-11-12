# Language direction

SkillWren is a Markdown-based instruction language for LLM readers. The
implemented 0.6 grammar in SPEC.md is authoritative. This note introduces no
syntax or runtime guarantees.

**What it is for.** Checking procedure structure that prose leaves implicit:
branches, gates, who decides, what is touched, how failures recover, and,
from 0.6, what must happen before what. The checked unit is the `logic`
block, in a complete skill or as a fragment inside an ordinary flow file.

**What it is not for.** Routing (hosts route on `description`) or prompt
compression for its own sake. The header and its routing protocol remain
optional conventions; full-stack, the format's one long-term user, dropped
the header after measuring its cost.

**Conversion.** Original SKILL.md → smaller, logical SkillWren skill remains
supported: preserve decisions, requirements, authority, recovery, and the
context needed to act correctly; archive the source outside the prompt.

**Three claims, kept separate.** Static validity (the validator), reviewed
rule preservation (hash-bound requirement maps), and observed behavior
(matched task trials and `conform` runs). None establishes the others.
Character reduction is not token reduction, and token reduction alone is
not lower cost per verified change.

**Direction.** Procedure-following research finds agents complete tasks far
more often than they follow required steps, and that runtime enforcement of
ordering closes much of that gap. The next step is compiling order rules and
evidence gates into host hooks or guard preconditions, then measuring with
content held constant ([review 2026-11](research/research-review-2026-11.md)).

See [fragments and ordering](design/fragments-and-ordering.md),
[compact conversion](design/compact-conversion.md), and
[compiler](compiler.md).
