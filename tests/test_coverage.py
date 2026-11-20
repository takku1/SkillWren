"""Enforcement coverage: each rule, gate and write is enforced, recorded, instructed or
unverifiable, and a guarantee is never claimed without the guard's own conditions."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skillwren.coverage import analyze, requirement_tiers  # noqa: E402
from skillwren.guard import Controller, file_digest  # noqa: E402
from skillwren.validator.approval import approve  # noqa: E402

FLOW = ROOT / "examples/host-demo/dep-audit/flow.md"
VERIFIER = ROOT / "docs/current/research/lifecycle/a-manual/tools/verify_report.py"


def tiers(rows):
    return {(r["kind"], r["line"]): r["tier"] for r in rows}


def by_text(rows, start):
    return next(r for r in rows if r["text"].startswith(start))


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.flow = self.root / "flow.md"
        shutil.copy2(FLOW, self.flow)
        self.approvals = self.root / "approvals"
        approve(self.flow, True, "host-admin", None, self.approvals)
        verifier = self.root / "verify.py"
        shutil.copy2(VERIFIER, verifier)
        pins = {PYTHON: file_digest(PYTHON), str(verifier): file_digest(verifier)}
        argv = [PYTHON, "-I", str(verifier)]
        self.policy = {"version": 1, "workflow": {
            "flow": str(self.flow), "flow_sha256": file_digest(self.flow), "approvals": str(self.approvals)},
            "operations": {
                "verify#deps": {"argv": argv, "pins": dict(pins), "timeout": 5},
                "write#report": {"target": str(self.root / "REPORT.md"), "argv": argv,
                                 "pins": dict(pins), "timeout": 5}}}
        Controller(self.policy)  # the policy is one the guard itself accepts

    def test_without_a_policy_nothing_is_enforced(self):
        rows = analyze(self.flow)
        self.assertNotIn("enforced", {r["tier"] for r in rows})
        self.assertEqual(by_text(rows, "verify#deps before")["tier"], "recorded")
        self.assertEqual(by_text(rows, "write #report")["tier"], "instructed")

    def test_bound_policy_enforces_the_rule_its_prerequisite_and_the_write(self):
        rows = analyze(self.flow, policy=self.policy)
        self.assertEqual(by_text(rows, "verify#deps before")["tier"], "enforced")
        self.assertEqual(by_text(rows, "verify #deps")["tier"], "enforced")
        self.assertIn("prerequisite", by_text(rows, "verify #deps")["why"])
        self.assertEqual(by_text(rows, "write #report")["tier"], "enforced")
        # The command that produces the evidence is not itself a guard operation.
        self.assertEqual(by_text(rows, "exec dependency check")["tier"], "recorded")

    def test_policy_for_another_flow_does_not_enforce_rules(self):
        other = dict(self.policy, workflow=dict(self.policy["workflow"], flow=str(self.root / "other.md")))
        rows = analyze(self.flow, policy=other)
        rule = by_text(rows, "verify#deps before")
        self.assertEqual(rule["tier"], "recorded")
        self.assertIn("not bound", rule["why"])

    def test_policy_for_another_flow_does_not_enforce_writes(self):
        # 0.13.1 (external review): a policy bound to another flow that happens to name the
        # same operation protects some other target, not this skill's write.
        other = dict(self.policy, workflow=dict(self.policy["workflow"], flow=str(self.root / "other.md")))
        rows = analyze(self.flow, policy=other)
        write = by_text(rows, "write #report")
        self.assertEqual(write["tier"], "instructed")
        self.assertIn("not bound", write["why"])
        self.assertNotIn("enforced", {r["tier"] for r in rows})

    def test_enforced_rows_state_the_isolation_assumption(self):
        rows = analyze(self.flow, policy=self.policy)
        enforced = [r for r in rows if r["tier"] == "enforced"]
        self.assertTrue(enforced)
        self.assertTrue(all("only through the guard" in r["assumes"] for r in enforced))
        self.assertFalse(any("assumes" in r for r in rows if r["tier"] != "enforced"))

    def test_rule_missing_an_operation_is_not_enforced(self):
        policy = dict(self.policy, operations={"write#report": self.policy["operations"]["write#report"]})
        rows = analyze(self.flow, policy=policy)
        self.assertEqual(by_text(rows, "verify#deps before")["tier"], "recorded")
        self.assertEqual(by_text(rows, "write #report")["tier"], "enforced")

    def write_flow(self, contract_order, body):
        path = self.root / "x.md"
        path.write_text("```contract\ninputs:\n  request\norder:\n" + contract_order
                        + "```\n\n```logic\nx:\n" + body + "```\n", encoding="utf-8")
        return path

    def test_self_report_rule_is_instructed_and_unmatched_rule_unverifiable(self):
        path = self.write_flow(
            "  generate plan before write result\n  verify nothing before write result\n",
            "  generate plan from request as plan\n  write plan with result\n  return plan as plan\n")
        rows = analyze(path)
        self.assertEqual(by_text(rows, "generate plan before")["tier"], "instructed")
        self.assertEqual(by_text(rows, "verify nothing before")["tier"], "unverifiable")

    def test_exclusion_rule_is_classified(self):
        path = self.write_flow(
            "  never exec deploy before ask user to approve\n",
            "  ask user to approve the plan\n  require user approves the plan\n"
            "  exec deploy from tools as done\n  return done as done\n")
        rows = analyze(path)
        rule = by_text(rows, "never exec deploy")
        self.assertEqual(rule["kind"], "exclusion rule")
        self.assertEqual(rule["tier"], "recorded")
        self.assertEqual(by_text(rows, "require user approves")["tier"], "recorded")

    def test_requirements_take_the_tier_of_the_element_that_preserves_them(self):
        rows = analyze(self.flow, policy=self.policy)
        text = self.flow.read_text(encoding="utf-8")
        prose = next(line.strip() for line in text.splitlines()
                     if line.strip() and not line.startswith(("```", " ", "#", "|", "-")))
        score = {"requirements": [
            {"id": "R-1", "kind": "ordering", "verdict": "preserved", "quote": "verify#deps before write#report"},
            {"id": "R-2", "kind": "obligation", "verdict": "preserved", "quote": prose[:60]},
            {"id": "R-3", "kind": "prohibition", "verdict": "missing", "quote": ""},
        ]}
        got = {r["id"]: r for r in requirement_tiers(self.flow, rows, score)}
        self.assertEqual(got["R-1"]["tier"], "enforced")
        self.assertEqual(got["R-2"]["tier"], "instructed")
        self.assertIsNone(got["R-3"]["tier"])

    def test_cli_json(self):
        import io
        from contextlib import redirect_stdout
        from skillwren.coverage import main
        policy = self.root / "policy.json"
        policy.write_text(json.dumps(self.policy), encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            main([str(self.flow), "--policy", str(policy), "--json"])
        counts = json.loads(out.getvalue())[str(self.flow)]["counts"]
        self.assertEqual(counts["enforced"], 3)


if __name__ == "__main__":
    unittest.main()
