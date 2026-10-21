"""Malformed input should produce diagnostics, never an analysis traceback."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from skillwren.validator import validate_files


class TestInputRobustness(unittest.TestCase):
    def validate_bytes(self, data):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "skill.md"
            path.write_bytes(data)
            return validate_files([str(path)])[str(path)]

    def test_invalid_utf8_is_diagnostic(self):
        errors, _ = self.validate_bytes(b"\xff\xfe\x00invalid")
        self.assertIn("F1", {error.rule for error in errors})

    def test_bad_schema_does_not_reach_semantic_analysis(self):
        text = (ROOT / "tests/fixtures/valid-skeleton.md").read_text(encoding="utf-8")
        import re
        for section in ("accepts", "produces"):
            broken = re.sub(r"(?m)^" + section + r":.*(?:\n[ \t]+.*)*", section + ": [wrong]", text)
            with self.subTest(section=section):
                errors, _ = self.validate_bytes(broken.encode("utf-8"))
                self.assertIn("F1", {error.rule for error in errors})

    def test_duplicate_header_key_is_rejected(self):
        text = (ROOT / "tests/fixtures/valid-skeleton.md").read_text(encoding="utf-8")
        text = text.replace("\n---\n", "\nrisk: high\n---\n", 1)
        errors, _ = self.validate_bytes(text.encode("utf-8"))
        self.assertIn("F1", {error.rule for error in errors})

    def test_nested_trigger_value_does_not_crash_batch(self):
        text = (ROOT / "tests/fixtures/valid-skeleton.md").read_text(encoding="utf-8")
        import re
        text = re.sub(r"(?m)^owns-when:.*(?:\n[ \t]+.*)*",
                      "owns-when:\n  - {bad: value}", text)
        errors, _ = self.validate_bytes(text.encode("utf-8"))
        self.assertIn("F1", {error.rule for error in errors})
