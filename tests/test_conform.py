"""Offline runtime-checker regressions: real workspaces, simulated model calls."""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from skillwren import conform

SKILL = ROOT / "tests/fixtures/conform/notes-skill/SKILL.md"
REAL_RUN = subprocess.run


class TestSession(unittest.TestCase):
    def run_case(self, mutate=lambda work: None, result=None, returncode=0,
                 workspace=None, events=(), claude=None, seen=None):
        args = argparse.Namespace(workspace=workspace, auth_from_profile=False,
                                  prompt="add a note", model="offline", budget_usd=0.1,
                                  timeout=10, claude=claude)
        if result is None:
            result = {"type": "result", "subtype": "success", "is_error": False}

        def fake_run(command, **kwargs):
            if Path(command[0]).stem != "claude":
                return REAL_RUN(command, **kwargs)
            if seen is not None:
                seen.append(command)
            mutate(Path(kwargs["cwd"]))
            return subprocess.CompletedProcess(command, returncode,
                                               "\n".join(json.dumps(e) for e in [*events, result]), "")

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "offline-test"}), \
                patch.object(conform.subprocess, "run", side_effect=fake_run):
            return conform.run_session(SKILL, args)

    def test_failed_process_is_not_conformance_evidence(self):
        with self.assertRaisesRegex(ValueError, "failed"):
            self.run_case(returncode=1)

    def test_error_result_is_not_conformance_evidence(self):
        with self.assertRaisesRegex(ValueError, "failed"):
            self.run_case(result={"type": "result", "subtype": "error_max_budget_usd"})

    def test_missing_result_is_not_conformance_evidence(self):
        with self.assertRaisesRegex(ValueError, "result"):
            self.run_case(result={"type": "system"})

    def test_non_object_stream_event_does_not_crash(self):
        with self.assertRaisesRegex(ValueError, "result"):
            self.run_case(result=["unexpected"])

    def test_ignored_file_is_observed(self):
        report = self.run_case(lambda work: (work / "secret.pyc").write_bytes(b"data"))
        self.assertIn("secret.pyc", report["undeclared"])

    def test_unicode_and_space_filename_is_exact(self):
        name = "caf\u00e9 notes.txt"
        report = self.run_case(lambda work: (work / name).write_bytes(b"data"))
        self.assertIn(name, report["changed"])

    def test_installed_skill_edits_are_observed(self):
        name = ".claude/skills/notes-skill/SKILL.md"
        report = self.run_case(lambda work: (work / name).write_text("tampered"))
        self.assertIn(name, report["undeclared"])

    def test_committed_changes_are_observed(self):
        def mutate(work):
            (work / "unexpected.txt").write_text("data")
            conform.git(work, "add", "-A")
            conform.git(work, "commit", "-qm", "hide from status")
        self.assertIn("unexpected.txt", self.run_case(mutate)["undeclared"])

    def test_permitted_change_is_clean(self):
        report = self.run_case(lambda work: (work / "notes.txt").write_text("note"))
        self.assertEqual(report["changed"], ["notes.txt"])
        self.assertEqual(report["undeclared"], [])

    def test_dismissal_with_permitted_write_still_fails(self):
        events = [{"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "AskUserQuestion"}]}}]
        report = self.run_case(lambda work: (work / "notes.txt").write_text("note"),
                               events=events)
        self.assertTrue(report["dismissal_violation"])

    def test_workspace_ignore_and_git_pointer_are_not_overwritten_or_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / ".gitignore").write_text("private/\n")
            (source / ".git").write_text("gitdir: /does-not-exist\n")
            (source / "private").mkdir()
            (source / "private/old.txt").write_text("before")
            def mutate(work):
                self.assertEqual((work / ".gitignore").read_text(), "private/\n")
                self.assertTrue((work / ".git").is_dir())
                (work / "private/old.txt").unlink()
                (work / "private/new.txt").write_text("after")
            report = self.run_case(mutate, workspace=source)
            self.assertEqual(report["changed"], ["private/new.txt", "private/old.txt"])
            self.assertEqual((source / "private/old.txt").read_text(), "before")


    def test_commands_are_reported_and_undeclared_ones_flagged(self):
        def bash(command):
            return {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": command}}]}}
        report = self.run_case(events=[bash("git status --short"), bash("py -3 build.py")])
        self.assertEqual(report["commands"], ["git status --short", "py -3 build.py"])
        self.assertEqual(report["undeclared_commands"], ["py -3 build.py"])

    def test_resolved_launcher_path_is_used(self):
        seen = []
        self.run_case(claude="C:/tools/npm/claude.cmd", seen=seen)
        self.assertEqual(seen[0][0], "C:/tools/npm/claude.cmd")

    def test_windows_interpreters_are_allowed(self):
        for tool in ("Bash(python:*)", "Bash(python3:*)", "Bash(py:*)"):
            self.assertIn(tool, conform.TOOLS)


class TestCli(unittest.TestCase):
    argv = [str(SKILL), "--prompt", "x", "--model", "offline", "--budget-usd", "0.1"]

    def test_json_is_one_document(self):
        report = dict(skill="notes-skill", changed=[], cost_usd=0, undeclared=[],
                      effects_without_glob=[], dismissal_violation=False)
        output = io.StringIO()
        with patch.object(conform.shutil, "which", return_value="claude"), \
                patch.object(conform, "run_session", return_value=report), \
                contextlib.redirect_stdout(output):
            self.assertEqual(conform.main(self.argv + ["--json"]), 0)
        self.assertTrue(json.loads(output.getvalue())["conforms"])

    def test_environment_failure_returns_two(self):
        with patch.object(conform.shutil, "which", return_value="claude"), \
                patch.object(conform, "run_session", side_effect=OSError("offline failure")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(conform.main(self.argv), 2)

    def test_record_keeps_successes_and_errors(self):
        report = dict(skill="notes-skill", changed=["x"], cost_usd=0, undeclared=["x"],
                      effects_without_glob=[], dismissal_violation=False)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(conform.shutil, "which", return_value="claude"), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(conform, "run_session", return_value=report):
                self.assertEqual(conform.main(self.argv + ["--record", directory]), 1)
            with patch.object(conform, "run_session", side_effect=ValueError("no result")):
                self.assertEqual(conform.main(self.argv + ["--record", directory]), 2)
            lines = (Path(directory) / conform.RECORD_FILE).read_text(encoding="utf-8").splitlines()
        entries = [json.loads(line) for line in lines]
        self.assertEqual([e["outcome"] for e in entries], ["violations", "error"])
        self.assertEqual(entries[1]["error"], "no result")
        self.assertEqual(len(entries[0]["skill_sha256"]), 64)

    def test_invalid_limits_do_not_start_session(self):
        with patch.object(conform, "run_session") as run:
            for option, value in [("--budget-usd", "nan"), ("--budget-usd", "inf"),
                                  ("--budget-usd", "0"), ("--timeout", "0")]:
                with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        conform.main(self.argv + [option, value])
                    self.assertEqual(error.exception.code, 2)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
