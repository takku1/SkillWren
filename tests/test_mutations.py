"""Mutation spike: can a one-break mutant of a valid skill validate clean?

Takes tests/fixtures/valid-skeleton.md, applies one structural break at a
time, and asserts the validator errors (with the expected rule). A mutant
that validates clean is either a validator hole (fix the validator and keep
the mutant) or a still-valid program (fix the mutant).
"""
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.insert(0, str(ROOT / "src"))
import skillwren


def base_text():
    return (ROOT / "tests/fixtures/valid-skeleton.md").read_text()


def drop_leading_require(text):
    return text.replace("  require input exists\n", "", 1)


def drop_otherwise_line(text):
    old = ("  require input exists\n    otherwise:\n"
           "      abort with \"An input is required.\"")
    new = ("  require input exists\n"
           "      abort with \"An input is required.\"")
    assert old in text
    return text.replace(old, new, 1)


def unbind_use(text):
    old = "  generate result from input as output"
    assert old in text
    return text.replace(old, "  generate result from ghost as output", 1)


def return_undeclared(text):
    old = "  return output as output"
    assert old in text
    return text.replace(old, "  return output as missing", 1)


def require_user_no_ask(text):
    # Before the decision ask: no ask dominates this gate.
    old = "  show output\n"
    assert old in text
    return text.replace(old, "  require user approves\n\n" + old, 1)


def stray_retry(text):
    old = "  return output as output"
    assert old in text
    return text.replace(old, "  retry\n" + old, 1)


def otherwise_under_show(text):
    old = "  show output\n"
    assert old in text
    return text.replace(old, old + "    otherwise:\n      abort with \"x\"\n", 1)


def bad_fence(text):
    assert "```logic" in text
    return text.replace("```logic", "```logik", 1)


def access_typo(text):
    old = "    access: read"
    assert old in text
    return text.replace(old, "    access: Read", 1)


def budget_zero(text):
    old = "budget: { header: 400, body: 2500 }"
    assert old in text
    return text.replace(old, "budget: { header: 0, body: 2500 }", 1)


def version_bump(text):
    old = "version: 0.3"
    assert old in text
    return text.replace(old, "version: 9.9", 1)


def unbalanced_type(text):
    old = "input: { type: Text, required: true }"
    assert old in text
    return text.replace(old, "input: { type: List<Text, required: true }", 1)


def move_return_early(text):
    ret = "  return output as output\n"
    gen = "  generate result from input as output\n"
    assert ret in text and gen in text
    return text.replace(ret, "", 1).replace(gen, ret + gen, 1)


def duplicate_flow_fence(text):
    return text + "\n```logic\nmain:\n  return output as output\n```\n"


def save_before_ask(text):
    old = "  ask user to approve output"
    assert old in text
    return text.replace(old, "  save output as output\n" + old, 1)


# (name, transform, expected rule, exact error count or None)
MUTANTS = [
    ("drop-leading-require", drop_leading_require, "R1", None),
    ("drop-otherwise-line", drop_otherwise_line, "O1", 1),
    ("unbind-use", unbind_use, "U1", 1),
    ("return-undeclared", return_undeclared, "R2", None),
    ("require-user-no-ask", require_user_no_ask, "A2", 1),
    ("stray-retry", stray_retry, "L3", 1),
    ("otherwise-under-show", otherwise_under_show, "O1", 1),
    ("bad-fence", bad_fence, "F2", None),
    ("access-typo", access_typo, "F2", 1),
    ("budget-zero", budget_zero, "F1", 1),
    ("version-bump", version_bump, "F1", 1),
    ("unbalanced-type", unbalanced_type, "F1", 1),
    ("move-return-early", move_return_early, "U1", 1),
    ("duplicate-flow-fence", duplicate_flow_fence, "F2", None),
    ("save-before-ask", save_before_ask, "M1", 1),
]


class TestMutations(unittest.TestCase):
    def test_base_is_clean(self):
        errors, warnings = skillwren.validate_file(
            str(ROOT / "tests/fixtures/valid-skeleton.md"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_one_break_mutants_error(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        case = str(Path(tmp.name) / "case.md")
        for name, transform, rule, count in MUTANTS:
            with self.subTest(mutant=name):
                mutant = transform(base_text())
                self.assertNotEqual(mutant, base_text())
                Path(case).write_text(mutant)
                errors, _ = skillwren.validate_file(case)
                rules = [d.rule for d in errors]
                self.assertIn(rule, rules)
                if count is not None:
                    self.assertEqual(len(errors), count)


if __name__ == "__main__":
    unittest.main()
