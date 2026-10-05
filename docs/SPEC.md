# SkillWren — Skill Logic Architecture (Contract-Header + Logic-Body)

- Date: 2026-10-01
- Status: v0.4.1 (2026-10-01)
- Source idea: `brainstorm - to be deleted.md` (theme-factory agent-DSL sketch)
- Direction: contract-header + logic-body (direction 1 of 3 proposed; user-approved)
- Document set: this spec (contract), `authoring-guide.md` (authoring
  procedure, template, checklists), `../examples/theme-factory.golden.md`
  (worked golden example). Shipped with the SkillWren validator
  (`src/skillwren/`, CLI: `skillwren check <file>...`).

## 1. Problem and goals

Natural-language skills are verbose, imprecise, and context-hungry. Agents
misread prose, load full skill bodies to decide relevance, re-read files while
chaining, and improvise where they should gate. This spec defines a logic-first
skill format that is frictionless to trigger and tight on context.

Goals:

1. Cut context: relevance decisions use ~400-token headers, never full bodies.
   This is the SkillWren routing convention for tooling that adopts it;
   current hosts (Claude Code, Codex) select skills from `name` and
   `description` only (Section 16).
2. Raise precision: sequencing, gates, authority, and effects are mechanically
   checked; transform specifications (`apply`/`generate` prose) are structured
   but advisory — prose describes meaning, including what a transform should do.
3. Stay frictionless: plain `.md` files that work with today's agents and gain
   checking/enforcement as tooling adopts the spec.
4. Be verifiable: a static validator answers "what can this touch, what does it
   require, who decides" without executing anything.

Release criteria: headers fit the token ceiling; converted skills use at
most half the tokens of their prose equivalents; zero undeclared mutations in
eval scenarios; every required gate fires; user dismissals never mutate.

## 2. Non-goals (YAGNI cuts)

- No constrained decoder or execution runtime (direction 2). The spec is
  enforceable later; this release is contract plus static validation.
- No automatic prompt compression (direction 3). Structure delivers the first
  context win; compression layers on afterward.
- No named reusable failure handlers, no skill inheritance/imports, no
  versioning story, no marketplace, no new file extension.

## 3. Research grounding

- Formal-LLM (CFG to pushdown automaton constrains agent plans):
  <https://arxiv.org/html/2402.00798v4/>
- Grammar prompting for DSL generation with LLMs:
  <https://arxiv.org/pdf/2305.19234>
- LTL specs plus constrained decoders for agent behavior:
  <https://arxiv.org/abs/2310.08535v1>
- Contract2Tool (preconditions, effects, risk, cost per tool):
  <https://arxiv.org/html/2606.07904>
- Agent Behavioral Contracts: preconditions, invariants, governance, recovery,
  with probabilistic satisfaction under LLM nondeterminism
  (see awesome-formal-llm-agents survey list):
  <https://github.com/zechang-xiong/awesome-formal-llm-agents>
- Safe LLM agents survey (PDDL-style domains: types, predicates, action schemas
  with preconditions and add/delete effects):
  <https://arxiv.org/pdf/2608.14590>
- LLMLingua / LongLLMLingua (prompt compression, fewer tokens with gains):
  <https://arxiv.org/abs/2310.05736>

Guiding principle (from the brainstorm doc): natural language describes meaning;
formal structure describes control.

## 4. Architecture overview

Each skill is one Markdown file with two tiers. The contract header (YAML
frontmatter under the SkillWren Frontmatter Profile) declares selection and
safety metadata. The logic body (fenced `logic` blocks plus one `contract`
block) defines named flows over a closed control vocabulary with gates,
invariants, and local recovery. Optional prose appendices cover steps that
are genuinely creative and must not be proceduralized.

Lifecycle: author writes header plus body; validator checks the file statically;
the agent loads headers only, routes by trigger plus satisfied preconditions,
loads the winning body on demand, executes gates in order, and chains via typed
`run`. Five units with clean interfaces: header schema, body language,
validator, router/loader convention, authoring template.

## 5. Contract header schema

Frontmatter fields (all machine-readable; prose values stay one line):

```yaml
skill: theme-factory        # kebab-case id
name: theme-factory
description: Style an artifact using a coherent visual theme.
version: 0.4
purpose: Style an artifact using a coherent visual theme.
accepts:
  artifact:    { type: Artifact, required: true }
  theme:       { type: Text, required: false }
  description: { type: Text, required: false }
produces:
  styled_artifact: { type: Artifact }
  theme_spec:      { type: ThemeSpec, when: creating a theme }
  theme_listing:   { type: List<Text>, when: listing themes }
owns-when:
  - user wants to change the visual styling of an artifact
requires:
  apply-theme: [artifact exists]
  create-theme: [artifact exists, description exists]
  show-themes: []
flows: [apply-theme, create-theme, show-themes]
authority:
  user-decides: [which theme to choose, whether a generated theme matches]
  system-decides: [whether colors satisfy readability, whether fonts exist]
  system-may: [suggest nearest readable colors]
  system-must-not: [infer user approval]
effects:
  reads: [theme-showcase.pdf, themes/*.md, source artifact]
  creates: [styled artifact, themes/{name}.md]
  mutates: []
risk: low                   # low | medium | high
cost: cheap                 # cheap | moderate | expensive
budget: { header: 400, body: 2500 }   # token ceilings
```

