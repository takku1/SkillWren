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


class Denied(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    return digest(Path(path).read_bytes()) if Path(path).exists() else None


class Controller:
    def __init__(self, policy):
        self.policy = json.loads(json.dumps(policy))
        if set(self.policy) != {'version', 'operations'} or self.policy['version'] != 1:
            raise Denied('unsupported policy')
        self.operations = self.policy['operations']
        if not isinstance(self.operations, dict) or not self.operations:
            raise Denied('operations must be a nonempty map')
        targets = set()
        for name, op in self.operations.items():
            if not isinstance(name, str) or not name or not isinstance(op, dict):
                raise Denied('invalid operation')
            if set(op) != {'target', 'argv', 'pins', 'timeout'}:
                raise Denied('operation requires target, argv, pins, timeout')
            target = Path(op['target'])
            if not target.is_absolute() or not target.parent.is_dir():
                raise Denied('target must have an existing absolute parent')
            canonical = str(target.resolve()).casefold() if os.name == 'nt' else str(target.resolve())
            if canonical in targets:
                raise Denied('duplicate target')
            targets.add(canonical)
            argv = op['argv']
            if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
                raise Denied('argv must be a string list')
            if not Path(argv[0]).is_absolute() or argv[0] not in op['pins']:
                raise Denied('absolute executable must be pinned')
            if not isinstance(op['timeout'], (int, float)) or not 0 < op['timeout'] <= 60:
                raise Denied('timeout must be in (0, 60]')
            self._pins(op)
            self._target(op)
        self.approvals = {}
        self.lock = threading.Lock()

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

    def handle(self, request):
        with self.lock:
            if not isinstance(request, dict):
                raise Denied('request must be an object')
            if request == {'action': 'status'}:
                return {'approved': sorted(self.approvals), 'coverage': 'controller requests only'}
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
            target = self._target(op)
            binding = (digest(data), file_digest(target))
            if action == 'verify':
                self.approvals.pop(name, None)
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
                        or result.get('ok') is not True or result.get('input_sha256') != binding[0]):
                    raise Denied('verifier rejected candidate or returned wrong digest')
                self._pins(op)
                if file_digest(target) != binding[1]:
                    raise Denied('target changed during verification')
                self.approvals[name] = binding
                return {'verified': name, 'input_sha256': binding[0]}
            approval = self.approvals.pop(name, None)
            if approval != binding:
                raise Denied('missing, stale or consumed verification')
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
            return {'written': name, 'sha256': binding[0]}


def main(argv):
    parser = argparse.ArgumentParser(prog='skillwren guard')
    parser.add_argument('policy', help='trusted host policy JSON; not agent-controlled')
    parser.add_argument('--audit', required=True, help='host-owned event log')
    parser.add_argument('--checkpoint', required=True, help='independently protected checkpoint')
    args = parser.parse_args(argv)
    try:
        controller = Controller(json.loads(Path(args.policy).read_text(encoding='utf-8')))
        audit = AuditStore(args.audit, args.checkpoint)
        if audit.records and audit.records[-1].get('type') == 'intent':
            raise Denied('unfinished write/request intent; host must reconcile output before recovery')
        audit.append({'type': 'start', 'policy_sha256': digest(Path(args.policy).read_bytes()),
                      'coverage': 'controller requests only; not direct host activity'})
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
