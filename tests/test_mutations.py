"""Mutation tripwire (beta): no one-break mutant may validate clean.

Runs the shared catalog (tests/mutation_catalog.py) and asserts both
mutation properties:

- beta (recall): every mutant produces at least one error. A survivor is
  a validator hole or a bad mutant, never a pass.
- alpha (precision): every kill includes the mutant's expected rule.
  A wrong-rule kill is diagnostic drift.

Failures print the mutant text so the break is inspectable. For the full
kill matrix across bases, run `python3 tests/mutation_sweep.py`.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import skillwren
from mutation_catalog import BASES, MUTANTS


def base_texts():
    return {b: (ROOT / rel).read_text() for b, rel in BASES.items()}


def validate_text(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(text)
        case = f.name
    try:
        return skillwren.validate_file(case)
    finally:
        Path(case).unlink()


def each_mutant():
    texts = base_texts()
    for mutant in MUTANTS:
        for base, edit in mutant["edits"].items():
            yield mutant, base, edit(texts[base])


class TestMutationTripwire(unittest.TestCase):
    def test_bases_are_clean(self):
        for base, rel in BASES.items():
            with self.subTest(base=base):
                errors, _ = skillwren.validate_file(str(ROOT / rel))
                self.assertEqual(errors, [])

    def test_no_mutant_survives_beta(self):
        for mutant, base, text in each_mutant():
            with self.subTest(mutant=mutant["name"], base=base):
                errors, _ = validate_text(text)
                self.assertGreater(
                    len(errors), 0,
                    f"BETA-MISS: one-break mutant validated clean:\n{text}")

    def test_mutants_blamed_correctly_alpha(self):
        for mutant, base, text in each_mutant():
            with self.subTest(mutant=mutant["name"], base=base):
                errors, _ = validate_text(text)
                rules = {d.rule for d in errors}
                self.assertTrue(
                    mutant["rules"] & rules,
                    f"ALPHA-DEVIATION: expected {sorted(mutant['rules'])}, "
                    f"got {sorted(rules)}:\n{text}")


if __name__ == "__main__":
    unittest.main()