### Frontmatter profile

The header is parsed under the SkillWren Frontmatter Profile: a strict,
deterministic, YAML-compatible subset — not unrestricted YAML. Scalars are
bare or single/double-quoted strings (no escapes processed), lowercase
`true`/`false` booleans, and base-10 integers. Values may also be inline
lists (`[a, b]`), inline maps (`{k: v}`, one level, no nested inline
structures), block lists (`- ` items), and block maps (indented `key:`
entries). `#` starts a comment outside quoted strings. Indentation is
spaces only; tab indentation is a validation error (F1). Not supported:
anchors, aliases, tags, multi-line scalars, escape processing, or YAML 1.1
extras (`yes`/`no`, `on`/`off`, `True`, unquoted dates). Anything outside
the profile is a frontmatter error (F1), even when some YAML parser would
accept it.

### Schema decisions

Closed type grammar (recursively validated):

```text
T := Text | Number | Boolean | Path | Artifact | Theme | ThemeSpec | Any
   | List<T> | Enum[v1, v2, ...]
```

`List` takes exactly one inner type, which must itself be valid
(`List<List<Text>>` is fine; `List<>` and `List<Dragon>` are not). `Enum`
needs at least one element; elements must be non-empty, duplicate-free,
and free of structural characters (`[]<>{},`). Enums are written
`Enum[a, b, c]`, for example `{ type: "Enum[low, medium, high]" }`. Inside
an inline map or list, quote any value containing `[`, `]`, `{` or `}`
(an `Enum`, a `{var}` path): YAML parsers reject them unquoted, and hosts
that fail to parse a header silently drop its description (F1). Quoted
type strings are parsed by the type grammar as usual.

Identifiers: `skill` is a kebab-case id
(`[a-z0-9]+(-[a-z0-9]+)*`, F1); flow names use the same grammar in header
`flows`, header `requires` keys, and logic-block headers alike (F1 on the
header side, F2 on the fence side). `skill`, `description`, and `purpose`
must be non-empty strings (F1). `version` is numeric `major.minor[.patch]`
and doubles as the format version: a validator accepts skills at or below
its own format version and rejects newer ones (F1), since it cannot verify
language it does not know. Patch versions carry no format change, so they
are format-equivalent to their `major.minor`: a format-0.4 validator
accepts `version: 0.4.1` and still rejects `version: 0.5`.

`accepts` entries carry `{ type: T }` with optional `required: true|false`
(lowercase only, F1; missing means `false`). From 0.5, `purpose` is
optional and defaults to `description`, and an optional `release` names
the package version (any non-empty string; never compared as a format
version). `mutates` defaults to empty
and must be explicit; `description` is required and `name` SHOULD equal
`skill` (the installer rejects files without `description`; verified
empirically); unknown frontmatter fields warn, never error; `risk`/`cost`
follow Contract2Tool; `requires` duplicates each entry
flow's leading `require` conditions so routing stays header-only (labels and
blank lines don't break the leading run; the validator enforces exact match
after case/whitespace normalization); token ceilings are part of the contract
and validator-enforced (counted per Section 10); budget ceilings must be
positive integers (F1).

## 6. Logic body language

Each flow lives in its own fenced block with info string `logic`; each file
has exactly one fenced block with info string `contract` carrying `resources:`,
`always:`, and `never:` sections in that order. Mislabelled, misplaced, or
duplicated fences fail validation. The vocabulary is closed, in five groups:

- Actions change or retrieve (13): `open, read, write, save, show, ask,
  generate, apply, run, return, abort, discard, exec`.
- Conditions branch (4): `if, unless, when, for each`.
- Gates prohibit advancement (3): `require` (must hold to continue), `verify`
  (check and establish evidence), `allow` (explicit permission grant).
- Invariants hold globally (2): `always`, `never`.
- References bind values (3): `as` (bind), `with` (arguments), `from`
  (sources); `{name}` interpolates a bound value into paths.
- Structure words (6): `label`, `return to`, `retry`, `otherwise`, `else`,
  `return:`.

Indentation is structure: the validator nests statements into an
indentation AST and anything nested where no block is allowed fails (O1).
Branches, `for each`, `otherwise:`, `return:`, and `run` take indented
bodies; `require`/`verify`/`read`/`open` take only an `otherwise:` repair
block; every other statement takes no children. Labels are transparent
markers: they declare jump targets but never take children, and they do
not break the leading-`require` run.

Jump targets are declared with `label <name>:` on its own line; `return to`
names a label in the same flow. `allow <action> when <condition>:` grants an
exception to exactly one `never` invariant within the enclosing flow only,
and must quote the invariant it narrows. `for each <source> as <var>:` iterates a List-typed binding: when the
source's declared `accepts` type is known and not a `List<...>` (and not
`Any`, which admits lists), iterating it fails validation (T1). Bindings
created by `as`/`generate`/`run` have unknown types until dataflow type
inference lands, so they are exempt. The loop variable is read-only, and
the iterated collection must not be rebound (`as`) or written
(`write`/`save`) inside the loop body (L1). Conditions stay natural language
until determinism demands more (`require text/background contrast meets
readability` today, `require contrast(spec) >= WCAG.AA` later).

