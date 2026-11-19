"""Requirement inventory and the `compile` pipeline, driven by a scripted adapter."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skillwren import inventory as inv
from skillwren.nlcompile import CompileError, compile_skill, main as compile_main
from skillwren.review import read_originals, validate_review

FIXTURE = ROOT / "tests" / "fixtures" / "compile"
SOURCE = FIXTURE / "source" / "SKILL.md"
STUB = FIXTURE / "stub_adapter.py"

INVENTORY = {
    "requirements": [
        {"id": "R1", "kind": "order", "evidence": "exec",
         "text": "verify debug is off before writing the config",
         "source": [{"file": "SKILL.md", "lines": [5, 5]}]},
        {"id": "R2", "kind": "gate", "evidence": "exec",
         "text": "run the config check and verify debug is off",
         "source": [{"file": "SKILL.md", "lines": [5, 5]}]},
        {"id": "R3", "kind": "recovery", "text": "a failed check stops with the reason",
         "source": [{"file": "SKILL.md", "lines": [6, 6]}]},
        {"id": "R4", "kind": "invariant", "text": "never write an unverified config",
         "source": [{"file": "SKILL.md", "lines": [7, 7]}]},
        {"id": "R5", "kind": "effect", "evidence": "effect",
         "text": "deploy the production config",
         "source": [{"file": "SKILL.md", "lines": [3, 3]}]},
    ],
    "non_requirements": [{"file": "SKILL.md", "lines": [1, 1], "reason": "title"}],
}

GOOD_SKILL = """---
name: config-deploy
description: Deploy the production config after a debug-off check.
---

# Config deploy

```contract
never:
  write an unverified config
order:
  verify#check before write#config
```

