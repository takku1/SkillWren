"""Tier 1 for the response to the full-stack field report of 2026-11-19.

Finding 5: exclusion rules (`never A before B`, P3), static and in the ledger.
Finding 6: package provenance (`ledger start --package`, `check --loaded`).
Finding 7: a skipped fragment is `incomplete` with a required milestone.
Finding 8: one typed-reference grammar shared by every consumer.
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import skillwren
from skillwren import compiler, ledger
from skillwren.validator import refs
from skillwren.validator.flowgraph import classify_flow_line
from skillwren.validator.ordering import matches
from skillwren.validator.workflow import _typed_ids, dump_workflow, explain_workflow

DEADLOCK = ROOT / "tests" / "fixtures" / "fragments" / "deadlock"
FLOWS = DEADLOCK / "flows"


def rules(diags):
    return sorted(d.rule for d in diags)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- Finding 8: one grammar -------------------------------------------------

# (id, accepted). Every consumer must agree with this table.
ID_TABLE = [
    ("deps", True), ("a", True), ("final-2", True), ("x9-y", True),
    ("Deps", False), ("DEP", False), ("2deps", False), ("-deps", False),
    ("de_ps", False), ("dé", False),
]


class TestSharedGrammar(unittest.TestCase):
    def test_every_consumer_agrees_on_ids(self):
        for ident, accepted in ID_TABLE:
            with self.subTest(ident=ident):
                statement = f"verify #{ident} the dependencies"
                self.assertEqual(bool(refs.reference(f"verify#{ident}")), accepted)
                self.assertEqual(bool(refs.statement_id(statement)), accepted)
                self.assertEqual(matches(f"verify#{ident}", statement), accepted)
                self.assertEqual(ledger.step_matches(f"verify#{ident}", statement), accepted)
                self.assertEqual(bool(_typed_ids(statement)), accepted)
                kind, data = classify_flow_line(f"return #{ident}:")
                self.assertEqual(kind == "returnblock" and data == ident, accepted)

    def test_renderer_no_longer_accepts_ids_the_validator_ignores(self):
        """The renderer used `#[A-Za-z][\\w-]*` and called `#Deps` addressable."""
        self.assertFalse(_typed_ids("verify #Deps the dependencies"))
        self.assertFalse(_typed_ids("write #de_ps with out"))

    def test_p2_uses_the_same_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = write(Path(tmp) / "f.md", "```logic\nmain:\n"
                         "  verify #deps ok from x\n  verify #deps again from x\n"
                         "  verify #Deps upper from x\n  verify #Deps upper2 from x\n"
                         "  return x as x\n```\n")
            errors, _ = skillwren.validate_fragment(str(flow))
            self.assertEqual([d.msg for d in errors if d.rule == "P2"],
                             ["duplicate operation ID deps"])


# --- Finding 5: exclusion rules, static ---------------------------------------

class TestExclusionRules(unittest.TestCase):
    def frag(self, name):
        return skillwren.validate_fragment(str(FLOWS / name))

    def test_each_fragment_alone_is_clean(self):
        """The field shape: both fragments check clean in isolation."""
        self.assertEqual(self.frag("design.md"), ([], []))
        self.assertEqual(self.frag("implement.md"), ([], []))

    def test_composition_that_deadlocks_is_p3(self):
        errors, _ = self.frag("build.md")
        self.assertEqual(rules(errors), ["P3"])
        self.assertIn("run implement from flows/implement.md", errors[0].msg)
        self.assertIn("implement.md", errors[0].msg)
        self.assertEqual(errors[0].line, 7)

    def test_rule_two_runs_down_still_binds(self):
        """Rules export transitively: implement.md's rule reaches outer.md
        through wrapper.md."""
        self.assertEqual(self.frag("wrapper.md"), ([], []))
        errors, _ = self.frag("outer.md")
        self.assertEqual(rules(errors), ["P3"])
        self.assertIn("run wrapped from flows/wrapper.md", errors[0].msg)
        self.assertIn("implement.md", errors[0].msg)

    def test_same_file_exclusion_is_p3(self):
        errors, _ = self.frag("same-file.md")
        self.assertEqual(rules(errors), ["P3"])
        self.assertIn("exec guard start", errors[0].msg)

    def test_narrowed_rule_admits_the_design_write(self):
        """Full-stack's fix: notes stay writable; only code makes it late."""
        self.assertEqual(self.frag("build-fixed.md"), ([], []))

    def test_later_step_first_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = write(Path(tmp) / "f.md", "```contract\norder:\n"
                         "  never write before exec guard start\n```\n\n```logic\nmain:\n"
                         "  exec guard start from guard as started\n"
                         "  write started with out\n  return started as started\n```\n")
            self.assertEqual(skillwren.validate_fragment(str(flow)), ([], []))

    def test_branch_write_is_enough(self):
        """May-analysis: one path that writes first is a conflict."""
        with tempfile.TemporaryDirectory() as tmp:
            flow = write(Path(tmp) / "f.md", "```contract\norder:\n"
                         "  never write before exec guard start\n```\n\n```logic\nmain:\n"
                         "  if notes are wanted:\n    write request with notes\n"
                         "  exec guard start from guard as started\n"
                         "  return started as started\n```\n")
            errors, _ = skillwren.validate_fragment(str(flow))
            self.assertEqual(rules(errors), ["P3"])

    def test_unused_exclusion_warns_w13(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = write(Path(tmp) / "f.md", "```contract\norder:\n"
                         "  never write before exec nothing\n```\n\n```logic\nmain:\n"
                         "  write request with out\n  return request as request\n```\n")
            errors, warnings = skillwren.validate_fragment(str(flow))
            self.assertEqual(errors, [])
            self.assertEqual(rules(warnings), ["W13"])

    def test_malformed_exclusion_is_f2(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = write(Path(tmp) / "f.md", "```contract\norder:\n"
                         "  never write\n```\n\n```logic\nmain:\n"
                         "  return request as request\n```\n")
            errors, _ = skillwren.validate_fragment(str(flow))
            self.assertIn("F2", rules(errors))

    def test_positive_rules_unchanged(self):
        """`never` entries do not leak into order (P1) consumers."""
        dump = dump_workflow(FLOWS / "implement.md", True)
        self.assertEqual(dump["order_rules"], [])
        self.assertEqual(dump["exclusion_rules"],
                         [{"line": 7, "first": "write", "then": "exec guard start"}])
        text = explain_workflow(FLOWS / "implement.md", True)
        self.assertIn("never 'write' before 'exec guard start'", text)


# --- Finding 5: exclusion rules on a recorded trace ------------------------------

class TestLedgerExclusions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def start(self):
        return ledger.start(FLOWS / "implement.md", self.dir)[1]

    def test_rules_committed_at_start(self):
        head = ledger.load(self.start())[0]
        self.assertEqual(head["rules"], [])
        self.assertEqual(head["exclusions"][0]["first"], "write")

    def test_write_before_start_is_a_violation(self):
        path = self.start()
        ledger.note_step(path, "write design with design_docs")
        ledger.exec_step(path, "exec guard start", [sys.executable, "-c", "print(1)"])
        report = ledger.check(path)
        self.assertFalse(report["ok"])
        self.assertFalse(report["ordering_valid"])
        self.assertEqual(report["completeness"], "violations")
        self.assertEqual(len(report["exclusions"][0]["violations"]), 1)

    def test_failed_attempt_still_counts(self):
        path = self.start()
        ledger.attempt_step(path, "write design", "blocked by hook")
        ledger.note_step(path, "exec guard start")
        self.assertFalse(ledger.check(path)["ok"])

    def test_start_then_write_is_valid(self):
        path = self.start()
        ledger.exec_step(path, "exec guard start", [sys.executable, "-c", "print(1)"])
        ledger.note_step(path, "write implementation with subject")
        report = ledger.check(path)
        self.assertTrue(report["ok"])
        self.assertTrue(report["exclusions"][0]["exercised"])

    def test_runs_without_exclusions_keep_their_start_record(self):
        path = ledger.start(ROOT / "tests/fixtures/fragments/skill/flows/build-fixed.md",
                            self.dir)[1]
        head = ledger.load(path)[0]
        self.assertNotIn("exclusions", head)
        self.assertNotIn("package", head)


# --- Finding 6: package provenance --------------------------------------------

class TestPackageProvenance(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.repo = base / "repo"
        shutil.copytree(DEADLOCK, self.repo)
        self.cache = base / "cache"
        shutil.copytree(DEADLOCK, self.cache)
        self.dir = base / "ledger"
        self.flow = self.repo / "flows" / "implement.md"
        for tree in (self.repo, self.cache):  # keep a set that builds clean
            for name in ("build.md", "same-file.md", "outer.md"):
                (tree / "flows" / name).unlink()

    def test_build_refuses_a_deadlocking_set(self):
        with self.assertRaises(compiler.BuildError) as raised:
            compiler.build_fragments(DEADLOCK, Path(self.tmp.name) / "bad")
        self.assertIn("P3", str(raised.exception))

    def test_build_manifest_digest_matches_source_and_artifact(self):
        out = Path(self.tmp.name) / "built"
        manifest = compiler.build_fragments(self.repo, out)
        self.assertEqual(manifest["tree_sha256"],
                         ledger.package_identity(self.repo)["tree_sha256"])
        self.assertEqual(manifest["tree_sha256"],
                         ledger.package_identity(out)["tree_sha256"])
        self.assertIsNotNone(ledger.package_identity(out)["manifest_sha256"])

    def test_matching_loaded_copy_passes(self):
        path = ledger.start(self.flow, self.dir, package=self.repo)[1]
        report = ledger.check(path, loaded=self.cache)
        self.assertTrue(report["package_consistent"])
        self.assertTrue(report["ok"])

    def test_stale_loaded_copy_fails(self):
        """The field case: the host loaded an older SKILL.md and hook."""
        write(self.cache / "SKILL.md", "---\nname: deadlock-demo\ndescription: old\n---\n")
        write(self.cache / "hooks" / "guard.py", "# 0.8.0 hook\n")
        path = ledger.start(self.flow, self.dir, package=self.repo)[1]
        report = ledger.check(path, loaded=self.cache)
        self.assertFalse(report["package_consistent"])
        self.assertFalse(report["ok"])
        self.assertTrue(report["valid"])  # the order rules themselves held
        self.assertEqual(report["outcome"], "package-mismatch")

    def test_hook_only_drift_is_caught(self):
        """Not only Markdown: a changed hook script changes the digest."""
        write(self.repo / "hooks" / "guard.py", "# 0.8.2 hook\n")
        write(self.cache / "hooks" / "guard.py", "# 0.8.0 hook\n")
        path = ledger.start(self.flow, self.dir, package=self.repo)[1]
        self.assertFalse(ledger.check(path, loaded=self.cache)["ok"])

    def test_unrecorded_package_cannot_vouch(self):
        path = ledger.start(self.flow, self.dir)[1]
        report = ledger.check(path, loaded=self.cache)
        self.assertIsNone(report["package"]["recorded"])
        self.assertFalse(report["ok"])

    def test_no_loaded_copy_leaves_provenance_unassessed(self):
        path = ledger.start(self.flow, self.dir, package=self.repo)[1]
        report = ledger.check(path)
        self.assertIsNone(report["package_consistent"])
        self.assertTrue(report["ok"])

    def test_flow_that_differs_from_package_is_refused(self):
        other = write(Path(self.tmp.name) / "elsewhere" / "flows" / "implement.md",
                      self.flow.read_text(encoding="utf-8") + "\nedited\n")
        with self.assertRaises(ledger.LedgerError):
            ledger.start(other, self.dir, package=self.repo)

    def test_flow_missing_from_package_is_refused(self):
        stray = write(Path(self.tmp.name) / "stray.md", "```logic\nmain:\n  return x as x\n```\n")
        with self.assertRaises(ledger.LedgerError):
            ledger.start(stray, self.dir, package=self.repo)

    def test_cli_round_trip(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger.main(["start", str(self.flow), "--package", str(self.repo),
                                "--dir", str(self.dir)])
        self.assertEqual(code, 0)
        run = out.getvalue().strip()
        write(self.cache / "SKILL.md", "stale\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger.main(["check", run, "--loaded", str(self.cache),
                                "--dir", str(self.dir)])
        self.assertEqual(code, 1)
        self.assertIn("package mismatch", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ledger.main(["check", run, "--loaded", str(self.cache), "--json",
                         "--dir", str(self.dir)])
        self.assertFalse(json.loads(out.getvalue())["package_consistent"])


# --- Finding 7: a skipped fragment is incomplete, not vacuously valid ---------------

class TestSkippedFragment(unittest.TestCase):
    def test_required_entry_milestone_exposes_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            stack = ROOT / "tests/fixtures/fragments/skill/flows/build-fixed.md"
            path = ledger.start(stack, Path(tmp), required=["exec stack profiles"])[1]
            ledger.note_step(path, "generate implementation from design")
            report = ledger.check(path)
            # No rule was violated, but the fragment was never entered.
            self.assertTrue(report["valid"])
            self.assertEqual(report["completeness"], "incomplete")
            self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
