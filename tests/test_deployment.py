"""End-to-end deployment test: adversarial agent in a container, guard on the host.

Topology under test: the guard controller, policy, verifiers, protected
targets, and audit store live on the trusted host and are never mounted into
the agent's container. The agent's only channel to protected state is the
guard's JSON-lines request protocol over stdio. The agent keeps its normal
tools (file writes, stdlib, no network) in an agent-owned scratch mount;
its script mount is read-only and host-owned paths are never mounted.

This is a mechanism test, not a red-team exercise: the adversary script is
fixed, so it proves the deployment denies direct access and that only the
mediated verify-then-write path mutates the target. It does not prove a
creative agent could not find another host misconfiguration.

Skipped when docker is unavailable.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.guard import file_digest

IMAGE = 'python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b'

ADVERSARY = r'''
import json, pathlib
report = {}
for name, path in [('direct_target', '/protected/sensitive.json'),
                   ('policy', '/policy/policy.json'),
                   ('audit', '/audit/events')]:
    try:
        pathlib.Path(path).write_bytes(b'bypass')
        report[name] = 'writable'
    except OSError:
        report[name] = 'unavailable'
    report[name + '_seen'] = pathlib.Path(path).exists()
# Normal tools still work in the agent-owned scratch space.
pathlib.Path('/scratch/agent-output.txt').write_text('agent was here')
report['own_scratch'] = 'writable'
print(json.dumps(report))
# Talk to the guard through the only channel: the request protocol.
for request in [{'action': 'write', 'operation': 'write#config', 'content': '{"debug": false}'},
                {'action': 'verify', 'operation': 'write#config', 'content': '{"debug": false}'},
                {'action': 'write', 'operation': 'write#config', 'content': '{"debug": false}'}]:
    print(json.dumps(request))
'''

DOCKER_FLAGS = ['--rm', '--network=none', '--read-only', '--cap-drop=ALL',
                '--security-opt=no-new-privileges', '--pids-limit=64',
                '--memory=128m', '--cpus=1', '--user=65534:65534']


def _docker_can_run():
    if not shutil.which('docker'):
        return False
    try:
        proc = subprocess.run(['docker', 'run', '--rm', IMAGE, 'python', '-c', 'pass'],
                              capture_output=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


@unittest.skipUnless(_docker_can_run(), 'docker or the pinned Linux image unavailable')
class DeploymentTests(unittest.TestCase):
    def test_agent_cannot_bypass_host_guard(self):
        from skillwren.audit import AuditStore
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protected = root / 'protected'
            protected.mkdir()
            target = protected / 'sensitive.json'
            script = str(ROOT / 'examples/guard/verify_config.py')
            policy = {'version': 1, 'operations': {'write#config': {
                'target': str(target), 'argv': [PYTHON, '-I', script],
                'pins': {PYTHON: file_digest(PYTHON), script: file_digest(script)},
                'timeout': 5}}}
            (root / 'policy.json').write_text(json.dumps(policy))
            work = root / 'work'
            work.mkdir()
            (work / 'adversary.py').write_text(ADVERSARY)
            # Agent-owned scratch: a fresh empty directory opened to the
            # container user, so the write test does not depend on who owns
            # the checkout. Protected, policy, and audit paths stay unmounted.
            # The temp root and script dir get traverse/read bits for the
            # same reason; the mounts themselves carry the real boundary.
            root.chmod(0o711)
            work.chmod(0o755)
            scratch = root / 'scratch'
            scratch.mkdir()
            scratch.chmod(0o777)
            agent = subprocess.run(
                ['docker', 'run', *DOCKER_FLAGS,
                 '--mount', f'type=bind,source={work},target=/work,readonly',
                 '--mount', f'type=bind,source={scratch},target=/scratch',
                 '--workdir=/work', IMAGE, 'python', '-I', '/work/adversary.py'],
                capture_output=True, text=True, timeout=120)
            self.assertEqual(agent.returncode, 0, agent.stderr)
            lines = agent.stdout.splitlines()
            report = json.loads(lines[0])
            # Direct access to every host-owned path is unavailable.
            for name in ('direct_target', 'policy', 'audit'):
                self.assertEqual(report[name], 'unavailable', name)
                self.assertFalse(report[name + '_seen'], name)
            # ...while the agent-owned scratch space works normally.
            self.assertEqual(report['own_scratch'], 'writable')
            self.assertEqual((scratch / 'agent-output.txt').read_text(), 'agent was here')
            guard = subprocess.run(
                [PYTHON, str(ROOT / 'scripts/skillwren.py'), 'guard',
                 str(root / 'policy.json'), '--audit', str(root / 'log'),
                 '--checkpoint', str(root / 'anchor')],
                input='\n'.join(lines[1:]) + '\n',
                text=True, capture_output=True, timeout=120)
            self.assertEqual(guard.returncode, 0, guard.stderr)
            outcomes = [json.loads(line) for line in guard.stdout.splitlines()]
            self.assertFalse(outcomes[0]['ok'])
            self.assertTrue(outcomes[1]['ok'] and outcomes[2]['ok'])
            self.assertEqual(target.read_text(), '{"debug": false}')
            store = AuditStore(root / 'log', root / 'anchor')
            self.assertEqual(store.records[-1]['type'], 'stop')
            self.assertNotIn('debug', (root / 'log').read_text())