Recovery is local and owned: an `otherwise:` block must nest directly under
a `require`, `verify`, `read`, or `open` (O1), and `retry` must appear
inside such a repair block (L3), where it re-executes the failed gate.
Repair blocks should end in `retry`, `return to <label>`, `abort`, or
`return`; falling through warns (W9).

Flows returning one value end in `return <binding> as <name>`; flows
returning several end in a `return:` block with one `name` or
`name = binding` line per value. Every returned name must be a skill
`produces` entry, and every `produces` entry must be returned by at least
one flow. Every reachable path through a flow must end in `return` or
`abort`, and every flow must have at least one reachable terminal (R2).
Unreachable statements warn (W10).

`apply` is a pure in-memory transform: it reads bindings and creates a
binding. It performs no resource effects, needs no effects coverage, and
must not name a resource (E4) — read the resource into a binding first,
then apply to the binding. To change a resource, `apply` then
`write`/`save`. `apply` always binds its outcome with `as` (V1 otherwise).

From 0.5, `else:` may follow an `if`, `unless`, or `when` block at the same
indentation; exactly one arm runs, so a name bound in both arms is
definitely bound after them (U1). An `else:` with no branch right before it
is O1. `exec <command> from <resource> as <name>` runs a command in or from
a declared resource and binds its outcome (exit status, output). It must
bind with `as` (V1), its source must be covered by `effects.executes`
(E2), and it counts as a mutation for dismissal safety (M1): a command can
change anything it reaches. `verify <condition> from <name>` names the
binding that holds the gate's evidence, usually an `exec` result, which
must be bound (U1).

Binding is path-sensitive: a name must be bound on every control-flow path
to its use (definite binding, U1). Bindings created inside a branch are
unavailable after the join; a failed `read`/`open` binds nothing on its
repair path; `discard` unbinds. Anything outside the vocabulary is a
validation error, not prose.

## 7. Authority model

Four lists (header) plus structural rules. Any list may be empty.
`user-decides`: choices that must reach a human (`ask` plus `require
confirmation`). `system-decides`: checks the agent settles alone (validity,
readability, availability). `system-may`: bounded discretion (suggest
corrections, repair objective defects). `system-must-not`: hard
prohibitions (never infer approval, never silently choose).

Decision structure is enforced mechanically (A2), with no fuzzy matching:

- A `require user ...` gate must be dominated by a decision `ask` (an `ask`
  without `as`) on every path to it. A skill that says the user decides
  must actually ask them.
- A decision `ask` must dominate a confirmation (`require user ...` or
  `require confirmation`). An ask with no confirmation never lands.
- A bare `require confirmation` must be dominated by an `ask` of either
  kind (decision asks and input asks both count).

Decision-`ask` lines (those without `as`) should map to a `user-decides`
entry, and every `user-decides` entry should be exercised by at least one
flow. Mapping is a word-overlap heuristic (shares at least two content
words, Section 9 stopword list, counting `ask` and `require user ...`
lines); misses are warnings (W3), never errors, and never constitute proof
that authority is correct. Input-`ask` lines (with `as`) fill `accepts`
entries or locals and need no authority mapping. A `system-may` entry is
exercised when it shares at least two content words (Section 9 stopword
list) with any flow line; misses warn (W2). On chains, callee authority
propagates unchanged: a sub-flow cannot downgrade a user decision to a
system one.

## 8. Effects and resources

Resources are declared once per file, inside the `contract` block, under a
closed schema: each resource has `path:` and `access:` (both required) and
optional `immutable: true|false` (lowercase), plus optional `glob:` (0.5): a
machine-readable repo-relative pattern for the files the resource covers,
used by runtime conformance (Section 14). Unknown resource properties,
non-canonical access, and non-boolean `immutable` are errors (F2). Access
is one of `read`, `create`, `read+create`, or `read+write` (0.5; same
checks as `read+create`, but says the resource is updated in place, which
is what `effects.mutates` means) (canonical scalar form; no
list syntax). Flows reference resources by name. Header `effects`
summarize the union across flows as `reads`/`creates`/`mutates`, plus
`executes` (0.5, optional list): resources an `exec` runs commands in or
from. Every `exec` source must be covered by `executes` (E2).

Mechanical effects rule: every `open`/`read`/`write`/`save` names a target
(the `from`-source for `read X from Y`); the target must match a declared
resource name, a declared resource path (`*` and `{var}` segments match
anything), or an `accepts` entry. Every resource referenced by `open`/`read`
must be covered by an `effects.reads` entry (name or path match); every
resource referenced by `write`/`save` must be covered by `effects.creates`
or `effects.mutates`. Anything marked `immutable` must never be a
`write`/`save` target. A resource read and written at the same literal
path must be declared under `mutates`, not only `creates`
(interpolated and wildcard paths are exempt: the validator cannot prove
identity through them). `apply` is pure and outside the effects model.
This gives pre-execution answers to what the skill can touch, overwrite,
create, or require from a human.

