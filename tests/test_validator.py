"""Validator tests (TDD): fixtures first, implementation after."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import skillwren

FIX = ROOT / "tests" / "fixtures"


def validate_fixture(name):
    return skillwren.validate_file(str(FIX / name))


def rule_ids(diags):
    return {d.rule for d in diags}


class TestValidFiles(unittest.TestCase):
    def test_skeleton_fixture_is_clean(self):
        errors, warnings = validate_fixture("valid-skeleton.md")
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_golden_theme_factory_is_clean(self):
        errors, warnings = skillwren.validate_file(
            str(ROOT / "examples/theme-factory.golden.md"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_code_reviewer_is_clean(self):
        errors, warnings = skillwren.validate_file(
            str(ROOT / "examples/code-reviewer.md"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])


class TestErrors(unittest.TestCase):
    def test_requires_mismatch_is_error(self):
        errors, _ = validate_fixture("invalid-requires.md")
        self.assertIn("R1", rule_ids(errors))

    def test_unknown_verb_is_error(self):
        errors, _ = validate_fixture("invalid-verb.md")
        self.assertIn("V1", rule_ids(errors))

    def test_unbound_interpolation_is_error(self):
        errors, _ = validate_fixture("invalid-unbound.md")
        self.assertIn("U1", rule_ids(errors))

    def test_undeclared_produces_return_is_error(self):
        errors, _ = validate_fixture("invalid-return.md")
        self.assertIn("R2", rule_ids(errors))

    def test_mislabeled_fence_is_error(self):
        errors, _ = validate_fixture("invalid-fence.md")
        self.assertIn("F2", rule_ids(errors))

    def test_missing_run_target_is_error(self):
        errors, _ = validate_fixture("invalid-run.md")
        self.assertIn("R3", rule_ids(errors))

    def test_undeclared_effect_target_is_error(self):
        errors, _ = validate_fixture("invalid-effects.md")
        self.assertIn("E1", rule_ids(errors))

    def test_flow_fence_set_mismatch_is_error(self):
        errors, _ = validate_fixture("invalid-flowset.md")
        self.assertIn("F3", rule_ids(errors))


class TestWarnings(unittest.TestCase):
    def test_ask_mapping_miss_warns_without_errors(self):
        errors, warnings = validate_fixture("warn-ask.md")
        self.assertEqual(errors, [])
        self.assertIn("W3", rule_ids(warnings))

    def test_write_never_read_warns_without_errors(self):
        errors, warnings = validate_fixture("warn-writeonly.md")
        self.assertEqual(errors, [])
        self.assertIn("W5", rule_ids(warnings))

    def test_identical_triggers_warn_on_overlap(self):
        result = skillwren.validate_files(
            [str(FIX / "valid-skeleton.md"), str(FIX / "valid-skeleton.md")])
        warnings = [d for _, ws in result.values() for d in ws]
        self.assertIn("W1", rule_ids(warnings))


class TestCli(unittest.TestCase):
    def run_cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "skillwren", *args],
            capture_output=True, text=True, cwd=str(ROOT), env=env)

    def test_cli_reports_error_and_exits_1(self):
        p = self.run_cli("check", str(FIX / "invalid-verb.md"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("V1", p.stdout)

    def test_cli_clean_file_exits_0(self):
        p = self.run_cli("check", str(FIX / "valid-skeleton.md"))
        self.assertEqual(p.returncode, 0)


BUILDER_FM = """---
skill: tiny
name: tiny
description: Minimal fixture skill.
version: 0.3
purpose: Do the thing.
accepts:
  input: { type: Text, required: true }
produces:
  output: { type: Text }
owns-when:
  - user wants to do the thing
requires:
  main: [input exists]
flows: [main]
authority:
  user-decides: [whether to approve the output]
  system-decides: [whether the input is valid]
  system-may: MAY
  system-must-not: [infer user approval]
effects:
  reads: READS
  creates: [output]
  mutates: []
risk: RISK
cost: cheap
budget: { header: HEADER, body: 2500 }EXTRA
---
"""

BUILDER_CONTRACT = """```contract
resources:
  source:
    path: input
    access: read
    immutable: true
  output:
    path: output
    access: create
always:
  leave the source unchanged
never:
  return an unapproved result
```
"""

BASE_FLOW = """  require input exists
    otherwise:
      abort with "An input is required."

  generate result from input as output
  return output as output
"""

BUILDER_APPENDIX = """
## Appendix

