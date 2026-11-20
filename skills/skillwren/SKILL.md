---
name: skillwren
description: Build a new agent skill, or convert an existing SKILL.md, as checked SkillWren logic - explicit steps, gates and ordering rules that a validator checks before the skill ships. Use when asked to create, write, convert, check or package a skill.
---

# SkillWren

SkillWren is a small, closed language for agent procedures: a `logic` block
of explicit steps, gates (`require`, `verify`) with owned repairs, and
`order:` rules, checked statically before anyone relies on them. The
`logic` block below is this skill's procedure; follow it in order. Each
`exec` step runs a command from the table; the sections after it define the
other steps. Language reference: [references/language.md](references/language.md)
(read it before drafting). Full grammar: `references/SPEC.md`; authoring
advice: `references/authoring-guide.md`.

```contract
inputs:
  request, source
order:
  ask user to confirm the requirement inventory before write draft
  verify the draft has no errors before exec skill build
  exec workflow explanation before exec skill build
```

```logic
skillwren:
  require request exists
    otherwise:
      abort with "Say what the skill should do, or name the SKILL.md to convert."

  if request is ambiguous on outcome, inputs, or authority:
    ask user to clarify the outcome, inputs, and authority as clarification
    apply update with clarification as request

  if request names an existing skill to convert:
    read original skill and its references from source as original
    generate requirement inventory from original as requirements
  else:
    generate requirement inventory from request as requirements

  label confirming:
  show requirements
  ask user to confirm the requirement inventory
  require user confirms the requirement inventory
    otherwise:
      ask user for the missing or wrong requirements as corrections
      apply inventory revision with corrections as requirements
      return to confirming

  read language reference from references as language
  generate skill draft from requirements as draft
  apply language rules with language as draft
  write draft with workdir

  label checking:
  exec skill check from launcher as checked
  verify the draft has no errors and every warning is fixed or explained from checked
    otherwise:
      apply check repair with checked as draft
      write draft with workdir
      exec skill check from launcher as checked
      retry

  verify every requirement lands in a step, gate, order rule, or step meaning from requirements
    otherwise:
      apply requirement repair with requirements as draft
      write draft with workdir
      return to checking

  exec workflow explanation from launcher as explanation
  exec skill build from launcher as package
  verify the package built without errors from package
    otherwise:
      apply check repair with package as draft
      write draft with workdir
      return to checking

  return:
    skill = package
    explanation
```

## Commands

`SW` = `python3 <this skill's directory>/scripts/skillwren.py` (Windows:
`py -3 ...`). Python 3.9+, standard library only, nothing to install.
Pass explicit file names, not shell globs.

| Step | Command |
|---|---|
| `exec skill check` | flow files: `SW check --fragment --summary --audit SKILL.md flows/*.md`; a complete skill (contract header): `SW check SKILL.md` |
| `exec workflow explanation` | `SW explain-workflow <file>` for each file with a `logic` block |
| `exec skill build` | `SW build <draft dir> --out <destination>` (a complete skill: `SW build <file> --out <destination>`) |

Exit 0 means no errors, 1 means errors, 2 means a usage failure. A warning
is not a pass: fix it or say why it is acceptable.

## Step meanings

- **workdir**: a new draft folder the user names, else `<name>-draft/` in
  the working directory. Never edit the original skill in place.
- **source**: the skill to convert: its `SKILL.md` and every file it links
  to that changes a decision.
- **references**: `references/language.md` in this skill's directory.
- **launcher**: `scripts/skillwren.py` in this skill's directory.
- **update**: fold the user's answer into the request.
- **requirement inventory**: one line per obligation, prohibition,
  condition, exception, ordering ("do X before Y"), evidence standard and
  output, quoted from the source or the request. Nothing is merged or
  dropped silently; mark anything you infer as inferred.
- **skill draft**: a `SKILL.md` with `name` and `description` frontmatter,
  a `contract` block (`inputs:`, and `order:` for every ordering in the
  inventory), one `logic` block per procedure, a command table for every
  `exec`, and a step meaning for every `apply`. Split into `flows/*.md`
  only when parts load at different times.
- **language rules**: the rules in `references/language.md`: closed
  vocabulary, gates with owned repairs, a signal outside the model behind
  every order rule, `ask` followed by `require user ...`.
- **check repair**: fix what the checker reported in the represented
  control flow. Never weaken a requirement or delete a rule to silence it.
- **requirement repair**: add the missing requirement where it belongs, or
  ask the user whether to drop it. A requirement may not disappear.
- **inventory revision**: add, correct or remove the lines the user named,
  then show the whole inventory again.

## Output

Return the built skill's path, the workflow explanation, the requirement
inventory with where each line landed, and limits: a clean check proves
the written procedure is well formed and ordered, not that a model will
follow it or that it does what the user meant beyond the inventory they
confirmed. The explanation is generated from the logic itself, so ask the
user to read it; if they accept it, they record that with `SW approve
<file>` (a human step: never run `approve` on their behalf). Do not
install the skill or run paid model evaluations unless asked.
