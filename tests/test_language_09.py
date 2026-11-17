"""0.9 language additions: typed return anchors and declared read-only exec."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.validator import validate_fragment
from skillwren.validator.workflow import explain_workflow

TERMINAL = '''# Terminal anchor

```contract
order:
  verify#final before return#result
```

```logic
main:
  exec suite from checks as results
{early}  verify #final every test passed from results
    otherwise:
      abort with "Red suite."
  return #result results as report
```
'''
EARLY = '''  if results show a flaky test:
    return #result results as report
'''
BLOCK = '''# Typed return block

```contract
order:
  verify#final before return#done
```

```logic
main:
  exec suite from checks as results
  verify #final every test passed from results
    otherwise:
      abort with "Red suite."
  return #done:
    report = results
```
'''
ASK = '''# Exec before ask

```logic
main:
  exec {mode}status check from checks as status
  verify the tree is clean from status
  ask user to approve the plan
  require confirmation
    otherwise:
      abort with "Declined."
  write plan with target
  return plan as plan
```
'''


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def rules(self, text):
        path = Path(self.tmp.name) / 'flow.md'
        path.write_text(text, encoding='utf-8')
        errors, _ = validate_fragment(str(path))
        return [d.rule for d in errors], path

    def test_typed_return_is_order_anchored(self):
        rules, _ = self.rules(TERMINAL.format(early=''))
        self.assertEqual(rules, [])

    def test_return_before_its_prerequisite_is_p1(self):
        # Two `return #result` statements: P1 on the early one, and no P2,
        # because returns of one exit may share their ID.
        rules, _ = self.rules(TERMINAL.format(early=EARLY))
        self.assertEqual(rules, ['P1'])

    def test_return_id_still_unique_against_other_verbs(self):
        text = TERMINAL.format(early='').replace('return #result', 'return #final')
        rules, _ = self.rules(text)
        self.assertIn('P2', rules)

    def test_typed_return_block(self):
        rules, _ = self.rules(BLOCK)
        self.assertEqual(rules, [])
        early = BLOCK.replace('  verify #final', '  if results are empty:\n'
                              '    return #done:\n      report = results\n  verify #final', 1)
        rules, _ = self.rules(early)
        self.assertEqual(rules, ['P1'])

    def test_plain_exec_before_ask_is_m1(self):
        rules, _ = self.rules(ASK.format(mode=''))
        self.assertIn('M1', rules)

    def test_readonly_exec_before_ask_is_not_a_mutation(self):
        rules, path = self.rules(ASK.format(mode='readonly '))
        self.assertNotIn('M1', rules)
        text = explain_workflow(path, fragment=True)
        self.assertIn('declared read-only', text)
        self.assertIn('ledger exec --readonly', text)

    def test_readonly_exec_still_needs_binding(self):
        rules, _ = self.rules(ASK.format(mode='readonly ').replace(' as status', ''))
        self.assertIn('V1', rules)


if __name__ == '__main__':
    unittest.main()
