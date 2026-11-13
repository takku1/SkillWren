"""Explainer + AST dump tests over the five NL-fidelity pairs.

Each pair is a natural-language intent, its hand-authored SkillWren flow,
and the key facts an independent reviewer must recover from the
explanation alone. These tests pin the inspectability claim: the facts
must be present in deterministic explainer output, not in a model's
paraphrase.
"""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.validator.workflow import (
    DUMP_VERSION, dump_workflow, explain_workflow)

PAIRS = Path(ROOT, 'docs/current/research/nl-fidelity')

# (flow file, facts file); facts are either a list (single-flow file) or
# a {flow: [facts]} map (batch files).
CORPUS = ([(f'{n}-flow.md', f'{n}-facts.json') for n in
           ('01', '02', '03', '04', '05')]
          + [(f'pairs{b}-flow.md', f'pairs{b}-facts.json') for b in
             ('06', '11', '16', '21')])


def load_facts(name):
    return json.loads((PAIRS / name).read_text())


class ExplainerTests(unittest.TestCase):
    def test_all_pairs_present(self):
        for flow_name, facts_name in CORPUS:
            self.assertTrue((PAIRS / flow_name).is_file(), flow_name)
            self.assertTrue((PAIRS / facts_name).is_file(), facts_name)
        for intent in ('01', '02', '03', '04', '05'):
            self.assertTrue((PAIRS / f'{intent}-intent.md').is_file(), intent)
        for batch in ('06', '11', '16', '21'):
            self.assertTrue((PAIRS / f'pairs{batch}-intent.md').is_file(), batch)

    def test_explanation_states_each_pair_facts(self):
        count = 0
        for flow_name, facts_name in CORPUS:
            text = explain_workflow(PAIRS / flow_name, fragment=True)
            facts = load_facts(facts_name)
            groups = facts.values() if isinstance(facts, dict) else [facts]
            for group in groups:
                for fact in group:
                    self.assertIn(fact, text, f'{flow_name}: {fact!r}')
                    count += 1
        self.assertGreaterEqual(count, 80, count)

    def test_explainer_is_deterministic(self):
        flow = PAIRS / '03-flow.md'
        self.assertEqual(explain_workflow(flow, fragment=True),
                         explain_workflow(flow, fragment=True))


class DumpTests(unittest.TestCase):
    def test_dump_versioned_and_provenanced(self):
        for flow_name, _ in CORPUS:
            dump = dump_workflow(PAIRS / flow_name, fragment=True)
            self.assertEqual(dump['version'], DUMP_VERSION)
            self.assertTrue(dump['flows'], flow_name)
            for statements in dump['flows'].values():
                self.assertTrue(statements, flow_name)
                for statement in self._flatten(statements):
                    self.assertGreater(statement['line'], 0, flow_name)
                    self.assertTrue(statement['text'], flow_name)
                    self.assertTrue(statement['explicit'], flow_name)

    def test_order_rules_carry_line_numbers(self):
        dump = dump_workflow(PAIRS / '01-flow.md', fragment=True)
        self.assertEqual(
            [(r['first'], r['then']) for r in dump['order_rules']],
            [('verify#check', 'write#config')])
        self.assertTrue(all(r['line'] > 0 for r in dump['order_rules']))

    def test_inferred_inputs_segregated_from_declared(self):
        dump = dump_workflow(PAIRS / '05-flow.md', fragment=True)
        self.assertEqual(dump['declared_inputs'], [])
        self.assertIn('request', dump['inferred']['inputs'])

    def _flatten(self, statements):
        for statement in statements:
            yield statement
            yield from self._flatten(statement.get('children', []))


if __name__ == '__main__':
    unittest.main()
