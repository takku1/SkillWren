"""Shared mutant catalog for the tripwire (test_mutations.py) and the sweep
(mutation_sweep.py).

Each mutant breaks exactly one structural property of a valid base skill.
Mutants are data: per-base text edits plus the set of acceptable blame
rules. A mutant that validates clean is a beta-miss (validator hole or bad
mutant); a mutant killed without an expected rule is an alpha-deviation
(diagnostic drift).
"""

BASES = {
    "skeleton": "tests/fixtures/valid-skeleton.md",
    "golden": "examples/theme-factory.golden.md",
    "else": "tests/fixtures/valid-else.md",
    "exec": "tests/fixtures/valid-exec.md",
}


def sub(old, new, count=1):
    """Build a one-break edit: replace `old` with `new`, asserting the
    pattern exists exactly as written so catalog rot fails loudly."""
    def edit(text):
        assert old in text, f"catalog pattern missing: {old!r}"
        out = text.replace(old, new, count)
        assert out != text
        return out
    return edit


def move_save_before_ask(text):
    save = "  save spec as themes/{name}.md\n"
    ask = "  ask user to approve generated theme"
    assert save in text and ask in text
    return text.replace(save, "", 1).replace(ask, save + ask, 1)


def move_return_early(text):
    ret = "  return output as output\n"
    gen = "  generate result from input as output\n"
    assert ret in text and gen in text
    return text.replace(ret, "", 1).replace(gen, ret + gen, 1)


def duplicate_flow_fence(text):
    return text + "\n```logic\nmain:\n  return output as output\n```\n"


# name -> {edits: {base: edit}, rules: {acceptable blame rules}}
MUTANTS = [
    # --- skeleton base: one mutant per rule family ---
    {"name": "drop-leading-require",
     "edits": {"skeleton": sub("  require input exists\n", "")},
     "rules": {"R1"}},
    {"name": "drop-otherwise-line",
     "edits": {"skeleton": sub(
         "  require input exists\n    otherwise:\n"
         "      abort with \"An input is required.\"",
         "  require input exists\n"
         "      abort with \"An input is required.\"")},
     "rules": {"O1"}},
    {"name": "unbind-use",
     "edits": {"skeleton": sub(
         "  generate result from input as output",
         "  generate result from ghost as output")},
     "rules": {"U1"}},
    {"name": "return-undeclared",
     "edits": {"skeleton": sub(
         "  return output as output", "  return output as missing")},
     "rules": {"R2"}},
    {"name": "require-user-no-ask",
     "edits": {"skeleton": sub(
         "  show output\n", "  require user approves\n\n  show output\n")},
     "rules": {"A2"}},
    {"name": "stray-retry",
     "edits": {"skeleton": sub(
         "  return output as output", "  retry\n  return output as output")},
     "rules": {"L3"}},
    {"name": "otherwise-under-show",
     "edits": {"skeleton": sub(
         "  show output\n",
         "  show output\n    otherwise:\n      abort with \"x\"\n")},
     "rules": {"O1"}},
    {"name": "bad-fence",
     "edits": {"skeleton": sub("```logic", "```logik")},
     "rules": {"F2"}},
    {"name": "access-typo",
     "edits": {"skeleton": sub("    access: read", "    access: Read")},
     "rules": {"F2"}},
    {"name": "budget-zero",
     "edits": {"skeleton": sub(
         "budget: { header: 400, body: 2500 }",
         "budget: { header: 0, body: 2500 }")},
     "rules": {"F1"}},
    {"name": "version-bump",
     "edits": {"skeleton": sub("version: 0.3", "version: 9.9")},
     "rules": {"F1"}},
    {"name": "unbalanced-type",
     "edits": {"skeleton": sub(
         "input: { type: Text, required: true }",
         "input: { type: List<Text, required: true }")},
     "rules": {"F1"}},
    {"name": "move-return-early",
     "edits": {"skeleton": move_return_early},
     "rules": {"U1"}},
    {"name": "duplicate-flow-fence",
     "edits": {"skeleton": duplicate_flow_fence},
     "rules": {"F2"}},
    {"name": "save-before-ask",
     "edits": {"skeleton": sub(
         "  ask user to approve output",
         "  save output as output\n  ask user to approve output")},
     "rules": {"M1"}},
    # --- golden base: production-shape breaks the skeleton cannot express ---
    {"name": "golden-stray-retry",
     "edits": {"golden": sub(
         "  apply spec with artifact as styled",
         "  retry\n  apply spec with artifact as styled")},
     "rules": {"L3"}},
    {"name": "golden-require-user-no-ask",
     "edits": {"golden": sub(
         "      ask user to accept the font substitution\n", "")},
     "rules": {"A2"}},
    {"name": "golden-access-comma",
     "edits": {"golden": sub(
         "    access: read+create", "    access: read, create")},
     "rules": {"F2"}},
    {"name": "golden-save-before-ask",
     "edits": {"golden": move_save_before_ask},
     "rules": {"M1"}},
    {"name": "golden-run-unbound-arg",
     "edits": {"golden": sub("    theme = name", "    theme = ghost")},
     "rules": {"U1"}},
    {"name": "golden-run-bad-target",
     "edits": {"golden": sub("run apply-theme with:", "run apply-themes with:")},
     "rules": {"R3"}},
    {"name": "golden-version-potato",
     "edits": {"golden": sub("version: 0.4", "version: potato")},
     "rules": {"F1"}},
    {"name": "golden-return-undeclared",
     "edits": {"golden": sub(
         "  return styled as styled_artifact", "  return styled as nope")},
     "rules": {"R2"}},
    {"name": "golden-drop-otherwise",
     "edits": {"golden": sub(
         "  require theme fonts are available\n    otherwise:\n",
         "  require theme fonts are available\n")},
     "rules": {"O1"}},
    # --- format 0.5 bases (full-stack backfill BF-6, BF-7) ---
    {"name": "else-arm-unbinds",
     "edits": {"else": sub(
         "    generate copy from input as output\n", "    show input\n")},
     "rules": {"U1"}},
    {"name": "else-after-non-branch",
     "edits": {"else": sub(
         "  if input is long:\n    generate summary from input as output\n",
         "  generate summary from input as output\n")},
     "rules": {"O1", "U1"}},
    {"name": "drop-executes-entry",
     "edits": {"exec": sub("  executes: [checks]\n", "")},
     "rules": {"E2"}},
    {"name": "verify-cites-unbound-evidence",
     "edits": {"exec": sub(
         "  exec acceptance checks from checks as results\n",
         "  exec acceptance checks from checks as outcome\n")},
     "rules": {"U1", "W5"}},
]
