"""Trusted-host, single-process capability controller. See runtime-assurance.md.

No filesystem isolation is provided by importing this module. The embedding
host must deny the requester direct access to outputs, policy and verifiers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from .audit import AuditStore
from .certgate import verify as certgate_verify


class Denied(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    return digest(Path(path).read_bytes()) if Path(path).exists() else None


class Controller:
    def __init__(self, policy, run_id=None):
        self.policy = json.loads(json.dumps(policy))
        if (set(self.policy) - {'workflow', 'skill'} != {'version', 'operations'}
                or self.policy['version'] != 1):
            raise Denied('unsupported policy')
        self.skill = self.policy.get('skill')
        if self.skill is not None:
            self._check_skill_spec(run_id)
        self.run_id = run_id
        self.operations = self.policy['operations']
        if not isinstance(self.operations, dict) or not self.operations:
            raise Denied('operations must be a nonempty map')
        targets = set()
        for name, op in self.operations.items():
            if not isinstance(name, str) or not name or not isinstance(op, dict):
                raise Denied('invalid operation')
            # A check operation (no target) only verifies: it records that a
            # pinned verifier accepted a candidate, for order rules to cite.
            # A write operation may additionally name a dpcc section binding
            # it to a certified deployment (report, study, artifacts, regime,
            # config, and a monitor check operation).
            if set(op) not in ({'target', 'argv', 'pins', 'timeout'},
                               {'argv', 'pins', 'timeout'},
                               {'target', 'argv', 'pins', 'timeout', 'dpcc'}):
                raise Denied('operation requires argv, pins, timeout, and target unless a check')
            self._check_argv(op)
            if 'target' not in op:
                self._pins(op)
                continue
            target = Path(op['target'])
            if not target.is_absolute() or not target.parent.is_dir():
                raise Denied('target must have an existing absolute parent')
            canonical = str(target.resolve()).casefold() if os.name == 'nt' else str(target.resolve())
            if canonical in targets:
                raise Denied('duplicate target')
            targets.add(canonical)
            self._pins(op)
            self._target(op)
        for op in self.operations.values():
            if 'dpcc' in op:
                self._check_dpcc(op)
        self.approvals = {}
        self.completed = set()
        self.ran = set()  # every operation that ran, failed checks included
        self.rules, self.exclusions, self.unenforced = [], [], []
        self.workflow = self.policy.get('workflow')
        if self.workflow is not None:
            self._load_workflow()
        self.lock = threading.Lock()

    def _check_skill_spec(self, run_id):
        """Validate a skill-load requirement at policy load (SPEC 24).

        The host names the skill, the exact package tree it approved, the
        host-owned file its record-load hook appends to, and (on the
        command line, not in the reusable policy) the run this guard serves.
        Nothing here comes from the agent."""
        spec = self.skill
        if not isinstance(spec, dict) or set(spec) != {'name', 'tree_sha256', 'loads'}:
            raise Denied('skill requires name, tree_sha256, loads')
        if not isinstance(spec['name'], str) or not spec['name'].strip():
            raise Denied('skill name must be a nonempty string')
        if (not isinstance(spec['tree_sha256'], str) or len(spec['tree_sha256']) != 64
                or any(c not in '0123456789abcdef' for c in spec['tree_sha256'])):
            raise Denied('skill tree_sha256 must be 64 lowercase hexadecimal characters')
        loads = spec['loads']
        if not isinstance(loads, str) or not Path(loads).is_absolute():
            raise Denied('skill loads must be an absolute path')
        if not Path(loads).parent.is_dir():
            raise Denied('skill loads must have an existing parent')
        if not isinstance(run_id, str) or not run_id.strip():
            raise Denied('a skill requirement needs the host run id')

    def _check_skill_load(self):
        """Deny unless the host recorded a load of the approved skill tree
        in this run, and nothing in this run contradicts it.

        Fails closed: the record file is host-owned, so an unreadable file,
        a malformed line, an ambiguous resolution, or a second load of the
        same name with a different tree all deny. Records from other runs
        are ignored. A record proves the host loaded the package, not that
        the agent read or followed it."""
        if self.skill is None:
            return
        name, expected = self.skill['name'], self.skill['tree_sha256']
        path = Path(self.skill['loads'])
        if path.is_symlink():
            raise Denied('skill load records must not be a symlink')
        try:
            lines = path.read_bytes().decode('utf-8').splitlines()
        except FileNotFoundError:
            lines = []
        except (OSError, UnicodeError):
            raise Denied('skill load records unreadable')
        matched = []
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                raise Denied('skill load records malformed')
            if not isinstance(record, dict):
                raise Denied('skill load records malformed')
            if record.get('session') != self.run_id:
                continue
            if name in (record.get('skill'), record.get('name')):
                matched.append(record)
        if not matched:
            raise Denied(f'skill {name} was not loaded in run {self.run_id}')
        for record in matched:
            digests = {record.get('tree_sha256')} | {
                c.get('tree_sha256') if isinstance(c, dict) else None
                for c in record.get('candidates') or []}
            if record.get('ambiguous') is not False or len(digests) != 1:
                raise Denied(f'skill {name} load is ambiguous: candidates differ')
            if digests != {expected}:
                raise Denied(f'skill {name} loaded with an unapproved tree')

    def _check_argv(self, op):
        argv = op['argv']
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            raise Denied('argv must be a string list')
        if not Path(argv[0]).is_absolute() or argv[0] not in op['pins']:
            raise Denied('absolute executable must be pinned')
        # Verifier identity is the executable plus every file it is told to
        # run: an unpinned script argument could be swapped after startup.
        # Relative paths cannot be pinned (verifiers run in a temporary cwd).
        for arg in argv[1:]:
            if Path(arg).is_absolute() and arg not in op['pins']:
                raise Denied('every absolute path argument must be pinned: ' + arg)
            if not Path(arg).is_absolute() and not arg.startswith('-') and Path(arg).suffix:
                raise Denied('relative path arguments cannot be pinned: ' + arg)
        if not isinstance(op['timeout'], (int, float)) or not 0 < op['timeout'] <= 60:
            raise Denied('timeout must be in (0, 60]')

    def _load_workflow(self):
        """Bind this controller to one approved flow and compile its order rules.

        The flow's exact bytes are pinned, and the host-owned approval record
        must approve those bytes. Typed order rules whose both steps are
        policy operations become write preconditions; every other rule is
        listed as unenforced (it stays a static or ledger check)."""
        workflow = self.workflow
        if not isinstance(workflow, dict) or set(workflow) != {'flow', 'flow_sha256', 'approvals'}:
            raise Denied('workflow requires flow, flow_sha256, approvals')
        for key in ('flow', 'approvals'):
            if not Path(workflow[key]).is_absolute():
                raise Denied('workflow paths must be absolute')
        self._check_workflow()
        from .validator.workflow import dump_workflow
        dump = dump_workflow(workflow['flow'], True)
        for rule in dump['order_rules']:
            first, then = rule['first'], rule['then']
            if first in self.operations and then in self.operations \
                    and 'target' in self.operations[then]:
                self.rules.append((first, then))
            else:
                self.unenforced.append(f'{first} before {then}')
        # SPEC 23: `never A before B` is enforced when both steps are policy
        # operations: once A has run, B is refused. A check counts as run
        # when its verifier is invoked, even if it fails (the ledger counts
        # attempts too); a write counts once it commits.
        for rule in dump.get('exclusion_rules', []):
            first, then = rule['first'], rule['then']
            if first in self.operations and then in self.operations:
                self.exclusions.append((first, then))
            else:
                self.unenforced.append(f'never {first} before {then}')

    def _check_workflow(self):
        from .validator.approval import check
        workflow = self.workflow
        if file_digest(workflow['flow']) != workflow['flow_sha256']:
            raise Denied('workflow file changed or missing')
        report = check(workflow['flow'], workflow['approvals'])
        if not report.get('approved'):
            raise Denied('workflow not approved: ' + report.get('reason', 'unknown'))

    def _pins(self, op):
        if not isinstance(op['pins'], dict) or not op['pins']:
            raise Denied('pins required')
        for path, expected in op['pins'].items():
            if not Path(path).is_absolute() or Path(path).is_symlink() or file_digest(path) != expected:
                raise Denied('verifier identity changed')

    def _target(self, op):
        target = Path(op['target'])
        if any(p.is_symlink() for p in [target, *target.parents]):
            raise Denied('symlink targets forbidden')
        if target.exists() and (not target.is_file() or target.stat().st_nlink != 1):
            raise Denied('target must be a regular unlinked file')
        return target

    def _check_dpcc(self, op):
        """Validate a deployment-certification binding at policy load.

        The policy is host-owned: naming an operation here is the host
        asserting that this write deploys a certified artifact. Monitor
        must name a check-only operation whose completion evidences a
        passing runtime monitor. Evidence files are read fresh at each
        write; only their paths and the regime/config bindings are
        pinned here.
        """
        spec = op['dpcc']
        if not isinstance(spec, dict) or set(spec) != {
                'report', 'study', 'artifacts', 'regime', 'cfg', 'monitor'}:
            raise Denied('dpcc requires report, study, artifacts, regime, cfg, monitor')
        for key in ('report', 'study', 'artifacts'):
            if not isinstance(spec[key], str) or not Path(spec[key]).is_absolute():
                raise Denied(f'dpcc {key} must be an absolute path')
        if not isinstance(spec['regime'], dict) or not spec['regime']:
            raise Denied('dpcc regime must be a nonempty object')
        if (not isinstance(spec['cfg'], str) or len(spec['cfg']) != 64
                or any(c not in '0123456789abcdef' for c in spec['cfg'])):
            raise Denied('dpcc cfg must be 64 lowercase hexadecimal characters')
        monitor = spec['monitor']
        if monitor not in self.operations or 'target' in self.operations[monitor]:
            raise Denied('dpcc monitor must name a check operation')

    def _enforce_dpcc(self, op, data):
        """Require a fresh certgate allow before a certified write.

        Re-reads the report, study, and artifacts on every write, so no
        verdict file can go stale or be replayed. The written bytes must
        equal the selected router's bound artifact: this operation
        deploys the certified artifact, nothing else. Returns a snapshot
        of the evidence digests for confirmation immediately before the
        write commits, narrowing concurrent modification to a negligible
        window (host file ownership remains the real boundary).
        """
        spec = op['dpcc']
        try:
            raw_report = Path(spec['report']).read_bytes()
            report = json.loads(raw_report.decode('utf-8-sig'))
            raw_study = Path(spec['study']).read_bytes()
            study = json.loads(raw_study.decode('utf-8-sig'))
            artifacts = {path.name: path.read_bytes()
                         for path in sorted(Path(spec['artifacts']).iterdir())
                         if path.is_file()}
        except OSError:
            raise Denied('dpcc evidence unreadable')
        except ValueError:
            raise Denied('dpcc evidence invalid')
        if spec['monitor'] not in self.completed:
            raise Denied('dpcc monitor has not passed')
        # Bind the monitor to the exact bytes being deployed: the check
        # re-runs now, against the current artifact, not an earlier state.
        self._run_verifier(self.operations[spec['monitor']], data)
        verdict = certgate_verify(report, artifacts, spec['regime'], spec['cfg'],
                                  True, True,
                                  study=study, study_sha256=digest(raw_study))
        if verdict['verdict'] != 'allow':
            raise Denied('dpcc gate denied: ' + '; '.join(verdict['reasons']))
        bound = artifacts.get(verdict['selected'])
        if bound is None or digest(data) != digest(bound):
            raise Denied('content is not the certified artifact')
        return {'report': digest(raw_report), 'study': digest(raw_study),
                'artifacts': {name: digest(blob) for name, blob in artifacts.items()},
                'selected': verdict['selected']}

    def _confirm_dpcc_snapshot(self, op, data, snapshot):
        """Re-hash evidence immediately before the write commits.

        Denies when anything changed since verification: report, study,
        artifacts, selection, or the content itself.
        """
        spec = op['dpcc']
        try:
            raw_report = Path(spec['report']).read_bytes()
            raw_study = Path(spec['study']).read_bytes()
            artifacts = {path.name: path.read_bytes()
                         for path in sorted(Path(spec['artifacts']).iterdir())
                         if path.is_file()}
        except OSError:
            raise Denied('dpcc evidence unreadable at commit')
        if (digest(raw_report) != snapshot['report']
                or digest(raw_study) != snapshot['study']
                or {name: digest(blob) for name, blob in artifacts.items()}
                != snapshot['artifacts']
                or digest(data) != digest(artifacts.get(snapshot['selected'], b'\0'))):
            raise Denied('dpcc evidence changed before commit')

    def handle(self, request):
        with self.lock:
            if not isinstance(request, dict):
                raise Denied('request must be an object')
            if request == {'action': 'status'}:
                return {'approved': sorted(self.approvals), 'completed': sorted(self.completed),
                        'enforced_rules': [f'{a} before {b}' for a, b in self.rules]
                        + [f'never {a} before {b}' for a, b in self.exclusions],
                        'unenforced_rules': self.unenforced,
                        'skill_load': None if self.skill is None else {
                            'name': self.skill['name'],
                            'tree_sha256': self.skill['tree_sha256'],
                            'run': self.run_id},
                        'coverage': 'controller requests only'}
            if set(request) != {'action', 'operation', 'content'}:
                raise Denied('only action, operation and content accepted')
            action, name, content = request['action'], request['operation'], request['content']
            if action not in ('verify', 'write') or not isinstance(name, str) or name not in self.operations:
                raise Denied('unknown action or operation')
            if not isinstance(content, str) or len(content.encode('utf-8')) > 1024 * 1024:
                raise Denied('content must be UTF-8 text of at most 1 MiB')
            data = content.encode('utf-8')
            op = self.operations[name]
            self._pins(op)
            self._check_skill_load()
            if 'target' not in op:
                if action != 'verify':
                    raise Denied('check operations only verify')
                self._check_exclusions(name)
                self.completed.discard(name)  # a failed check revokes earlier success
                self.ran.add(name)
                self._run_verifier(op, data)
                self.completed.add(name)
                return {'checked': name, 'input_sha256': digest(data)}
            target = self._target(op)
            binding = (digest(data), file_digest(target))
            if action == 'verify':
                self.approvals.pop(name, None)
                self._run_verifier(op, data)
                if file_digest(target) != binding[1]:
                    raise Denied('target changed during verification')
                self.approvals[name] = binding
                return {'verified': name, 'input_sha256': binding[0]}
            approval = self.approvals.pop(name, None)
            if approval != binding:
                raise Denied('missing, stale or consumed verification')
            snapshot = self._enforce_dpcc(op, data) if 'dpcc' in op else None
            if self.workflow is not None:
                self._check_workflow()
                missing = [first for first, then in self.rules
                           if then == name and first not in self.completed]
                if missing:
                    raise Denied('order rule not satisfied: ' + ', '.join(
                        f'{first} before {name}' for first in missing))
                self._check_exclusions(name)
            # Re-read immediately before commit: a conflicting record appended
            # while this request ran (dpcc monitor, approval check) denies.
            self._check_skill_load()
            if snapshot is not None:
                self._confirm_dpcc_snapshot(op, data, snapshot)
            fd, temporary = tempfile.mkstemp(prefix='.skillwren-', dir=target.parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            self.completed.add(name)
            self.ran.add(name)
            return {'written': name, 'sha256': binding[0]}

    def _check_exclusions(self, name):
        if self.workflow is None:
            return
        ran = [first for first, then in self.exclusions if then == name and first in self.ran]
        if ran:
            raise Denied('exclusion rule: ' + ', '.join(
                f'{first} already ran; never {first} before {name}' for first in ran))

    def _run_verifier(self, op, data):
        # Verifiers are trusted administrator programs, not agent scripts.
        # Isolated cwd/env limit accidental dependence; this is no sandbox.
        env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR') if k in os.environ}
        with tempfile.TemporaryDirectory(prefix='skillwren-verify-') as cwd:
            proc = subprocess.run(op['argv'], input=data, capture_output=True,
                                  cwd=cwd, env=env, timeout=op['timeout'])
        try:
            result = json.loads(proc.stdout)
        except (ValueError, UnicodeError):
            raise Denied('verifier did not return JSON')
        if (proc.returncode != 0 or not isinstance(result, dict)
                or result.get('ok') is not True or result.get('input_sha256') != digest(data)):
            raise Denied('verifier rejected candidate or returned wrong digest')
        self._pins(op)


def main(argv):
    parser = argparse.ArgumentParser(prog='skillwren guard')
    parser.add_argument('policy', help='trusted host policy JSON; not agent-controlled')
    parser.add_argument('--audit', required=True, help='host-owned event log')
    parser.add_argument('--checkpoint', required=True, help='independently protected checkpoint')
    parser.add_argument('--run-id', default=None,
                        help='host run id (the session id the host gave the agent);'
                             ' required when the policy has a skill requirement')
    args = parser.parse_args(argv)
    try:
        controller = Controller(json.loads(Path(args.policy).read_text(encoding='utf-8')),
                                args.run_id)
        audit = AuditStore(args.audit, args.checkpoint)
        if audit.records and audit.records[-1].get('type') == 'intent':
            raise Denied('unfinished write/request intent; host must reconcile output before recovery')
        start = {'type': 'start', 'policy_sha256': digest(Path(args.policy).read_bytes()),
                 'coverage': 'controller requests only; not direct host activity'}
        if controller.skill is not None:
            start['run_id'] = args.run_id
        audit.append(start)
        while True:
            line = sys.stdin.buffer.readline(2 * 1024 * 1024 + 1)
            if not line:
                audit.append({'type': 'stop'})
                return 0
            if len(line) > 2 * 1024 * 1024:
                print(json.dumps({'ok': False, 'error': 'request too large'}), flush=True)
                return 2
            try:
                audit.append({'type': 'intent', 'request_sha256': digest(line)})
                response = {'ok': True, 'result': controller.handle(json.loads(line))}
            except (Denied, OSError, ValueError, subprocess.TimeoutExpired) as error:
                response = {'ok': False, 'error': str(error)}
            audit.append({'type': 'result', 'ok': response['ok']})
            print(json.dumps(response), flush=True)
    except (Denied, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