```logic
deploy:
  exec config check from checks as result
  verify #check candidate has debug off from result
    otherwise:
      abort with "Unverified config."
  write #config candidate with target
  return candidate as candidate
```
"""

LANDS = {"R1": ["verify#check before write#config"],
         "R2": ["verify #check candidate has debug off from result"],
         "R3": ['abort with "Unverified config."'],
         "R4": ["write an unverified config"],
         "R5": ["write #config candidate with target"]}

# Unbacked verify (the measured silent-loss class) and a bare return.
BAD_SKILL = GOOD_SKILL.replace("candidate has debug off from result",
                               "candidate has debug off").replace(
    "return candidate as candidate", "return")
BAD_LANDS = dict(LANDS, R2=["verify #check candidate has debug off"])

JUDGE_CLEAN = {"dropped": [], "added": [], "changed": []}


def stamped():
    return inv.stamp(copy.deepcopy(INVENTORY), read_originals(SOURCE))


class InventoryCoverageTests(unittest.TestCase):
    def test_complete_inventory_has_no_findings(self):
        self.assertEqual(inv.check_coverage(stamped(), read_originals(SOURCE)), [])

    def test_unaccounted_lines_are_named(self):
        body = stamped()
        body["requirements"] = [r for r in body["requirements"] if r["id"] != "R3"]
        findings = inv.check_coverage(body, read_originals(SOURCE))
        self.assertEqual([f["rule"] for f in findings], ["I3"])
        self.assertIn("6", findings[0]["message"])

    def test_changed_source_is_rejected(self):
        body = stamped()
        body["sources"]["SKILL.md"] = "0" * 64
        with self.assertRaises(inv.InventoryError):
            inv.check_coverage(body, read_originals(SOURCE))

    def test_bad_kind_and_span_and_duplicate_ids_are_rejected(self):
        for mutate in (lambda b: b["requirements"][0].update(kind="vibe"),
                       lambda b: b["requirements"][0].update(
                           source=[{"file": "SKILL.md", "lines": [5, 99]}]),
                       lambda b: b["requirements"][1].update(id="R1"),
                       lambda b: b["non_requirements"][0].update(reason=" ")):
            body = stamped()
            mutate(body)
            with self.assertRaises(inv.InventoryError):
                inv.check_coverage(body, read_originals(SOURCE))

    def test_unrepresentable_is_a_warning_not_a_drop(self):
        body = stamped()
        body["requirements"][2]["kind"] = "unrepresentable"
        findings = inv.check_coverage(body, read_originals(SOURCE))
        self.assertEqual([(f["rule"], f["severity"]) for f in findings], [("I8", "warning")])


class LandingTests(unittest.TestCase):
    def landed(self, text, lands):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "SKILL.md"
        path.write_text(text, encoding="utf-8")
        body = stamped()
        for item in body["requirements"]:
            if item["id"] in lands:
                item["lands"] = lands[item["id"]]
        return inv.check_landing(body, inv.Candidate(path)), body, path

    def test_good_candidate_lands_every_requirement(self):
        findings, _, _ = self.landed(GOOD_SKILL, LANDS)
        self.assertEqual(findings, [])

    def test_missing_landing_and_missing_anchor(self):
        lands = dict(LANDS, R2=["verify that the moon is full"])
        del lands["R3"]
        findings, _, _ = self.landed(GOOD_SKILL, lands)
        self.assertEqual(sorted((f["rule"], f["id"]) for f in findings),
                         [("I4", "R3"), ("I5", "R2")])

    def test_order_requirement_must_be_an_order_rule(self):
        findings, _, _ = self.landed(GOOD_SKILL, dict(
            LANDS, R1=["verify #check candidate has debug off from result"]))
        self.assertEqual([(f["rule"], f["id"]) for f in findings], [("I6", "R1")])

    def test_gate_landing_in_prose_is_not_a_statement(self):
        findings, _, _ = self.landed(GOOD_SKILL, dict(LANDS, R2=["# Config deploy"]))
        rules = sorted(f["rule"] for f in findings if f["id"] == "R2")
        self.assertEqual(rules, ["I6", "I7"])

    def test_unbacked_verify_loses_demanded_evidence(self):
        text = GOOD_SKILL.replace("candidate has debug off from result",
                                  "candidate has debug off")
        findings, _, _ = self.landed(text, BAD_LANDS)
        self.assertEqual([(f["rule"], f["id"]) for f in findings], [("I7", "R2")])

    def test_landed_inventory_becomes_a_valid_review_map(self):
        findings, body, path = self.landed(GOOD_SKILL, LANDS)
        self.assertEqual(findings, [])
        originals = read_originals(SOURCE)
        raw = path.read_bytes()
        review = inv.to_review(body, originals, raw)
        result = validate_review(originals, raw, raw, review)
        self.assertFalse(result["semantic_equivalence_proven"])
        self.assertEqual(result["non_requirements"], 1)

    def test_review_rejects_unexplained_non_requirement(self):
        _, body, path = self.landed(GOOD_SKILL, LANDS)
        originals = read_originals(SOURCE)
        raw = path.read_bytes()
        review = inv.to_review(body, originals, raw)
        review["non_requirements"][0]["reason"] = ""
        with self.assertRaises(ValueError):
            validate_review(originals, raw, raw, review)


class CompileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.state = self.dir / "state.json"

    def adapter(self, script):
        path = self.dir / "script.json"
        path.write_text(json.dumps(script), encoding="utf-8")
        return [sys.executable, str(STUB), str(path), str(self.state)]

    def requests(self, phase):
        state = json.loads(self.state.read_text(encoding="utf-8"))
        return [r for r in state["requests"] if r["phase"] == phase]

    def script(self, **overrides):
        script = {"inventory": [{"inventory": INVENTORY}],
                  "lower": [{"files": {"SKILL.md": GOOD_SKILL}, "lands": LANDS}],
                  "repair": [{"files": {"SKILL.md": GOOD_SKILL}, "lands": LANDS}],
                  "judge": [JUDGE_CLEAN]}
        script.update(overrides)
        return script

    def test_clean_compile_publishes_skill_and_audit(self):
        out = self.dir / "out"
        manifest = compile_skill(SOURCE, out, self.adapter(self.script()))
        self.assertEqual((out / "SKILL.md").read_text(encoding="utf-8"), GOOD_SKILL)
        for name in ("inventory.json", "review.json", "compile-manifest.json",
                     "SKILL.md.explain.txt"):
            self.assertTrue((out / "audit" / name).is_file(), name)
        self.assertFalse(manifest["semantic_equivalence_proven"])
        self.assertFalse(manifest["approved"])
        self.assertEqual(manifest["requirements"], 5)
        self.assertEqual([c["phase"] for c in manifest["calls"]],
                         ["inventory", "lower", "judge"])
        # The judge saw the deterministic explanation, not the source text.
        judge = self.requests("judge")[0]
        self.assertIn("SKILL.md", judge["explanations"])
        self.assertNotIn("sources", judge)

    def test_check_and_landing_findings_drive_a_repair(self):
        out = self.dir / "out"
        script = self.script(lower=[{"files": {"SKILL.md": BAD_SKILL}, "lands": BAD_LANDS}])
        manifest = compile_skill(SOURCE, out, self.adapter(script))
        repair = self.requests("repair")[0]
        rules = {e["rule"] for e in repair["diagnostics"]["SKILL.md"]["errors"]}
        self.assertTrue(rules, "bare return must produce a check error")
        self.assertIn("I7", {f["rule"] for f in repair["findings"]})
        self.assertTrue(repair["unbacked_verifies"])
        self.assertEqual([c["phase"] for c in manifest["calls"]],
                         ["inventory", "lower", "repair", "judge"])

    def test_inventory_gap_is_sent_back_before_lowering(self):
        partial = copy.deepcopy(INVENTORY)
        partial["requirements"] = partial["requirements"][:-1]
        script = self.script(inventory=[{"inventory": partial}, {"inventory": INVENTORY}])
        compile_skill(SOURCE, self.dir / "out", self.adapter(script))
        second = self.requests("inventory")[1]
        self.assertEqual([f["rule"] for f in second["findings"]], ["I3"])

    def test_persistent_failure_publishes_nothing_and_keeps_attempt(self):
        out, kept = self.dir / "out", self.dir / "kept"
        script = self.script(lower=[{"files": {"SKILL.md": BAD_SKILL}, "lands": BAD_LANDS}],
                             repair=[{"files": {"SKILL.md": BAD_SKILL}, "lands": BAD_LANDS}])
        with self.assertRaises(CompileError) as caught:
            compile_skill(SOURCE, out, self.adapter(script), rounds=2, keep_failed=kept)
        self.assertIn("still invalid", str(caught.exception))
        self.assertFalse(out.exists())
        self.assertTrue((kept / "SKILL.md").is_file())
        self.assertEqual(len(self.requests("repair")), 2)

    def test_judge_drop_gets_one_repair_and_is_reported(self):
        drop = {"dropped": ["R3 recovery"], "added": [], "changed": []}
        script = self.script(judge=[drop])
        manifest = compile_skill(SOURCE, self.dir / "out", self.adapter(script))
        self.assertEqual(self.requests("repair")[0]["findings"][0]["rule"], "J1")
        # The repaired candidate is judged again; a persistent drop is reported,
        # not repaired forever.
        self.assertEqual([c["phase"] for c in manifest["calls"]],
                         ["inventory", "lower", "judge", "repair", "judge"])
        self.assertEqual(manifest["judge"]["dropped"], ["R3 recovery"])

    def test_judge_verdict_reported_is_for_the_published_candidate(self):
        drop = {"dropped": ["R3 recovery"], "added": [], "changed": []}
        script = self.script(judge=[drop, JUDGE_CLEAN])
        manifest = compile_skill(SOURCE, self.dir / "out", self.adapter(script))
        self.assertEqual(manifest["judge"], JUDGE_CLEAN)

    def test_unsafe_adapter_paths_are_refused(self):
        for name in ("../escape.md", "/abs.md", "audit/x.md", "C:evil.md"):
            script = self.script(lower=[{"files": {"SKILL.md": GOOD_SKILL, name: "x"},
                                         "lands": LANDS}])
            with self.assertRaises(CompileError):
                compile_skill(SOURCE, self.dir / f"out-{len(name)}", self.adapter(script))

    def test_existing_output_is_never_overwritten(self):
        out = self.dir / "out"
        out.mkdir()
        with self.assertRaises(CompileError):
            compile_skill(SOURCE, out, self.adapter(self.script()))

    def test_cli_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()),                 contextlib.redirect_stderr(io.StringIO()):
            self._cli_exit_codes()

    def _cli_exit_codes(self):
        adapter = self.adapter(self.script())
        code = compile_main([str(SOURCE), "--out", str(self.dir / "a"), "--"] + adapter)
        self.assertEqual(code, 0)
        self.state.unlink()
        adapter = self.adapter(self.script(judge=[
            dict(JUDGE_CLEAN, changed=["abort message wording"])]))
        code = compile_main([str(SOURCE), "--out", str(self.dir / "b"), "--"] + adapter)
        self.assertEqual(code, 1)
        script = self.script(inventory=[{"inventory": {"requirements": []}}])
        code = compile_main([str(SOURCE), "--out", str(self.dir / "c"), "--rounds", "0",
                             "--"] + self.adapter(script))
        self.assertEqual(code, 2)


class FrozenBenchmarkTests(unittest.TestCase):
    CORPUS = ROOT / "docs/current/research/nl-compiler/full-stack-0.2"

    def test_manifest_digests_match_the_frozen_bytes(self):
        import hashlib
        import re
        text = (self.CORPUS / "FROZEN.md").read_text(encoding="utf-8")
        pinned = re.findall(r"^([0-9a-f]{64})  (\S+)$", text, re.M)
        self.assertEqual(len(pinned), 9)
        for expected, name in pinned:
            actual = hashlib.sha256((self.CORPUS / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_published_runs_still_validate_against_their_inventories(self):
        source = self.CORPUS / "source"
        contexts = sorted((source / "references").glob("*.md"))
        originals = read_originals(source / "SKILL.md", contexts)
        for run in ("run1", "run2"):
            inventory = json.loads((self.CORPUS / "runs" / run / "audit/inventory.json")
                                   .read_text(encoding="utf-8"))
            # Reordered contexts change nothing but the digest-map order.
            inventory["sources"] = {k: inventory["sources"][k] for k in originals}
            findings = inv.check(inventory, originals, self.CORPUS / "runs" / run / "SKILL.md")
            self.assertFalse([f for f in findings if f["severity"] == "error"], run)


class CheckJsonTests(unittest.TestCase):
    def test_check_json_reports_errors_and_unbacked_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SKILL.md"
            path.write_text(BAD_SKILL, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "skillwren", "check", "--json", "--fragment", str(path)],
                capture_output=True, text=True,
                env=dict(os.environ, PYTHONPATH=str(ROOT / "src")))
        self.assertEqual(proc.returncode, 1, proc.stderr)
        report = json.loads(proc.stdout)
        entry = report["files"][str(path)]
        self.assertFalse(report["ok"])
        self.assertTrue(entry["errors"])
        self.assertEqual(entry["unbacked_verifies"][0]["flow"], "deploy")


if __name__ == "__main__":
    unittest.main()
