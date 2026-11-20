"""The distributable skill: generated plugin in sync, shipped skill and its example check
clean, and the bundled checker runs outside the repository with no installation."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
SKILL = PLUGIN / "skillwren"


def run(*args, cwd=None):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    return subprocess.run([sys.executable, "-I", *map(str, args)], cwd=cwd, env=env,
                          capture_output=True, text=True)


class PluginTests(unittest.TestCase):
    def test_plugin_matches_its_sources(self):
        result = run(ROOT / "scripts" / "build_plugin.py", "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_versions_agree(self):
        version = re.search(r'^version = "([^"]+)"',
                            (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], version)
        self.assertEqual(market["plugins"][0]["version"], version)
        self.assertEqual(market["plugins"][0]["source"], "./plugin")
        self.assertTrue((PLUGIN / manifest["skills"][0] / "SKILL.md").is_file())

    def test_bundled_checker_runs_outside_the_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "installed"
            shutil.copytree(SKILL, copy)
            result = run(copy / "scripts" / "skillwren.py", "check", "--fragment", "SKILL.md", cwd=copy)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("clean", result.stdout)
            self.assertNotIn(str(ROOT), result.stdout + result.stderr)

    def test_shipped_skill_checks_clean_without_warnings(self):
        result = run(SKILL / "scripts" / "skillwren.py", "check", "--fragment", SKILL / "SKILL.md")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("warning", result.stdout)

    def test_language_card_example_checks_clean(self):
        text = (SKILL / "references" / "language.md").read_text(encoding="utf-8")
        example = re.search(r"````markdown\n(.*?)````", text, re.S).group(1)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(example, encoding="utf-8")
            result = run(SKILL / "scripts" / "skillwren.py", "check", "--fragment", path)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("warning", result.stdout)

    def test_every_model_repair_loop_has_a_blocked_exit(self):
        # 0.12.1: a repair that loops back (retry / return to) must also be able to stop and
        # report, so an unfixable draft cannot burn model calls forever. A loop driven by a
        # user answer (it asks) ends when the user stops.
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        logic = re.search(r"```logic\n(.*?)```", text, re.S).group(1).splitlines()
        loops = 0
        for i, line in enumerate(logic):
            if line.strip() != "otherwise:":
                continue
            indent = len(line) - len(line.lstrip())
            body = []
            for nxt in logic[i + 1:]:
                if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                body.append(nxt.strip())
            loops_back = any(b == "retry" or b.startswith("return to ") for b in body)
            if loops_back and not any(b.startswith("ask user") for b in body):
                loops += 1
                self.assertTrue(any(b.startswith("return #blocked") for b in body),
                                f"repair at logic line {i + 1} loops without a blocked exit")
        self.assertGreaterEqual(loops, 3)

    # 0.12.2: the repair budget is counted by the launcher, not the model (Haiku ran
    # about eight repair rounds under a model-counted budget of five).

    DRAFT = ("---\nname: x\ndescription: demo\n---\n\n```contract\ninputs:\n  request\n```\n\n"
             "```logic\nx:\n  exec make clean from tools as cleaned\n"
             "  ask user whether to rebuild as choice\n{extra}  return cleaned as result\n```\n")

    def draft(self, tmp, extra=""):
        folder = Path(tmp) / "x-draft"
        folder.mkdir(exist_ok=True)
        (folder / "SKILL.md").write_text(self.DRAFT.format(extra=extra), encoding="utf-8")
        return folder

    def check_draft(self, folder):
        return run(SKILL / "scripts" / "skillwren.py", "check", "--fragment", folder / "SKILL.md")

    def test_budget_stops_a_repair_that_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.draft(tmp)
            self.assertEqual(self.check_draft(folder).returncode, 1)
            with (folder / "SKILL.md").open("a", encoding="utf-8") as f:
                f.write("\nA note that fixes nothing.\n")
            result = self.check_draft(folder)
            self.assertEqual(result.returncode, 3, result.stdout)
            self.assertIn("same problems", result.stdout)

    def test_budget_stops_after_five_repairs(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = self.draft(tmp)
            codes = [self.check_draft(folder).returncode]
            for i in range(1, 6):  # each repair changes the result (a new undefined apply)
                extra = "".join(f"  apply step{k} with request as request\n" for k in range(i))
                self.draft(tmp, extra)
                codes.append(self.check_draft(folder).returncode)
            self.assertEqual(codes, [1, 1, 1, 1, 1, 3])

    def test_budget_never_stops_a_clean_draft_or_touches_other_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "y-draft"
            folder.mkdir()
            text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
            for i in range(7):
                (folder / "SKILL.md").write_text(text + f"\n<!-- {i} -->\n", encoding="utf-8")
                self.assertEqual(self.check_draft(folder).returncode, 0)
            other = Path(tmp) / "plain"
            other.mkdir()
            (other / "SKILL.md").write_text(self.DRAFT.format(extra=""), encoding="utf-8")
            run(SKILL / "scripts" / "skillwren.py", "check", "--fragment", other / "SKILL.md")
            self.assertFalse((other / ".skillwren").exists())

    def test_budget_state_is_not_packaged(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "y-draft"
            folder.mkdir()
            shutil.copy2(SKILL / "SKILL.md", folder / "SKILL.md")
            self.check_draft(folder)
            self.assertTrue((folder / ".skillwren" / "budget.json").is_file())
            out = Path(tmp) / "pkg"
            result = run(SKILL / "scripts" / "skillwren.py", "build", folder, "--out", out)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(any(".skillwren" in p.parts for p in out.rglob("*")))

    def test_skill_links_resolve_inside_the_plugin(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#]+)\)", text) + re.findall(r"`(references/[^`]+\.md)`", text):
            self.assertTrue((SKILL / target).is_file(), target)


if __name__ == "__main__":
    unittest.main()
