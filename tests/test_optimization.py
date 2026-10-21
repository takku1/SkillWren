"""A compact build must pass structure, review bookkeeping, and real size gates."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skillwren.compiler import BuildError, _compile, build
from skillwren.metrics import MeasurementError, compare
from skillwren.review import digest, read_originals, validate_review


class TestMeasurements(unittest.TestCase):
    def test_known_character_reduction(self):
        report = compare([b"abcdefghij"], b"abcde", metric="characters")
        self.assertEqual((report["saved"], report["reduction_percent"]), (5, 50))
        self.assertTrue(report["accepted"])
        self.assertIsNone(report["tokenizer"])

    def test_equality_is_not_an_optimization(self):
        self.assertFalse(compare([b"same"], b"same", metric="characters")["accepted"])

    def test_minimum_saving_can_be_required(self):
        self.assertFalse(compare([b"abcdefghij"], b"abcdefghi", metric="characters", max_ratio=.8)["accepted"])
        self.assertTrue(compare([b"abcdefghij"], b"abcdefgh", metric="characters", max_ratio=.8)["accepted"])

    def test_empty_original_and_invalid_limits_fail(self):
        for originals, ratio in [([], 1), ([b""], 1), ([b"a"], 0),
                                  ([b"a"], float("nan")), ([b"a"], 1.1), ([b"a"], True)]:
            with self.subTest(originals=originals, ratio=ratio), self.assertRaises(MeasurementError):
                compare(originals, b"", metric="characters", max_ratio=ratio)

    def test_original_reference_boundaries_count(self):
        report = compare([b"abc", b"def"], b"abcdefg", metric="characters")
        self.assertEqual(report["original"]["count"], 8)  # Includes the explicit double-newline join.
        self.assertEqual(report["original"]["files"], 2)

    def test_no_estimate_fallback_when_tokenizer_is_unavailable(self):
        with patch.dict(sys.modules, {"tiktoken": None}):
            with self.assertRaisesRegex(MeasurementError, "exact token measurement"):
                compare([b"original"], b"short")

    @unittest.skipUnless(importlib.util.find_spec("tiktoken"), "optional tiktoken not installed")
    def test_special_token_spellings_are_plain_skill_text(self):
        import tiktoken
        text = "<|endoftext|>"
        report = compare([text.encode()], b"short")
        self.assertEqual(report["original"]["count"], len(tiktoken.get_encoding(
            "cl100k_base").encode(text, disallowed_special=())))


class TestOptimizedBuild(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "logic.md"
        self.source.write_bytes((ROOT / "tests/fixtures/valid-skeleton.md").read_bytes())
        self.original = self.root / "original.md"
        self.original.write_bytes(b"Retain all the original requirements and exceptions.\n" * 100)
        self.review_path = self.root / "review.json"
        self.review = {"original_sha256": digest(self.original.read_bytes()),
                       "logic_sha256": digest(self.source.read_bytes()), "requirements": [
                           {"id": "all", "original_lines": [1, 100],
                            "logic_contains": ["require input exists", "return output as output"]}]}
        self.write_review()

    def write_review(self):
        self.review_path.write_text(json.dumps(self.review), encoding="utf-8")

    def build(self, **kwargs):
        return build(self.source, self.root / "built", original=self.original,
                     review=self.review_path, metric="characters", **kwargs)

    def test_archive_is_outside_a_smaller_prompt(self):
        report = self.build()
        compiled = (self.root / "built/SKILL.md").read_bytes()
        self.assertTrue(report["optimization"]["accepted"])
        self.assertFalse(report["optimization"]["audit_in_prompt"])
        self.assertNotIn(self.original.read_bytes(), compiled)
        archived = report["sources"]["audit/originals/original.md"]["base64"]
        self.assertEqual(base64.b64decode(archived), self.original.read_bytes())

    def test_expanded_context_is_measured_not_hidden(self):
        (self.root / "large.md").write_bytes(b"Important context.\n" * 400)
        with self.source.open("ab") as stream:
            stream.write(b'\n@context large from "large.md" as instruction\n')
        self.review["logic_sha256"] = digest(self.source.read_bytes())
        self.write_review()
        with self.assertRaisesRegex(BuildError, "size target"):
            self.build()
        self.assertFalse((self.root / "built").exists())

    def test_review_and_original_are_paired(self):
        with self.assertRaisesRegex(BuildError, "both original and review"):
            build(self.source, self.root / "built", original=self.original)

    def test_stale_original_fails(self):
        self.original.write_bytes(self.original.read_bytes() + b"New obligation.\n")
        with self.assertRaisesRegex(BuildError, "original changed"):
            self.build()

    def test_stale_candidate_fails(self):
        self.source.write_bytes(self.source.read_bytes() + b"\nA new note.\n")
        with self.assertRaisesRegex(BuildError, "candidate changed"):
            self.build()

    def test_missing_requirement_span_fails(self):
        self.review["requirements"][0]["original_lines"] = [1, 99]
        self.write_review()
        with self.assertRaisesRegex(BuildError, "unmapped original lines"):
            self.build()

    def test_duplicate_id_and_invalid_spans_fail(self):
        for mutation in ("duplicate", "bool-span", "unknown-file", "no-anchor"):
            review = json.loads(json.dumps(self.review))
            if mutation == "duplicate":
                review["requirements"] *= 2
            elif mutation == "bool-span":
                review["requirements"][0]["original_lines"] = [True, 100]
            elif mutation == "unknown-file":
                review["requirements"][0]["original_file"] = "absent.md"
            else:
                review["requirements"][0]["logic_contains"] = ["unimplemented obligation"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_review(read_originals(self.original), self.source.read_bytes(),
                                self.source.read_bytes(), review)

    def test_selected_original_references_need_review_and_are_archived(self):
        context = self.root / "reference.md"
        context.write_bytes(b"Additional domain facts.\n")
        self.review["original_context_sha256"] = {"reference.md": digest(context.read_bytes())}
        self.review["requirements"].append({"id": "reference", "original_file": "reference.md",
            "original_lines": [1, 1], "logic_contains": ["return output as output"]})
        self.write_review()
        report = self.build(original_context=[context])
        self.assertEqual(report["optimization"]["original"]["files"], 2)
        self.assertIn("audit/originals/reference.md", report["sources"])

    def test_reference_omission_and_duplicate_count_padding_fail(self):
        context = self.root / "reference.md"
        context.write_bytes(b"Facts.\n")
        self.review["original_context_sha256"] = {"reference.md": digest(context.read_bytes())}
        self.write_review()
        with self.assertRaisesRegex(BuildError, "context changed"):
            self.build()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            read_originals(self.original, [self.original])

    def test_cli_measures_a_candidate_as_one_json_document(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        result = subprocess.run([sys.executable, "-m", "skillwren", "measure",
            str(self.original), str(self.source), "--metric", "characters", "--json"],
            env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["accepted"])

    def test_unchanged_original_does_not_pass_by_relabeling_it(self):
        self.original.write_bytes(self.source.read_bytes())
        self.review["original_sha256"] = digest(self.original.read_bytes())
        self.review["requirements"][0]["original_lines"] = [1, len(self.source.read_text().splitlines())]
        self.write_review()
        with self.assertRaisesRegex(BuildError, "strictly smaller"):
            self.build()

    @unittest.skipUnless(importlib.util.find_spec("tiktoken"), "optional tiktoken not installed")
    def test_worked_example_passes_real_token_and_review_gates(self):
        example = ROOT / "examples/optimization"
        report = build(example / "SKILL.md", self.root / "worked",
                       original=example / "original.md", review=example / "review.json")
        self.assertTrue(report["optimization"]["accepted"])
        self.assertEqual(report["optimization"]["metric"], "tokens")
        self.assertEqual(report["optimization"]["review"]["requirements"], 6)

    def test_cli_rejects_unreviewed_conversion_before_publication(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        output = self.root / "unreviewed"
        result = subprocess.run([sys.executable, "-m", "skillwren", "build", str(self.source),
            "--original", str(self.original), "--out", str(output)],
            env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_cli_build_accepts_reviewed_reduction(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        output = self.root / "reviewed"
        result = subprocess.run([sys.executable, "-m", "skillwren", "build", str(self.source),
            "--original", str(self.original), "--review", str(self.review_path),
            "--metric", "characters", "--out", str(output)],
            env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["optimization"]["accepted"])


if __name__ == "__main__":
    unittest.main()
