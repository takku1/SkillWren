"""Format 0.6: fragment layout, cross-file runs, inputs, and order rules."""
import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import skillwren
from skillwren import validator

FLOWS = ROOT / "tests" / "fixtures" / "fragments" / "skill" / "flows"
FIX = ROOT / "tests" / "fixtures"


def frag(name):
    return skillwren.validate_fragment(str(FLOWS / name))


def rules(diags):
    return sorted(d.rule for d in diags)


class TestFragmentLayout(unittest.TestCase):
    def test_flow_file_with_prose_and_foreign_fence_is_clean(self):
        self.assertEqual(frag("design.md"), ([], []))

    def test_same_file_is_rejected_in_skill_layout(self):
        errors, _ = skillwren.validate_file(str(FLOWS / "design.md"))
        self.assertIn("F1", rules(errors))
        self.assertIn("F2", rules(errors))

    def test_host_only_frontmatter_is_accepted(self):
        errors, _ = skillwren.validate_fragment(str(FLOWS.parent / "SKILL.md"))
        self.assertEqual(errors, [])

    def test_prose_only_fragment_warns_nothing_checked(self):
        self.assertEqual(rules(frag("prose-only.md")[1]), ["W14"])

    def test_presence_tests_declare_inputs(self):
        flows = validator.summarize(str(FLOWS / "build-fixed.md"))
        self.assertEqual(flows["build"]["inputs"], ["design", "request"])
        self.assertEqual(flows["build"]["writes"], ["design_docs", "subject"])

    def test_declared_inputs_make_unbound_names_errors(self):
        errors, _ = frag("declared-inputs.md")
        self.assertEqual(rules(errors), ["U1"])
        self.assertIn("'design' is not bound", errors[0].msg)

    def test_correlated_branches_are_not_assumed(self):
        errors, _ = frag("integration-gap.md")
        self.assertEqual(rules(errors), ["U1"])
        self.assertIn("integration", errors[0].msg)


class TestCrossFileRuns(unittest.TestCase):
    def test_unresolvable_targets_are_r3(self):
        errors, _ = frag("bad-runs.md")
        self.assertEqual(rules(errors), ["R3", "R3"])
        self.assertIn("cannot resolve", errors[0].msg)
        self.assertIn("no logic block", errors[1].msg)

    def test_callee_returns_bind_in_caller(self):
        errors, warnings = frag("build-via-run.md")
        self.assertEqual(errors, [])
        self.assertEqual(rules(warnings), ["W15"])  # the callee's screen is a self-report

    def test_mutating_callee_before_ask_is_m1(self):
        self.assertEqual(rules(frag("ask-after-run.md")[0]), ["M1"])


class TestOrderRules(unittest.TestCase):
    def test_skipped_design_path_violates_order(self):
        """Field report 3, G1: a supplied design skips the screen."""
        errors, _ = frag("build-gap.md")
        self.assertEqual(rules(errors), ["P1"])
        self.assertIn("write implementation", errors[0].msg)

    def test_gate_on_every_path_satisfies_order(self):
        self.assertEqual(frag("build-fixed.md"), ([], []))

    def test_callee_guarantee_satisfies_order(self):
        self.assertEqual(frag("build-via-run.md")[0], [])

    def test_failed_gate_establishes_nothing(self):
        errors, warnings = frag("failed-gate.md")
        self.assertEqual(rules(errors), ["P1"])
        self.assertIn("W9", rules(warnings))

    def test_rule_that_never_applies_warns(self):
        errors, warnings = frag("never-applies.md")
        self.assertEqual(errors, [])
        self.assertEqual(rules(warnings), ["W13", "W15"])

    def test_order_rules_in_skill_layout(self):
        self.assertEqual(skillwren.validate_file(str(FIX / "valid-order.md")), ([], []))
        errors, _ = skillwren.validate_file(str(FIX / "invalid-order.md"))
        self.assertEqual(rules(errors), ["P1"])

    def test_malformed_order_entry_is_f2(self):
        errors, _ = skillwren.validate_file(str(FIX / "invalid-order-entry.md"))
        self.assertEqual(rules(errors), ["F2"])

    def test_self_report_anchor_warns_w15(self):
        """Game-theory review: a rule anchored only on the model's judgment is cheap talk."""
        errors, warnings = skillwren.validate_file(str(FIX / "valid-order-self-anchor.md"))
        self.assertEqual(errors, [])
        self.assertIn("W15", rules(warnings))
        errors, warnings = frag("build-gap.md")
        self.assertIn("W15", rules(warnings))

    def test_evidence_anchor_is_quiet(self):
        self.assertNotIn("W15", rules(frag("build-fixed.md")[1]))

    def test_inputs_section_is_fragment_only(self):
        errors, _ = skillwren.validate_file(str(FIX / "invalid-inputs-in-skill.md"))
        self.assertEqual(rules(errors), ["F2"])


class TestAudit(unittest.TestCase):
    def test_gate_classes_and_branch_controllers(self):
        report = validator.audit(str(FLOWS / "build-fixed.md"))
        gates = {text: label for _, text, label in report["flows"]["build"]["gates"]}
        self.assertEqual(gates["verify design has an assurance table from screen"], "evidence")
        self.assertEqual(gates["require request exists"], "self")
        branches = [label for _, _, label in report["flows"]["build"]["branches"]]
        self.assertEqual(branches, ["model"])
        (rule, classes), = report["rules"]
        self.assertEqual(classes, ["evidence"])

    def test_user_decisions_and_user_controlled_branches(self):
        report = validator.audit(str(FLOWS / "ask-after-run.md"))
        gates = [label for _, _, label in report["flows"]["build"]["gates"]]
        self.assertEqual(gates, ["user"])
        report = validator.audit(str(FIX / "valid-order.md"), fragment=False)
        self.assertIn("evidence", [label for _, _, label in report["flows"]["main"]["gates"]])


class TestTemplates(unittest.TestCase):
    def test_fragment_template_is_clean_inside_a_skill(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory)
            (skill / "flows").mkdir()
            (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo.\n---\n")
            shutil.copy(FLOWS / "design.md", skill / "flows" / "design.md")
            shutil.copy(ROOT / "docs" / "current" / "fragment-template.md",
                        skill / "flows" / "build.md")
            self.assertEqual(skillwren.validate_fragment(str(skill / "flows" / "build.md")),
                             ([], []))


class TestCheckCli(unittest.TestCase):
    def run_cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = validator.main(["skillwren", "check", *args])
        return code, out.getvalue()

    def test_fragment_flag_and_summary(self):
        code, out = self.run_cli("--fragment", "--summary", str(FLOWS / "build-fixed.md"))
        self.assertEqual(code, 0)
        self.assertIn("flow build: inputs design, request; writes design_docs, subject;"
                      " runs design from flows/design.md", out)

    def test_flags_in_any_position(self):
        code, out = self.run_cli(str(FLOWS / "build-gap.md"), "--explain", "--fragment")
        self.assertEqual(code, 1)
        self.assertIn("error P1", out)
        self.assertIn("SPEC Section 20", out)

    def test_audit_flag(self):
        code, out = self.run_cli("--fragment", "--audit", str(FLOWS / "build-fixed.md"))
        self.assertEqual(code, 0)
        self.assertIn("gate [evidence] verify design has an assurance table from screen", out)
        self.assertIn("rests on evidence", out)

    def test_unknown_flag_is_usage_error(self):
        code, _ = self.run_cli("--frag", str(FLOWS / "design.md"))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