Mechanically enforced invariants: immutable writes (E3), effect
targeting and coverage (E1/E2), apply purity (E4), authority structure
(A2), dismissal safety (M1). Semantic runtime invariants: the
natural-language `always`/`never` lines, which the runner enforces and
the validator cannot prove. `allow` matching is lexical overlap and
warning-grade in spirit: it errors only when an `allow` matches no
`never` at all (A1). Invariant identifiers that would make `allow`
exact are deferred to a later release (Section 17). The effects model
assumes a single actor (a runtime guard can cover the multi-actor case:
full-stack's `run_guard.py` checks a run's git changes against a declared
write set and refuses overlapping claims across workers; see the authoring
guide): concurrent modification by other agents or
sessions is out of scope for static checking, so skills that mutate
shared repositories carry the gap as an `always` invariant (authoring
guide step 10).

## 9. Discovery and routing (headers-only protocol)

The agent parses frontmatter from every skill file and never opens bodies
during selection. Matching order: `owns-when` overlap score, then `accepts`
satisfiability (caller can supply required inputs), then header `requires`
satisfiability against known state. Overlap scoring is deterministic
content-word match: lowercase request and trigger, drop stopwords (fixed list:
a, an, the, to, of, and, or, for, with, on, in, please), score each trigger by
the count of its remaining words present in the request; the skill's score is
its best trigger's count. Ties break toward lower `risk`, then lower `cost`,
then alphabetical id. Overlapping `owns-when` triggers across skills emit a
validator warning naming the pair. Embedding or LLM-judged matching is
explicitly deferred. Decision: routing reads structured fields first
and uses trigger prose only as a ranked signal, so selection stays cheap and
explainable. This protocol describes a SkillWren-aware router. Hosts that
do not implement it route on `description` alone, so write `description`
as the routing text: what the skill is for and what it is not for.

## 10. Loading and progressive disclosure

Load order per activation: header (always), requested flow block (on demand),
referenced resource (on demand), prose appendix (only when a `generate` or
creative step needs it). Bodies of unselected skills stay out of context
entirely. Token counting uses tiktoken `cl100k_base`; where tiktoken is
unavailable the validator may use ceil(characters/4) and must label the result
approximate. Budgets: the header ceiling is at most 400 tokens (declaring more
is B1, because routing reads headers); the body ceiling is declared per skill,
defaults to 2500, and a declaration above 2500 warns (W11). Exceeding the
declared ceiling fails validation with the overage count. Past roughly 20 skills,
headers move to a sharded index (one index file per group) so discovery scans
the index instead of every file; the index format is headers concatenated, no
new syntax.

Body layout is `contract`, then `logic` blocks, then appendix prose.
Semantic fences are exactly three backticks plus `logic` or `contract`
(trailing whitespace allowed); any other backtick-led fence line is an
error (F2). The contract block precedes all logic blocks (F2). Lines
before the first fence are an ignored preamble (titles). Non-blank prose
between semantic blocks, and any semantic block after appendix content
began, are errors (F2). A skill with a `generate` step needs a real
appendix: an ATX heading (`#`–`######`) whose text contains "appendix",
case-insensitive — merely mentioning the word in prose warns (W4).

## 11. Chaining and composition

`run <flow> with:` invokes a flow in the same skill; `run <skill>.<flow>
with:` crosses skills. Cross-skill arguments bind by name to the callee's `accepts` at load time; the single-file validator cannot see the callee file, so cross-file arity and type mismatches are not validation errors — every cross-skill `run` warns as an unverified effect boundary (W8) instead, and cross-file checking awaits the workspace validator. Same-skill arguments bind by name into callee scope: names matching an `accepts` entry must satisfy its type, other names create locals. Arguments are optional overrides — the callee still sees skill `accepts` ambiently, so omitting an argument is never an error; passed values must be bound (U1). (Flow-local parameter declarations are deferred to a later release.) A same-skill `run` binds exactly the callee flow's
returned names into same-named caller bindings (overwriting on collision):
running one flow never binds another flow's outputs. The callee's `produces`
must satisfy the caller's expectation or the call is rejected before
execution. Effects union across the chain for audit; `never` invariants
from every skill in the chain apply jointly. Recursion deeper than one
self-`return to` label cycle is a validation error; mutual skill recursion
is rejected outright.

A cross-skill `run` is an unverified effect boundary (W8): the single-file
validator cannot see the callee's effects, authority, or dismissal safety,
so it warns once per call site instead of checking. Resolving external
runs is the top priority for the future workspace validator.

## 12. Failure semantics

Recovery is local: any `require`, `verify`, `read`, or `open` may carry an
`otherwise:` block directly beneath it (O1), with repair steps ending in
`retry`, `return to <label>`, `abort`, or `return` (W9 when they fall
through). `retry` appears only inside such a repair block (L3) and
re-executes the failed gate after the repair steps. Defaults when no
`otherwise` is given: failed `require` aborts with the condition quoted;
failed `verify` discards derived artifacts (also available explicitly as
`discard <binding>`), reports the failure, leaves sources unchanged, and
aborts.