Keep the result minimal and faithful to the input.
"""


def make_skill(tmpdir, name, flow=BASE_FLOW, may="[]", reads="[input]",
               risk="low", header="400", extra="", appendix=True,
               frontmatter=True):
    fm = (BUILDER_FM.replace("MAY", may).replace("READS", reads)
          .replace("RISK", risk).replace("HEADER", header)
          .replace("EXTRA", extra))
    text = (fm + "\n" + BUILDER_CONTRACT + "\n```logic\nmain:\n"
            + flow + "```\n" + (BUILDER_APPENDIX if appendix else ""))
    if not frontmatter:
        text = text.split("---\n", 2)[2]
    p = Path(tmpdir) / name
    p.write_text(text)
    return str(p)


class TestGeneratedCases(unittest.TestCase):
    def validate_built(self, **kw):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return skillwren.validate_file(make_skill(tmp.name, "case.md", **kw))

    def test_tiny_header_budget_is_error(self):
        errors, _ = self.validate_built(header="1")
        self.assertIn("B1", rule_ids(errors))

    def test_return_to_missing_label_is_error(self):
        flow = BASE_FLOW.replace("  return output as output",
                                 "  return to nowhere\n  return output as output")
        errors, _ = self.validate_built(flow=flow)
        self.assertIn("L1", rule_ids(errors))

    def test_mutual_recursion_is_error(self):
        errors, _ = validate_fixture("invalid-recursion.md")
        self.assertIn("L2", rule_ids(errors))

    def test_unexercised_system_may_warns(self):
        errors, warnings = self.validate_built(may="[juggle geese profitably]")
        self.assertEqual(errors, [])
        self.assertIn("W2", rule_ids(warnings))

    def test_missing_appendix_warns(self):
        errors, warnings = self.validate_built(appendix=False)
        self.assertEqual(errors, [])
        self.assertIn("W4", rule_ids(warnings))

    def test_unmatched_effects_entry_warns(self):
        errors, warnings = self.validate_built(reads="[input, phantom-zone]")
        self.assertEqual(errors, [])
        self.assertIn("W6", rule_ids(warnings))

    def test_unknown_frontmatter_field_warns(self):
        errors, warnings = self.validate_built(extra="\nflavor: vanilla")
        self.assertEqual(errors, [])
        self.assertIn("W7", rule_ids(warnings))

    def test_missing_frontmatter_is_error(self):
        errors, _ = self.validate_built(frontmatter=False)
        self.assertIn("F1", rule_ids(errors))

    def test_foreign_run_warns_unresolved(self):
        flow = BASE_FLOW.replace(
            "  return output as output",
            "  run other.main with:\n    input = input\n\n  return output as output")
        errors, warnings = self.validate_built(flow=flow)
        self.assertEqual(errors, [])
        self.assertIn("W8", rule_ids(warnings))

    def test_uncovered_resource_is_error(self):
        flow = BASE_FLOW.replace(
            "  return output as output",
            "  read x from source as data\n  return output as output")
        errors, _ = self.validate_built(flow=flow, reads="[]")
        self.assertIn("E2", rule_ids(errors))

    def test_allow_without_never_is_error(self):
        flow = BASE_FLOW.replace(
            "  return output as output",
            "  allow tea when thirsty:\n  return output as output")
        errors, _ = self.validate_built(flow=flow)
        self.assertIn("A1", rule_ids(errors))

    def test_write_to_immutable_is_error(self):
        flow = BASE_FLOW.replace(
            "  return output as output",
            "  save output as source\n  return output as output")
        errors, _ = self.validate_built(flow=flow)
        self.assertIn("E3", rule_ids(errors))

    def test_bad_risk_value_is_error(self):
        errors, _ = self.validate_built(risk="extreme")
        self.assertIn("F1", rule_ids(errors))

    def test_bare_effect_verb_is_error(self):
        flow = BASE_FLOW.replace("  return output as output",
                                 "  open\n  return output as output")
        errors, _ = self.validate_built(flow=flow)
        self.assertIn("E1", rule_ids(errors))


class TestV04Rules(unittest.TestCase):
    def test_otherwise_without_gate_is_error(self):
        errors, _ = validate_fixture("invalid-otherwise.md")
        self.assertIn("O1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_retry_outside_repair_is_error(self):
        errors, _ = validate_fixture("invalid-retry.md")
        self.assertIn("L3", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_unasked_decisions_are_errors(self):
        errors, _ = validate_fixture("invalid-authority.md")
        a2 = [d for d in errors if d.rule == "A2"]
        self.assertEqual(len(a2), 3)

    def test_ungated_required_input_is_error(self):
        errors, _ = validate_fixture("invalid-required-gate.md")
        self.assertIn("R4", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_noncanonical_access_is_error(self):
        errors, _ = validate_fixture("invalid-access.md")
        self.assertIn("F2", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_resource_schema_is_closed(self):
        errors, _ = validate_fixture("invalid-resource-schema.md")
        f2 = [d for d in errors if d.rule == "F2"]
        self.assertEqual(len(f2), 2)

    def test_type_system_is_closed(self):
        errors, _ = validate_fixture("invalid-types.md")
        f1 = [d for d in errors if d.rule == "F1"]
        self.assertEqual(len(f1), 3)

    def test_type_grammar_unit(self):
        import skillwren.validator as validator
        for good in ("Text", "Number", "Boolean", "Path", "Artifact",
                     "Theme", "ThemeSpec", "Any", "List<Text>",
                     "List<List<Text>>", "List<Enum[a]>", "Enum[a, b]",
                     "Enum[low]"):
            self.assertTrue(validator.valid_type(good), good)
        for bad in ("Potato", "List<>", "List<DragonSpaghetti>",
                    "List<Text", "Enum[]", "Enum[x, x]", "Enum[a,]",
                    "Enum[, a]", "Text ", " List<Text>"):
            self.assertFalse(validator.valid_type(bad), bad)

    def test_negative_budget_is_error(self):
        errors, _ = validate_fixture("invalid-budget.md")
        f1 = [d for d in errors if d.rule == "F1"]
        self.assertEqual(len(f1), 2)

    def test_garbage_version_is_error(self):
        errors, _ = validate_fixture("invalid-version.md")
        self.assertIn("F1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_future_version_is_error(self):
        errors, _ = validate_fixture("invalid-version-new.md")
        self.assertIn("F1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_skill_name_must_be_kebab(self):
        errors, _ = validate_fixture("invalid-skill-name.md")
        self.assertIn("F1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_flow_names_must_be_kebab(self):
        errors, _ = validate_fixture("invalid-flowname.md")
        f1 = [d for d in errors if d.rule == "F1"]
        f2 = [d for d in errors if d.rule == "F2"]
        self.assertEqual(len(f1), 2)
        self.assertEqual(len(f2), 1)

    def test_required_must_be_boolean(self):
        errors, _ = validate_fixture("invalid-required-bool.md")
        self.assertIn("F1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_tabs_rejected(self):
        errors, _ = validate_fixture("invalid-tabs.md")
        self.assertTrue(any(d.rule == "F1" and "tab" in d.msg
                            for d in errors))
        self.assertTrue(any(d.rule == "F2" and "tab" in d.msg
                            for d in errors))

    def test_fence_width_is_strict(self):
        errors, _ = validate_fixture("invalid-fence-strict.md")
        self.assertIn("F2", rule_ids(errors))

    def test_contract_precedes_logic(self):
        errors, _ = validate_fixture("invalid-body-order.md")
        self.assertIn("F2", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_no_fence_after_appendix(self):
        errors, _ = validate_fixture("invalid-appendix-fence.md")
        f2 = [d for d in errors if d.rule == "F2"]
        self.assertEqual(len(f2), 2)

    def test_appendix_word_is_not_an_appendix(self):
        errors, warnings = validate_fixture("warn-appendix-word.md")
        self.assertEqual(errors, [])
        self.assertIn("W4", rule_ids(warnings))

    def test_mutation_before_ask_is_error(self):
        errors, _ = validate_fixture("invalid-mutation-order.md")
        self.assertIn("M1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_run_outputs_scoped_to_callee(self):
        errors, _ = validate_fixture("invalid-run-outputs.md")
        self.assertIn("U1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_apply_cannot_target_resource(self):
        errors, _ = validate_fixture("invalid-apply-resource.md")
        self.assertIn("E4", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_read_write_overlap_requires_mutates(self):
        errors, _ = validate_fixture("invalid-create-mutate.md")
        self.assertIn("E2", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_otherwise_fallthrough_warns(self):
        errors, warnings = validate_fixture("warn-otherwise-fallthrough.md")
        self.assertEqual(errors, [])
        w9 = [d for d in warnings if d.rule == "W9"]
        self.assertEqual(len(w9), 2)

    def test_unreachable_code_warns(self):
        errors, warnings = validate_fixture("warn-unreachable.md")
        self.assertEqual(errors, [])
        self.assertIn("W10", rule_ids(warnings))

    def test_branch_binding_is_path_sensitive(self):
        errors, _ = validate_fixture("invalid-branch-binding.md")
        self.assertIn("U1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_failed_read_binds_nothing(self):
        errors, _ = validate_fixture("invalid-fail-binding.md")
        self.assertIn("U1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_foreach_requires_list_type(self):
        errors, _ = validate_fixture("invalid-foreach-type.md")
        self.assertIn("T1", rule_ids(errors))
        self.assertEqual(len(errors), 1)

    def test_foreach_collection_immutable(self):
        errors, _ = validate_fixture("invalid-foreach-mutate.md")
        l1 = [d for d in errors if d.rule == "L1"]
        self.assertEqual(len(l1), 2)
        self.assertEqual(len(errors), 2)

    def test_foreign_run_marks_unverified_boundary(self):
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        flow = BASE_FLOW.replace(
            "  return output as output",
            "  run other.main with:\n    input = input\n\n  return output as output")
        errors, warnings = skillwren.validate_file(
            make_skill(tmp.name, "case.md", flow=flow))
        self.assertEqual(errors, [])
        w8 = [d for d in warnings if d.rule == "W8"]
        self.assertEqual(len(w8), 1)
        self.assertIn("unverified", w8[0].msg)


if __name__ == "__main__":
    unittest.main()
