# SkillWren language reference (authoring card)

Everything needed to draft a skill that passes `check`. The full grammar
is `SPEC.md` beside this file; section numbers below point into it.

## Layout

- **Default: one `SKILL.md`** with `name` and `description` frontmatter,
  one `contract` block, one `logic` block per procedure, a command table
  for every `exec`, and a **Step meanings** list for every `apply`. Real
  agents follow this form; do not also write a prose copy of the logic
  (nothing checks that the two agree).
- **Flow files** (`flows/*.md`, each with its own `contract` and `logic`)
  only when parts load at different times. `SKILL.md` then says which flow
  to read when. Check every file together so cross-file rules apply.
- A **complete skill** (rich YAML header: `skill`, `accepts`, `produces`,
  `authority`, `effects`, budgets; SPEC 5) only when a tool reads that
  header. Check it without `--fragment`.

## Contract block (flow files and inline SKILL.md)

```text
inputs:
  request, design
order:
  verify design has an assurance table before write implementation
  never write * with design_docs before exec guard start
```

- `inputs:` names values the flows may use unbound (U1 otherwise).
- `order:` rules: `<earlier> before <later>` (P1: the earlier step
  completes on every path before the later step starts) and `never
  <earlier> before <later>` (P3: the later step may not start once the
  earlier one may have run, including inside flows it `run`s). Sides are
  statement prefixes; `*` matches any text; a typed reference
  (`verify#table`, `return#result`) matches the statement carrying that ID.
- Give every rule's earlier step a signal outside the model: an `exec`
  result cited by `verify ... from`, a written artifact, or a user
  decision. A rule resting on the model's own judgment warns (W15).

## Statements (closed vocabulary, SPEC 6)

| Form | Meaning |
|---|---|
| `require <condition>` | must hold to continue; may take an `otherwise:` repair |
| `verify <claim> from <binding>` | check against evidence; `verify #id ...` gives it an ID |
| `read <thing> from <resource> as <name>` | load; may take `otherwise:` |
| `write <binding> with <resource>` | change a resource (a mutation) |
| `exec <command> from <resource> as <name>` | run a command (a mutation unless `exec readonly ...`) |
| `generate <thing> from <inputs> as <name>` | the model produces a value |
| `apply <spec> with <input> as <name>` | the model transforms a value; define `<spec>` under Step meanings (W12) |
| `ask user to <decide>` then `require user <decides>` | a decision: no `as` on the ask (A2) |
| `ask user for <thing> as <name>` | an input question |
| `show <binding>` | display |
| `run <flow> [from <file>] with:` + `name = binding` lines | call a flow |
| `if / unless / when <condition>:` and `else:` | branches |
| `for each <list> as <item>:` | loop; do not rebind the list inside (L1) |
| `label <name>:` / `return to <name>` | a jump target in the same flow |
| `return <binding> as <name>` or `return:` block | exit; `return #id ...` names the exit |
| `abort with "<message>"` | stop with a reason |

Conditions stay natural language. Indentation is structure (two spaces).

## Rules that catch most drafts

| Code | Rule | Fix |
|---|---|---|
| U1 | a name is used where some path has not bound it | bind it on every path, or list it in `inputs:` |
| O1 | `otherwise:` sits only directly under `require`, `verify`, `read`, `open` | move the repair under its gate |
| L3 | `retry` only inside an `otherwise:` block | use `return to <label>` elsewhere |
| W9 | a repair falls through | end it with `retry`, `return to`, `abort` or `return` |
| M1 | a write or non-readonly `exec` happens before an `ask` | ask first; a dismissed ask must leave nothing changed |
| A2 | `require user ...` without a decision `ask` before it, or an ask with no following `require` | pair them; decision asks take no `as` |
| P1 / P3 | an order or exclusion rule is broken on some path | move the step the message names; the hint says where |
| W12 | an `apply` spec has no step meaning | add `- **<spec>**: ...` under Step meanings |
| W13 | an order rule's later step matches no statement | fix the rule's wording to match a statement prefix |

A warning is not a pass. Repair the represented control flow; never
delete a requirement or a rule to silence the checker.

## Worked example (checked in this package's tests)

````markdown
---
name: release-notes
description: Draft release notes from merged changes and publish them after the maintainer approves. Use when asked to write or publish release notes.
---

# Release notes

```contract
inputs:
  request
order:
  verify #changes before generate notes
  ask user to approve the notes before write notes
```

```logic
release-notes:
  require request exists
    otherwise:
      abort with "Name the release to write notes for."

  exec readonly changelog query from tools as changes
  verify #changes the query listed at least one merged change from changes
    otherwise:
      abort with "No merged changes since the last release."

  generate notes from changes as notes
  apply house style with request as notes
  show notes
  ask user to approve the notes
  require user approves the notes
    otherwise:
      abort with "Notes not approved; nothing was written."

  write notes with release_file
  return notes as notes
```

| Step | Command |
|---|---|
| `exec readonly changelog query` | `git log --oneline <last tag>..HEAD` |

## Step meanings

- **house style**: past tense, one line per change, grouped by area.
- **tools**: the repository's command line. **release_file**: `RELEASE.md`.
````

## Commands

`SW check --fragment --summary --audit SKILL.md flows/*.md` (flow files and
inline skills), `SW check FILE` (complete skills), `SW explain-workflow
FILE` (the deterministic reading a user reviews), `SW build DIR --out
DEST` (package), `SW approve FILE` (the user records approval of exact
bytes; never run it for them). Exit 0 no errors, 1 errors, 2 usage.