A decision `ask` has three outcomes. **Confirmed**: the user agrees and the
confirmation `require` holds. **Declined**: the user answers no; the
confirmation fails and its `otherwise:` repair runs, which may mark
dependent work and continue rather than abort. **Dismissed**: the user
cancels or never answers, or the host cannot reach a user at all (a
non-interactive run such as `claude -p`); the flow stops with zero
mutation and no repair runs.

Global rules: user dismissal of any `ask` stops the flow with zero
mutation; `never` violations abort the entire chain immediately; `abort`
always reports what was and was not changed. Per-flow failure catalogs
(missing input, missing resource, gate failure, verification failure, user
dismiss) live directly under their flows, never in a detached appendix.

Dismissal safety is proved in a weak mechanical form (M1): no resource
write, and no call to a mutating same-skill flow, may precede a
dismissible `ask` on any control-flow path. Cross-skill calls are excluded
from this proof (W8 boundary): their effects are unverified, so a foreign
call before an ask keeps its warning but cannot clear or fail the check.

## 13. Static validation catalog

The validator runs without execution and reports errors (block use) and
warnings (allow with notice).

Errors:

- F1 frontmatter/schema: missing keys; empty skill/description/purpose;
  non-kebab skill id; malformed or newer-than-validator `version`;
  non-list authority/effects groups; accepts/produces entries without a
  valid closed-grammar type; non-boolean `required`; non-kebab flow names
  in `flows`/`requires`; malformed `requires`/`flows`/`owns-when`;
  bad `risk`/`cost`; non-integer or non-positive budget ceilings;
  tab indentation; unquoted `[ ] { }` inside an inline collection.
- F2 fences/contract/body-order: mislabeled, misplaced, or duplicated
  fences; fences not exactly three backticks; logic before the contract;
  content between semantic blocks; semantic blocks after appendix began;
  malformed contract sections; resources missing `path`/`access`;
  unknown resource properties; non-canonical access; non-boolean
  `immutable`; tab indentation.
- F3 flow/fence set: flow without header entry or vice versa.
- V1 vocabulary: unknown verb, control word, or reference; `allow`/`run`/
  `return` malformed; stray assignments or bare names outside run args
  and `return:` blocks; `apply` without `as`.
- R1 requires: header `requires` missing or mismatching a flow's leading
  `require` conditions, or naming an unknown flow.
- R2 returns: `return` naming an undeclared `produces` entry; `produces`
  entry never returned by any flow; reachable path falling off the end
  without `return`/`abort`; flow with no reachable terminal.
- R3 run: `run` target naming no flow in the file.
- R4 required inputs: a `required: true` accepts entry used by a flow
  without a leading `require <name> exists`.
- T1 for-each type: iterating a binding whose declared type is known and
  not a `List` type.
- T2 run-argument type: a same-skill `run` argument passing a binding
  whose known declared type mismatches the callee `accepts` entry type
  (bindings with unknown types, from `as`/`generate`/`run`, stay exempt).
- U1 unbound: reference to a name not bound on every path to its use
  (definite binding; failed reads bind nothing on repair paths).
- E1 effect target: `open`/`read`/`write`/`save` target matching no
  resource, path, or `accepts` entry.
- E2 effect coverage: referenced resource uncovered by `effects`;
  same-literal-path read+write declared only under `creates`.
- E3 immutable write.
- E4 impure apply: `apply` naming a resource target.
- A1 allow/never: `allow` matching no `never` invariant.
- A2 ask/confirm structure: `require user ...` without a dominating
  decision `ask`; decision `ask` without a following confirmation;
  `require confirmation` without a preceding `ask`.
- L1 label/loop: duplicate label; `return to` an unknown label;
  rebinding a `for each` variable; rebinding or writing the iterated
  collection inside the loop.
- L2 recursion: `run` cycles between flows.
- L3 retry: `retry` outside an `otherwise:` repair block.
- O1 block structure: `otherwise:` not directly under a fallible gate;
  statements nested where no block is allowed.
- B1 budget: header/body token overruns; a declared header ceiling above 400.
- M1 dismissal: a resource write (or call to a mutating same-skill flow)
  on a path to a dismissible `ask`.

Warnings:

- W1 overlapping `owns-when` triggers across files.
- W2 `system-may` entry never exercised.
- W3 `ask`/`user-decides` mapping miss (heuristic, warning-grade only).
- W4 creative step without a `## Appendix` heading.
- W5 binding created by `as` never referenced on a reachable path.
- W6 `effects` entry matching no resource.
- W7 unknown frontmatter field (or `name` unequal to `skill`).
- W8 cross-skill `run`: unverified effect boundary.
- W9 `otherwise:` block falling through without a terminal step.
- W10 unreachable statement.
- W11 declared body ceiling above the 2500-token default.
- W12 `apply` spec with no appendix anchor: no appendix list item or
  paragraph contains all of the spec's content words.

