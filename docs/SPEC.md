# SkillWren — Skill Logic Architecture (Contract-Header + Logic-Body)

- Date: 2026-10-01
- Status: v0.3 final (2026-10-01)
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
2. Raise precision: control flow, gates, authority, and effects are formal;
   prose describes only meaning (creative/semantic steps).
3. Stay frictionless: plain `.md` files that work with today's agents and gain
   checking/enforcement as tooling adopts the spec.
4. Be verifiable: a static validator answers "what can this touch, what does it
   require, who decides" without executing anything.

Success criteria (v0.1): headers fit the token ceiling; converted skills use at
most half the tokens of their prose equivalents; zero undeclared mutations in
eval scenarios; every required gate fires; user dismissals never mutate.

## 2. Non-goals (YAGNI cuts)

- No constrained decoder or execution runtime (direction 2). The spec is
  enforceable later; v0.1 is spec plus static validation.
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
frontmatter) declares selection and safety metadata. The logic body (fenced
`logic` blocks plus one `contract` block) defines named flows over a 16-verb
vocabulary with gates, invariants, and local recovery. Optional prose
appendices cover steps that are genuinely creative and must not be
proceduralized.

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
version: 0.3
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

Decisions: closed v0.1 type set (`Text, Number, Boolean, Path, Artifact, Theme,
ThemeSpec, List<T>, Enum, Any`); enums are written `Enum[a, b, c]`, for example
`{ type: Enum[low, medium, high] }`; `mutates` defaults to empty and must be
explicit; `description` is required and `name` SHOULD equal `skill` (the installer rejects files without `description`; verified empirically); unknown frontmatter fields warn, never error; `risk`/`cost` follow Contract2Tool; `requires` duplicates each entry
flow's leading `require` conditions so routing stays header-only (labels and
blank lines don't break the leading run; the validator enforces exact match
after case/whitespace normalization); token ceilings are part of the contract
and validator-enforced (counted per Section 10).

## 6. Logic body language

Each flow lives in its own fenced block with info string `logic`; each file
has exactly one fenced block with info string `contract` carrying `resources:`,
`always:`, and `never:` sections in that order. Mislabelled, misplaced, or
duplicated fences fail validation. Vocabulary v0.1, four statement kinds:

- Actions change or retrieve: `open, read, write, save, show, ask, generate,
  apply, run, return, abort, discard`.
- Conditions branch: `if, unless, when, for-each`.
- Gates prohibit advancement: `require` (must hold to continue), `verify`
  (check and establish evidence), `allow` (explicit permission grant).
- Invariants hold globally: `always`, `never`.

References bind values: `as` (bind), `with` (arguments), `from`/`using`
(sources); `{name}` interpolates a bound value into paths. Jump targets are
declared with `label <name>:` on its own line; `return to` names a label in
the same flow. `allow <action> when <condition>:` grants an exception to
exactly one `never` invariant within the enclosing flow only, and must quote
the invariant it narrows. `for each <item> as <var>:` iterates a List-typed
binding; the loop variable is read-only and mutating the iterated collection
inside the loop fails validation. Conditions stay natural language until
determinism demands more (`require text/background contrast meets readability`
today, `require contrast(spec) >= WCAG.AA` later). Flows returning one value
end in `return <binding> as <name>`; flows returning several end in a `return:`
block with one `name` or `name = binding` line per value. Every returned name
must be a skill `produces` entry, and every `produces` entry must be returned
by at least one flow. Every mutating verb must be covered by the header
`effects`. Anything outside this vocabulary is a validation error, not prose.

## 7. Authority model

Four lists (header) plus one rule. Any list may be empty. `user-decides`: choices that must reach a
human (`ask` plus `require confirmation`). `system-decides`: checks the agent
settles alone (validity, readability, availability). `system-may`: bounded
discretion (suggest corrections, repair objective defects). `system-must-not`:
hard prohibitions (never infer approval, never silently choose). Rule:
decision-`ask` lines (those without `as`, followed by a confirmation `require`)
must map to a `user-decides` entry, and every `user-decides` entry must be
exercised by at least one flow. Mapping is mechanical in v0.1: a line maps when
it shares at least two content words (Section 9 stopword list) with the entry,
counting `ask` and `require user ...` lines; misses are warnings, not errors.
Input-`ask` lines (with `as`) fill `accepts` entries or locals and need no
authority mapping. A `system-may` entry is exercised when it shares at least
two content words (Section 9 stopword list) with any flow line; misses warn. On chains, callee authority propagates unchanged: a
sub-flow cannot downgrade a user decision to a system one.

## 8. Effects and resources

Resources are declared once per file, inside the `contract` block (`path`,
`access: read | create | read+create`, `immutable: true | false`); flows
reference them by name. Header `effects` summarize the union across flows as
`reads`/`creates`/`mutates`. Mechanical effects rule: every `open`/`read`/`write`/`save` names a target (the `from`-source for `read X from Y`); the target must match a declared resource name, a declared resource path (`*` and `{var}` segments match anything), or an `accepts` entry. Every resource referenced by `open`/`read` must be covered by an `effects.reads` entry (name or path match); every resource referenced by `write`/`save` must be covered by `effects.creates` or `effects.mutates`. Anything marked `immutable` must never be a `write`/`save` target. This gives pre-execution
answers to what the skill can touch, overwrite, create, or require from a
human.

## 9. Discovery and routing (headers-only protocol)

