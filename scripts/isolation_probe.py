"""Real container isolation probes; no host mounts and no model/API calls."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

PYTHON = str(Path(sys.executable).resolve())
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.guard import Controller, Denied, file_digest

IMAGE = 'python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b'
PROBE = r'''
import json, pathlib, socket
checks = {}
for name, path in [('root_write', '/unauthorized'), ('protected_write', '/protected/sensitive.json')]:
    try:
        pathlib.Path(path).write_text('bypass')
        checks[name] = False
    except OSError:
        checks[name] = True
checks['docker_socket_absent'] = not pathlib.Path('/var/run/docker.sock').exists()
try:
    socket.create_connection(('1.1.1.1', 443), timeout=1).close()
    checks['network_denied'] = False
except OSError:
    checks['network_denied'] = True
print(json.dumps(checks))
print(json.dumps({'action':'write','operation':'write#config','content':'{"debug": false}'}))
print(json.dumps({'action':'verify','operation':'write#config','content':'{"debug": false}'}))
print(json.dumps({'action':'write','operation':'write#config','content':'{"debug": false}'}))
'''

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output')
    args = parser.parse_args()
    command = ['docker', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=ALL',
               '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=128m',
               '--cpus=1', '--user=65534:65534', IMAGE, 'python', '-I', '-c', PROBE]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90, check=True)
    lines = result.stdout.splitlines()
    probes = json.loads(lines[0])
    assert all(probes.values()), probes
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / 'sensitive.json'
        script = str(ROOT / 'examples/guard/verify_config.py')
        controller = Controller({'version': 1, 'operations': {'write#config': {
            'target': str(target), 'argv': [PYTHON, '-I', script],
            'pins': {PYTHON: file_digest(PYTHON), script: file_digest(script)}, 'timeout': 5}}})
        outcomes = []
        for line in lines[1:]:
            try:
                outcomes.append(controller.handle(json.loads(line)))
            except Denied as error:
                outcomes.append({'denied': str(error)})
        assert 'denied' in outcomes[0]
        assert 'verified' in outcomes[1] and 'written' in outcomes[2]
        assert target.read_text() == '{"debug": false}'
    report = {'kind': 'container mechanism test, not a model benchmark', 'image': IMAGE,
              'probes': probes, 'requests': outcomes}
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    run()