Output is a file/line list with one-line fixes.

## 14. Testing and evaluation

Four suites. Conformance: valid and invalid fixture skills with golden
validator outputs. Budget: token counts (per Section 10) for headers and bodies
against ceilings, plus a headers-only discovery test proving bodies never load
during selection. Precision: scenario scripts asserting each required gate
fires, each `never` holds under adversarial branches, and dismissals mutate
nothing (gate-recall 100 percent, zero undeclared mutations). Compression:
theme-factory plus two further prose skills rewritten in this format must use
at most half the tokens while preserving behavior, with a reviewer checklist
per conversion.

Adversarial fixtures accompany every validator rule: each rule has at least
one invalid fixture proving it fires and, where the rule is new, evidence it
stays silent on the behavior it replaces. Mutation testing (systematically
deleting, replacing, or moving one structural element of a known-valid skill)
is the preferred way to find the next hole.

Runtime conformance (0.5): `skillwren conform <skill.md> --prompt ...`
runs the skill in one headless Claude Code session inside a throwaway git
workspace with an empty user profile, then reports every changed file that
no `glob:` of a created or mutated resource covers (an undeclared
mutation), and any run that asked a question yet changed files (an `ask`
cannot reach a user headless, so it is a dismissal). It spends model usage,
so it is opt-in and never part of `check` or CI. It samples behavior; a
conforming run is evidence for that prompt, not proof for all inputs.

## 15. Authoring kit and migration

Ship a one-file template (`docs/skill-template.md`), the validator as a
CLI (`skillwren check <file>...`, exit 0 clean, 1 on errors;
`check --all` checks every `*.md` under the current directory except
`benchmarks/archive/` with a one-line summary per file, exit 1 when any
file fails; `check --explain <file>...` adds a plain-language paragraph
per error naming the SPEC section; `conform` as described in Section 14),
and the `authoring-guide.md` companion
guide, which carries the full procedure, template, and checklists. New
skills start from the template; prose-first drafting is allowed only as a
scratch step before conversion.

## 16. Compatibility

The format is valid Markdown with YAML frontmatter, so agents without tooling
degrade gracefully to reading it as structured prose. A conforming file can
serve directly as a `SKILL.md`. No new extension, no sidecar files, no required
runtime; validator and router conventions are additive.

What current hosts read (observed with Claude Code and Codex, 2026-10):

| Field or block | Host behavior |
|---|---|
| `name`, `description` | Read for discovery and selection; `description` is the only routing text |
| Other header fields (`accepts`, `authority`, `effects`, `budget`, ...) | Parsed as YAML and ignored; declarations, not host-enforced controls |
| `contract` and `logic` blocks, appendix | Loaded as instructions when the skill runs; nothing executes them |

A header that fails to parse as YAML can make a host drop it entirely
(observed: Claude Code fell back to the H1 as description), which is why
F1 rejects YAML-invalid members. `version` is the format version; state a
package release elsewhere until `release` lands. Runtime guarantees need
runtime tooling: the host's permission mode, hooks, or a skill's own guard
script (Section 8).

## 17. Future work

EBNF grammar plus parser; constrained-decoding profile; measured compression
layer; cross-skill imports; named failure handlers only after three skills
demonstrably need them; invariant identifiers so `allow` can reference the
exact `never` it narrows instead of word overlap; repair-provenance and
dataflow-correctness analysis (accepted corrections must reach the values
they repair); dataflow type inference (binding types from `run` outputs
and transforms, so `for each` checks more than declared inputs);
loop-scoped `for each` bindings; a workspace validator that
resolves cross-skill `run` effects, authority, and dismissal safety;
optional resources (`required: false` on resources, with reads and writes
dominated by a presence guard).
Planned from full-stack evidence (BF-1 to BF-6 in
`docs/design/full-stack-backfill.md`): YAML-safe header values,
budget-cap alignment, decline versus dismissal, host-compatibility
notes, an `apply` anchor warning, and format 0.5 (`else:`,
`access: read+write`, optional `purpose`, `release`), an `exec` action
with `executes` effects (BF-7), and runtime conformance runs (BF-8).

## 18. Glossary

Contract header: selection and safety metadata. Logic body: flows over the
closed verb set. Gate: `require`/`verify`/`allow` statement blocking progress.
Invariant: `always`/`never` statement true on every path. Authority: who
decides, human or system. Effects: reads/creates/mutates the skill may perform.
Flow: named, runnable unit ending in `return` or `abort`. Binding: named value
created by `as` (rebinding allowed, latest wins). Label: `label <name>:` jump
target inside a flow. Repair block: an `otherwise:` block with its owning
gate. Dismissal safety: no mutation on any path to a user decision.
Kebab-case: `[a-z0-9]+(-[a-z0-9]+)*` identifiers. Frontmatter Profile: the
strict YAML-compatible header grammar (Section 5). Definite binding: bound
on every path to the use.

## 19. Amendment log

### Unreleased

### v0.5 (format change): full-stack backfill BF-6, BF-7, BF-8

