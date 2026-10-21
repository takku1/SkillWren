"""Markdown language compilation and exact context retention."""
import base64
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from skillwren.compiler import BuildError, build
from skillwren.validator import validate_file


class TestCompiler(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.md"
        self.text = (ROOT / "tests/fixtures/valid-skeleton.md").read_text(encoding="utf-8")

    def prepare(self, payload=b"Never omit an exception.\r\n", directive=None):
        self.payload = payload
        (self.root / "reference.md").write_bytes(payload)
        self.source.write_text(self.text + "\n" + (directive or
            '@context rubric from "reference.md" as instruction') + "\n", encoding="utf-8")

    def test_build_retains_exact_sources_and_expands_context(self):
        self.prepare()
        out = self.root / "built"
        build(self.source, out)
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
        compiled = (out / "SKILL.md").read_bytes()
        self.assertEqual(base64.b64decode(manifest["sources"]["reference.md"]["base64"]), self.payload)
        self.assertEqual(base64.b64decode(manifest["sources"]["source.md"]["base64"]), self.source.read_bytes())
        span = manifest["contexts"][0]
        self.assertEqual(compiled[span["start_byte"]:span["end_byte"]], self.payload)
        self.assertEqual(validate_file(out / "SKILL.md")[0], [])

    def test_code_examples_are_context_not_executable_flows(self):
        self.prepare(b"Example only:\n```logic\nnot-a-real-flow:\n  delete everything\n```\n````\n")
        out = self.root / "built"
        build(self.source, out)
        self.assertEqual(validate_file(out / "SKILL.md")[0], [])

    def test_unicode_and_no_final_newline_are_preserved(self):
        self.prepare("Exception: caf\u00e9 \u65e5\u672c\u8a9e".encode("utf-8"))
        out = self.root / "built"
        build(self.source, out)
        self.assertIn(self.payload, (out / "SKILL.md").read_bytes())

    def test_missing_context_fails_without_output(self):
        self.prepare(directive='@context missing from "absent.md" as instruction')
        with self.assertRaises(BuildError):
            build(self.source, self.root / "built")
        self.assertFalse((self.root / "built").exists())

    def test_duplicate_context_id_is_rejected(self):
        directive = '@context rubric from "reference.md" as instruction'
        self.prepare(directive=directive + "\n" + directive)
        with self.assertRaisesRegex(BuildError, "duplicate"):
            build(self.source, self.root / "built")

    def test_context_cannot_escape_source_directory(self):
        self.prepare(directive='@context outside from "../outside.md" as data')
        with self.assertRaisesRegex(BuildError, "outside"):
            build(self.source, self.root / "built")

    def test_unknown_role_is_not_silently_ignored(self):
        self.prepare(directive='@context rubric from "reference.md" as executable')
        with self.assertRaises(BuildError):
            build(self.source, self.root / "built")

    def test_invalid_control_flow_is_rejected(self):
        self.text = self.text.replace("return output as output", "unknown-operation output")
        self.prepare()
        with self.assertRaisesRegex(BuildError, "V1"):
            build(self.source, self.root / "built")

    def test_existing_output_is_not_overwritten(self):
        self.prepare()
        out = self.root / "built"
        out.mkdir()
        (out / "SKILL.md").write_text("existing")
        with self.assertRaises(BuildError):
            build(self.source, out)
        self.assertEqual((out / "SKILL.md").read_text(), "existing")

    def test_context_cannot_hide_real_flow_after_it(self):
        self.prepare()
        self.source.write_text(self.source.read_text(encoding="utf-8") +
            "\n```logic\nextra:\n  abort with no\n```\n", encoding="utf-8")
        with self.assertRaises(BuildError):
            build(self.source, self.root / "built")

    def test_unclosed_opaque_context_is_diagnostic(self):
        self.source.write_text(self.text + "\n````context rubric instruction\ntext", encoding="utf-8")
        self.assertIn("F2", {d.rule for d in validate_file(self.source)[0]})

    def test_oversized_context_fails_instead_of_truncating(self):
        self.prepare(b"Important context. " * 1000)
        with self.assertRaisesRegex(BuildError, "B1"):
            build(self.source, self.root / "built")
        self.assertFalse((self.root / "built").exists())

    def test_build_is_deterministic(self):
        self.prepare()
        build(self.source, self.root / "one")
        build(self.source, self.root / "two")
        for name in ("SKILL.md", "manifest.json"):
            self.assertEqual((self.root / "one" / name).read_bytes(),
                             (self.root / "two" / name).read_bytes())

    def test_shipped_example_builds(self):
        manifest = build(ROOT / "examples/context-build/SKILL.md", self.root / "built")
        self.assertEqual(len(manifest["contexts"]), 2)

    def test_cli_build_and_check(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        out = self.root / "built"
        command = [sys.executable, "-m", "skillwren"]
        built = subprocess.run(command + ["build", str(ROOT / "examples/context-build/SKILL.md"),
                                          "--out", str(out)], env=env, capture_output=True, text=True)
        self.assertEqual(built.returncode, 0, built.stderr)
        checked = subprocess.run(command + ["check", str(out / "SKILL.md")],
                                 env=env, capture_output=True, text=True)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