The agent parses frontmatter from every skill file and never opens bodies
during selection. Matching order: `owns-when` overlap score, then `accepts`
satisfiability (caller can supply required inputs), then header `requires`
satisfiability against known state. Overlap scoring v0.1 is deterministic
content-word match: lowercase request and trigger, drop stopwords (fixed list:
a, an, the, to, of, and, or, for, with, on, in, please), score each trigger by
the count of its remaining words present in the request; the skill's score is
its best trigger's count. Ties break toward lower `risk`, then lower `cost`,
then alphabetical id. Overlapping `owns-when` triggers across skills emit a
validator warning naming the pair. Embedding or LLM-judged matching is
explicitly deferred to v0.2. Decision: routing reads structured fields first
and uses trigger prose only as a ranked signal, so selection stays cheap and
explainable.

## 10. Loading and progressive disclosure

Load order per activation: header (always), requested flow block (on demand),
referenced resource (on demand), prose appendix (only when a `generate` or
creative step needs it). Bodies of unselected skills stay out of context
entirely. Token counting uses tiktoken `cl100k_base`; where tiktoken is
unavailable the validator may use ceil(characters/4) and must label the result
approximate. Budgets: header at most 400 tokens, body at most 2500 tokens v0.3;
violations fail validation with the overage count. Past roughly 20 skills,
headers move to a sharded index (one index file per group) so discovery scans
the index instead of every file; the index format is headers concatenated, no
new syntax.

## 11. Chaining and composition

`run <flow> with:` invokes a flow in the same skill; `run <skill>.<flow>
with:` crosses skills. Cross-skill arguments bind by name to the callee's `accepts`; arity and type mismatches fail validation where both files are present, and fail at load time otherwise. Same-skill arguments bind by name into callee scope: names matching an `accepts` entry must satisfy its type, other names create locals. (Flow-local parameter declarations are deferred to v0.4.) The callee's `produces` must satisfy the caller's
expectation or the call is rejected before execution. The callee's `produces`
bind into same-named caller bindings (overwriting on collision). Effects union
across the chain for audit; `never` invariants from every skill in the chain
apply jointly. Recursion deeper than one self-`return to` label cycle is a
validation error; mutual skill recursion is rejected outright in v0.1.

## 12. Failure semantics

Recovery is local: any `require`, `verify`, `read`, or `open` may carry an
`otherwise:` block with repair steps ending in `retry`, `return to <label>`, or
`abort [with "<message>"]`. `retry` re-executes the failed gate after the repair steps. Defaults when no `otherwise` is given: failed
`require` aborts with the condition quoted; failed `verify` discards derived
artifacts (also available explicitly as `discard <binding>`), reports the
failure, leaves sources unchanged, and aborts. Global rules: user dismissal of
any `ask` stops the flow with zero mutation; `never` violations abort the
entire chain immediately; `abort` always reports what was and was not changed.
Per-flow failure catalogs (missing input, missing resource, gate failure,
verification failure, user dismiss) live directly under their flows, never in a
detached appendix.

## 13. Static validation catalog

The validator runs without execution and reports errors (block use) and
warnings (allow with notice). Errors: frontmatter schema violation; unknown
verb, control word, or reference; unbound variable; header `requires` missing
or mismatching a flow's leading `require` conditions; `allow` without a
matching `never`; mutation of a `for each` collection or loop variable;
`logic`/`contract` fence mislabeled, misplaced, or duplicated; `return`
naming an undeclared `produces` entry; `produces` entry never returned by any
flow; `accepts`/`produces` type inconsistency; `run` target or argument
mismatch; mutating verb outside declared `effects`; write to an `immutable`
resource; label/recursion violation; token budget overrun; effect target matching no resource, path, or `accepts` entry; referenced resource uncovered by `effects`; flow/fence set mismatch (flow without header entry or vice versa). Warnings:
overlapping `owns-when` triggers; `system-may` entry never exercised; `ask`/`user-decides` mapping miss; `effects` entry matching no resource; binding created by `as` never referenced; unknown frontmatter field; creative step without appendix guidance. Output is a file/line list with one-line fixes.

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

## 15. Authoring kit and migration

Ship a one-file template, the validator as a CLI (`skillwren check
<file>...`, exit 0 clean, 1 on errors; `check --all` and `--explain` are
deferred to a later release), and the `authoring-guide.md` companion guide,
which carries the full procedure, template, and checklists. New skills
start from the template; prose-first drafting is allowed only as a scratch
step before conversion.

## 16. Compatibility

The format is valid Markdown with YAML frontmatter, so agents without tooling
degrade gracefully to reading it as structured prose. A conforming file can
serve directly as a `SKILL.md`. No new extension, no sidecar files, no required
runtime in v0.1; validator and router conventions are additive.

## 17. Future work (post-v0.1)

EBNF grammar plus parser; constrained-decoding profile toward direction 2;
measured compression layer toward direction 3; cross-skill imports; named
failure handlers only after three skills demonstrably need them.

## 18. Glossary

Contract header: selection and safety metadata. Logic body: flows over the
closed verb set. Gate: `require`/`verify`/`allow` statement blocking progress.
Invariant: `always`/`never` statement true on every path. Authority: who
decides, human or system. Effects: reads/creates/mutates the skill may perform.
Flow: named, runnable unit ending in `return` or `abort`. Binding: named value
created by `as` (rebinding allowed, latest wins). Label: `label <name>:` jump
target inside a flow.

## 19. Amendment log (v0.3 applied 2026-10-01)

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