Additive; every 0.4.x file that validated clean still does, apart from the
BF-1 YAML fix. Evidence: first real skill maintained in the format
(full-stack 0.3.0) plus fixtures and mutants per rule.

- `else:` arm for `if`/`unless`/`when` (§6). Full-stack had to read the
  same reference twice because definite binding could not see that two
  arms were complementary. Fixtures `valid-else`, `invalid-else-one-arm`
  (U1), `invalid-else-orphan` (O1); mutants `else-arm-unbinds`,
  `else-after-non-branch`.
- `access: read+write` (§8) for resources updated in place.
- `purpose` optional, defaulting to `description`; optional `release`
  (§5). Full-stack's header hit the 400-token ceiling and dropped safety
  wording twice; `description` and `purpose` were near-duplicates.
  Fixture `valid-v05-header`.
- `exec <command> from <resource> as <name>`, `effects.executes`, and
  `verify ... from <name>` (§6, §8). Full-stack 0.3.0 had to describe
  running its guard script and acceptance checks as writes to a log.
  Fixtures `valid-exec`, `invalid-exec-undeclared` (E2),
  `invalid-exec-no-as` (V1), `invalid-verify-from-unbound` (U1),
  `invalid-exec-before-ask` (M1); mutants `drop-executes-entry`,
  `verify-cites-unbound-evidence`.
- Optional resource `glob:` and `skillwren conform` (§8, §14, BF-8): the
  release criteria "zero undeclared mutations" and "dismissals never
  mutate" are runtime properties no tool measured. Offline tests cover
  glob extraction and classification. Live runs on 2026-10-05 (fixture
  `tests/fixtures/conform/notes-skill`): a normal run conformed; a prompt
  asking for an extra backup file conformed because the model obeyed the
  skill's `never`; a copy with a deliberately wrong glob was reported as an
  undeclared mutation (exit 1).
- The validator's format version is 0.5; `version: 0.6` fails F1.

Full-stack backfill BF-5 (new warning, no format change):

- Common mistake 21 is now checkable: W12 warns when no appendix list
  item or paragraph contains all of an `apply` spec's content words.
  Both golden examples had unanchored specs; each gains a short
  step-meanings list, and their decline paths now say "Declined" (BF-3).
  Full-stack 0.3.0, whose glossary defines every step, raises no W12.
  Evidence: `warn-apply-anchor` warns W12, `valid-apply-anchor` is clean.

Full-stack backfill BF-4 (docs only, no format change):

- Goal 1 and §9 now say headers-only routing is a SkillWren convention;
  current hosts route on `description` alone. §16 gains a table of what
  hosts read versus ignore. §8 notes that a runtime guard covers the
  multi-actor case. The authoring guide adds four live-use patterns:
  a step-meanings glossary, subject-precedence `always`, parallel write
  sets, and fallback-chain resource paths. Evidence: fresh-user review
  findings 3 and 11, field report 2 items G1, G2 and G4, full-stack D-016.

Full-stack backfill BF-3 (semantics clarified, no validator change):

- §12 defines confirmed, declined, and dismissed. A decline runs the
  confirmation's repair; a dismissal (including an `ask` in a
  non-interactive host) stops with zero mutation and runs no repair. The
  template's repair message said "Dismissed" on what is the decline path;
  it now says "Declined". New authoring-guide mistake 22. Evidence:
  full-stack pilot D1 and the fresh-user review's finding 1.

Full-stack backfill BF-2 (validator alignment, no format change):

- §10 said "header at most 400, body at most 2500", but the validator
  accepted any declared ceiling (a `{ header: 900, body: 9000 }` probe
  validated clean). The header ceiling now has a hard maximum of 400
  (B1). The body ceiling stays declared per skill, and a declaration
  above 2500 warns (new W11): full-stack's plain-language step glossary
  needs about 3000. Evidence: `invalid-budget-header-max` fails B1,
  `warn-budget-body` warns W11 only.

Full-stack backfill BF-1 (validator fix, no format change):

- The Frontmatter Profile promised YAML compatibility but accepted
  unquoted `Enum[...]` and `{var}` members inside inline collections,
  which YAML parsers reject. Claude Code then dropped the header and
  showed the skill's H1 as its description (observed 2026-10-05 with
  full-stack). Such members are now F1 errors; quoting fixes them. The
  §5 example and `examples/theme-factory.golden.md` (`"themes/{name}.md"`)
  were themselves affected and are quoted. Evidence:
  `invalid-yaml-unquoted` fails F1, `valid-yaml-quoted` is clean, and a
  test parses every clean fixture's header with PyYAML.

Final hardening pass, no format change:

- Patch versions are format-equivalent: the validator compares
  `major.minor` only, so a format-0.4 validator accepts
  `version: 0.4.1` and still rejects `version: 0.5` (F1; Section 5).
  A skill honestly declaring the project version no longer fails.
  Evidence: `valid-version-patch` validates clean,
  `invalid-version-minor` fails F1.
