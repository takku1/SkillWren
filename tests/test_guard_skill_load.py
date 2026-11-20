"""Skill-load assurance: the guard refuses protected operations unless the
host recorded a load of the approved skill tree in this run (SPEC 24).

These are unit tests of the controller's decision. They do not show that an
agent cannot write the record file; that is the host-isolation assumption.
"""
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren import guard as guard_module
from skillwren.guard import Controller, Denied, file_digest
from skillwren.hostload import record_load
from skillwren.ledger import package_identity

VERIFIER = ROOT / 'docs/current/research/lifecycle/a-manual/tools/verify_report.py'
CLEAN = json.dumps({'banned': [], 'licenses': {'MIT': True}, 'verdict': 'clean'})
RUN = '0b6c2d36-5f0e-4c51-9a55-3f2f1f3c9d01'
OTHER_RUN = '7d1f0f8e-2a64-4c1b-8d5e-6b0f9a1e2c33'


class SkillLoadGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # The approved skill package, as a host would install it.
        self.home = self.root / 'home'
        self.package = self.home / '.claude' / 'skills' / 'build-notes'
        self.package.mkdir(parents=True)
        (self.package / 'SKILL.md').write_text(
            '---\nname: build-notes\ndescription: demo\n---\nSteps.\n', encoding='utf-8')
        (self.package / 'hooks.json').write_text('{}', encoding='utf-8')
        self.tree = package_identity(self.package)['tree_sha256']
        # Host-owned record file, outside the agent workspace.
        self.host = self.root / 'host'
        self.host.mkdir()
        self.loads = self.host / 'loaded.jsonl'
        self.workspace = self.root / 'workspace'
        self.workspace.mkdir()
        verifier = self.host / 'verify.py'
        shutil.copy2(VERIFIER, verifier)
        self.target = self.workspace / 'REPORT.md'
        pins = {PYTHON: file_digest(PYTHON), str(verifier): file_digest(verifier)}
        argv = [PYTHON, '-I', str(verifier)]
        self.policy = {'version': 1,
                       'skill': {'name': 'build-notes', 'tree_sha256': self.tree,
                                 'loads': str(self.loads)},
                       'operations': {
                           'verify#deps': {'argv': argv, 'pins': dict(pins), 'timeout': 5},
                           'write#report': {'target': str(self.target), 'argv': argv,
                                            'pins': dict(pins), 'timeout': 5}}}

    def record(self, path=None, **fields):
        record = {'time': '2026-11-20T00:00:00+00:00', 'skill': 'build-notes',
                  'name': 'build-notes', 'session': RUN, 'path': str(self.package),
                  'tree_sha256': self.tree,
                  'candidates': [{'path': str(self.package), 'tree_sha256': self.tree}],
                  'ambiguous': False}
        record.update(fields)
        with (path or self.loads).open('a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')

    def req(self, action, operation, content=CLEAN):
        return {'action': action, 'operation': operation, 'content': content}

    def write_through(self, guard):
        guard.handle(self.req('verify', 'verify#deps'))
        guard.handle(self.req('verify', 'write#report'))
        return guard.handle(self.req('write', 'write#report'))

    def assertDenied(self, guard, text, action='verify', operation='verify#deps'):
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req(action, operation))
        self.assertIn(text, str(caught.exception))
        self.assertFalse(self.target.exists())

    # Acceptance table, row by row.

    def test_correct_skill_tree_and_run_allows(self):
        self.record()
        result = self.write_through(Controller(self.policy, RUN))
        self.assertEqual(result['written'], 'write#report')
        self.assertEqual(self.target.read_text(), CLEAN)

    def test_no_load_record_denies_every_operation(self):
        guard = Controller(self.policy, RUN)
        self.assertDenied(guard, 'was not loaded in run')
        self.assertDenied(guard, 'was not loaded in run', 'verify', 'write#report')
        self.assertDenied(guard, 'was not loaded in run', 'write', 'write#report')

    def test_empty_record_file_denies(self):
        self.loads.write_text('', encoding='utf-8')
        self.assertDenied(Controller(self.policy, RUN), 'was not loaded in run')

    def test_wrong_skill_denies(self):
        self.record(skill='other', name='other')
        self.assertDenied(Controller(self.policy, RUN), 'was not loaded in run')

    def test_wrong_tree_denies(self):
        self.record(tree_sha256='0' * 64, candidates=[{'path': 'x', 'tree_sha256': '0' * 64}])
        self.assertDenied(Controller(self.policy, RUN), 'unapproved tree')

    def test_load_from_previous_run_denies(self):
        self.record(session=OTHER_RUN)
        self.assertDenied(Controller(self.policy, RUN), 'was not loaded in run')

    def test_record_without_session_denies(self):
        self.record(session=None)
        self.assertDenied(Controller(self.policy, RUN), 'was not loaded in run')

    def test_ambiguous_flag_denies(self):
        self.record(ambiguous=True)
        self.assertDenied(Controller(self.policy, RUN), 'ambiguous')

    def test_missing_ambiguous_flag_denies(self):
        self.record(ambiguous=None)
        self.assertDenied(Controller(self.policy, RUN), 'ambiguous')

    def test_disagreeing_candidates_deny_even_if_flag_says_unambiguous(self):
        self.record(candidates=[{'path': 'a', 'tree_sha256': self.tree},
                                {'path': 'b', 'tree_sha256': '1' * 64}])
        self.assertDenied(Controller(self.policy, RUN), 'ambiguous')

    def test_second_load_with_other_tree_in_same_run_denies(self):
        self.record()
        self.record(tree_sha256='2' * 64, candidates=[{'path': 'b', 'tree_sha256': '2' * 64}])
        self.assertDenied(Controller(self.policy, RUN), 'unapproved tree')

    def test_plugin_qualified_record_matches_by_name(self):
        self.record(skill='notes:build-notes')
        self.assertEqual(self.write_through(Controller(self.policy, RUN))['written'],
                         'write#report')

    def test_malformed_record_file_fails_closed(self):
        self.record()
        with self.loads.open('a', encoding='utf-8') as f:
            f.write('{not json\n')
        self.assertDenied(Controller(self.policy, RUN), 'malformed')

    def test_non_object_record_fails_closed(self):
        self.record()
        with self.loads.open('a', encoding='utf-8') as f:
            f.write('[1, 2]\n')
        self.assertDenied(Controller(self.policy, RUN), 'malformed')

    def test_forged_record_in_agent_workspace_is_not_read(self):
        # The agent can write its own .skillwren/loaded.jsonl; the guard only
        # reads the host-owned path the policy names.
        forged = self.workspace / '.skillwren' / 'loaded.jsonl'
        forged.parent.mkdir()
        self.record(path=forged)
        self.assertDenied(Controller(self.policy, RUN), 'was not loaded in run')

    def test_valid_load_does_not_excuse_stale_verification(self):
        self.record()
        guard = Controller(self.policy, RUN)
        guard.handle(self.req('verify', 'write#report'))
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req('write', 'write#report', CLEAN + ' '))
        self.assertIn('missing, stale or consumed', str(caught.exception))
        guard.handle(self.req('verify', 'write#report'))
        guard.handle(self.req('write', 'write#report'))
        with self.assertRaises(Denied) as caught:
            guard.handle(self.req('write', 'write#report'))
        self.assertIn('missing, stale or consumed', str(caught.exception))

    def test_policy_without_skill_is_unchanged(self):
        policy = dict(self.policy)
        del policy['skill']
        guard = Controller(policy)
        self.assertEqual(self.write_through(guard)['written'], 'write#report')
        self.assertIsNone(guard.handle({'action': 'status'})['skill_load'])

    # Fresh authorization and time of check.

    def test_conflicting_load_after_verify_denies_the_write(self):
        self.record()
        guard = Controller(self.policy, RUN)
        guard.handle(self.req('verify', 'write#report'))
        self.record(tree_sha256='3' * 64, candidates=[{'path': 'c', 'tree_sha256': '3' * 64}])
        self.assertDenied(guard, 'unapproved tree', 'write', 'write#report')

    def test_conflict_appended_during_write_denies_at_commit(self):
        self.record()
        guard = Controller(self.policy, RUN)
        guard.handle(self.req('verify', 'write#report'))
        real_target = Controller._target
        def target_then_conflict(controller, op):
            result = real_target(controller, op)
            self.record(ambiguous=True)
            return result
        with mock.patch.object(Controller, '_target', target_then_conflict):
            self.assertDenied(guard, 'ambiguous', 'write', 'write#report')

    # Policy validation.

    def test_requirement_needs_run_id(self):
        for run in (None, '', '  '):
            with self.assertRaises(Denied) as caught:
                Controller(self.policy, run)
            self.assertIn('run id', str(caught.exception))

    def test_requirement_shape_is_strict(self):
        bad = [{'name': 'build-notes', 'tree_sha256': self.tree},
               {'name': '', 'tree_sha256': self.tree, 'loads': str(self.loads)},
               {'name': 'build-notes', 'tree_sha256': self.tree.upper(), 'loads': str(self.loads)},
               {'name': 'build-notes', 'tree_sha256': self.tree[:-1], 'loads': str(self.loads)},
               {'name': 'build-notes', 'tree_sha256': self.tree, 'loads': 'loaded.jsonl'},
               {'name': 'build-notes', 'tree_sha256': self.tree,
                'loads': str(self.root / 'missing' / 'loaded.jsonl')},
               {'name': 'build-notes', 'tree_sha256': self.tree, 'loads': str(self.loads),
                'path': 'extra'}]
        for spec in bad:
            with self.assertRaises(Denied, msg=spec):
                Controller({**self.policy, 'skill': spec}, RUN)

    def test_status_reports_the_requirement(self):
        status = Controller(self.policy, RUN).handle({'action': 'status'})
        self.assertEqual(status['skill_load'],
                         {'name': 'build-notes', 'tree_sha256': self.tree, 'run': RUN})

    # End to end through the hook writer.

    def test_hook_record_with_host_out_path_satisfies_the_guard(self):
        event = {'tool_name': 'Skill', 'tool_input': {'skill': 'build-notes'},
                 'cwd': str(self.workspace), 'session_id': RUN}
        record = record_load(event, home=self.home, out=self.loads)
        self.assertEqual(record['tree_sha256'], self.tree)
        self.assertFalse((self.workspace / '.skillwren').exists())
        self.assertEqual(self.write_through(Controller(self.policy, RUN))['written'],
                         'write#report')

    def test_hook_record_from_another_session_does_not(self):
        event = {'tool_name': 'Skill', 'tool_input': {'skill': 'build-notes'},
                 'cwd': str(self.workspace), 'session_id': OTHER_RUN}
        record_load(event, home=self.home, out=self.loads)
        self.assertDenied(Controller(self.policy, RUN), 'was not loaded in run')

    def test_hook_record_of_an_edited_package_does_not(self):
        (self.package / 'hooks.json').write_text('{"PostToolUse": []}', encoding='utf-8')
        event = {'tool_name': 'Skill', 'tool_input': {'skill': 'build-notes'},
                 'cwd': str(self.workspace), 'session_id': RUN}
        record_load(event, home=self.home, out=self.loads)
        self.assertDenied(Controller(self.policy, RUN), 'unapproved tree')

    def test_cli_requires_run_id_for_a_skill_policy(self):
        policy = self.host / 'policy.json'
        policy.write_text(json.dumps(self.policy), encoding='utf-8')
        args = [str(policy), '--audit', str(self.host / 'audit.jsonl'),
                '--checkpoint', str(self.host / 'audit.ckpt')]
        err = io.StringIO()
        with mock.patch('sys.stderr', err):
            self.assertEqual(guard_module.main(args), 2)
        self.assertIn('run id', err.getvalue())
        self.record()
        out = io.StringIO()
        stdin = io.TextIOWrapper(io.BytesIO(
            (json.dumps(self.req('verify', 'verify#deps')) + '\n').encode('utf-8')))
        with mock.patch('sys.stdin', stdin), mock.patch('sys.stdout', out):
            self.assertEqual(guard_module.main(args + ['--run-id', RUN]), 0)
        self.assertTrue(json.loads(out.getvalue().splitlines()[0])['ok'])
        audit = [json.loads(line) for line in
                 (self.host / 'audit.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertTrue(any(r.get('run_id') == RUN for r in audit))


if __name__ == '__main__':
    unittest.main()
