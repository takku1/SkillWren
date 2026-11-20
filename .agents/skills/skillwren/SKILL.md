---
name: skillwren
description: Build a new agent skill, or convert an existing SKILL.md, as checked SkillWren logic - explicit steps, gates and ordering rules that a validator checks before the skill ships. Use when asked to create, write, convert, check or package a skill.
---

# SkillWren in this checkout

This is a pointer for Codex working inside the SkillWren repository. The
skill lives at `skills/skillwren/` (three directories above this one):
read [its SKILL.md](../../../skills/skillwren/SKILL.md) and follow it,
resolving "this skill's directory" to `skills/skillwren/`. Its launcher,
`skills/skillwren/scripts/skillwren.py`, runs this checkout's `src/` with
Python 3.9+ (`py -3` on Windows, `python3` elsewhere) and needs no
installation.

Outside this repository, install the plugin instead (README, "Install the
skill"), or copy `plugin/skillwren/` into a skills folder: it bundles the
checker.