- Same-skill `run` arguments are type-checked (new error T2, Section 13):
  a named argument matching a callee `accepts` entry must carry a
  binding of that type when the binding's type is known. Bindings with
  unknown types (from `as`/`generate`/`run`, or rebound after their
  declaration) stay exempt pending dataflow type inference. This
  enforces the Section 11 sentence the v0.3 amendment stated but no
  validator checked. Evidence: `invalid-run-arg-type` fires T2 once;
  `valid-run-args` (unknown-typed plus correct-typed arguments) stays
  clean; both golden examples still validate clean.
- CLI ships the deferred Section 15 surface: `check --all` checks every
  `*.md` under the current directory except `benchmarks/archive/`,
  prints a one-line summary per file, and exits 1 when any file fails;
  `check --explain <file>...` adds a plain-language paragraph per
  error naming the violated SPEC section.
- One-file template ships at `docs/skill-template.md` (Section 15
  promise): header with every required field, one contract block, one
  logic flow exercising ask/confirm, one `otherwise` repair, `# TODO`
  markers at each fill site. It passes `skillwren check` clean and is
  referenced from the authoring guide.

Side-by-side pilot feedback (docs only, no format change, no validator
behavior change):

- Authoring guide states budget ceilings are tokens, not bytes
  (a 3700-byte body is roughly 930 tokens); the template carries the
  same note. A passing check prints no usage — only overruns print
  the count.
- Authoring guide documents piloting conversions side-by-side under
  a distinct `-logic` skill id with the prose original kept installed.
- Two live-fire authoring lessons join Common mistakes: don't
  over-constrain `generate` sources to one input, and qualify
  escalation conditions with the failure pattern, not a bare count.
  Evidence: systematic-debugging pilot report (hypothesis-from-diff
  misfire and blunt 3-strikes false-fire on a verified stack-peel).

MochiOS live-fire feedback (docs only, no format change, no validator
behavior change):

- Goal 2 no longer claims transform specifications are formal:
  sequencing, gates, authority, and effects are mechanically checked;
  `apply`/`generate` prose is structured but advisory.
- Authoring guide documents derive-before-ask for optional inputs, the
  guard pattern for possibly-absent resources, an `always` recipe for
  multi-agent repos, and an `apply`-to-appendix anchoring rule (new
  Common mistakes 20-21, new pre-submit checklist item).
- The effects model states its single-actor boundary (Section 8), and
  optional resources join future work (Section 17). Evidence:
  full-stack field report 2026-10-03 (needless criteria ask, undefined
  registry, cross-flow registry inconsistency, advisory `apply`
  confusion, concurrent-edit gap).

### v0.4.1 (2026-10-01)

Follow-up seams from red-team review: `for each` over a binding with a
known non-`List` declared type is a type error (T1); rebinding or
writing the iterated collection inside the loop body is an error (L1,
which previously covered only the loop variable); Section 11 no longer
claims cross-file validation the single-file validator cannot perform
(W8 boundary is now stated up front). No format change.

### v0.4 (2026-10-01): make the bird mean what it says

Hardening release: no new expressive features. The validator parses flows
into an indentation AST and a control-flow graph and enforces:
`otherwise`/retry ownership (O1/L3), ask/confirm structure (A2),
required-input leading gates (R4), complete frontmatter/contract schemas
(F1/F2: closed types, kebab ids, boolean flags, canonical access,
positive budgets, supported versions, no tabs), strict fences and body
ordering (F2), per-flow run outputs (U1 scoping), apply purity (E4),
definite per-path binding (U1), dismissal safety (M1), and
create-vs-mutate precision for literal paths (E2). New warnings:
otherwise fall-through (W9), unreachable code (W10). `allow` and W3
authority mapping are documented as heuristic-grade; invariant ids are
future work. Golden theme-factory repaired (corrections incorporated,
decisions asked, retry showcased, canonical access).

### v0.3 (2026-10-01)

Applied in v0.3 after round 2 (content-only attribution held). Items 1-6 folded
into the normative sections above; items 7-8 are new in this pass. Evidence:
trial conversion of code-reviewer plus benchmark rounds 1-2 (`benchmarks/`).

1. Same-skill `run` arguments: bind by name into callee scope; names matching
   an `accepts` entry must satisfy its type, other names create locals.
   (Round-1 test skill duplicates its report tail because this is undefined.)
2. `system-may` exercised rule: mechanical, mirroring the `user-decides`
   mapping (shares two content words with a flow line); misses warn.
3. Mechanical effects coverage: every `open`/`read`/`write`/`save` target
   (`from`-source for reads) must match a resource name, resource path (`*`
   and `{var}` segments wild), or `accepts` entry; referenced resources must
   be covered by `effects`; unmatched `effects` entries warn.
4. Installer frontmatter: `description` required (installer rejects without
   it; verified empirically), `name` optional (validated without it),
   installer copies files byte-pristine (verified by diff); unknown
   frontmatter fields warn, never error.
5. New warning: binding created by `as` never referenced afterward.
6. `retry` semantics: re-executes the failed gate after the repair steps.
7. Header budget 200 to 400 tokens (measured: golden 356, code-reviewer 234;
   200 fit no real header; bodies stay under 2500).
8. Flow/fence set mismatch is an error; the unimplementable `unused flow`
   warning is removed.
