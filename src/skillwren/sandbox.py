"""Offline container effect observer; final snapshots do not see transient writes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
from .conform import snapshot, undeclared


def run(image, workspace, argv, allowed=(), timeout=60):
    if '@sha256:' not in image:
        raise ValueError('pin the container image by digest')
    if not argv:
        raise ValueError('a command is required after --')
    with tempfile.TemporaryDirectory(prefix='skillwren-sandbox-') as directory:
        work = Path(directory) / 'work'
        shutil.copytree(workspace, work, symlinks=True, ignore=shutil.ignore_patterns('.git'))
        if any(path.is_symlink() for path in work.rglob('*')):
            raise ValueError('workspace symlinks are not supported')
        before = snapshot(work)
        name = 'skillwren-' + uuid.uuid4().hex
        user = f'{os.getuid()}:{os.getgid()}' if hasattr(os, 'getuid') else '65534:65534'
        command = ['docker', 'run', '--rm', '--name', name, '--network=none', '--read-only',
                   '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64',
                   '--memory=256m', '--cpus=1', '--user=' + user,
                   '--tmpfs=/tmp:rw,noexec,nosuid,size=64m',
                   '--mount', f'type=bind,source={work},target=/work', '--workdir=/work', image, *argv]
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        finally:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=15)
        after = snapshot(work)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        violations = undeclared(changed, allowed)
        return {'ok': proc.returncode == 0 and not violations, 'exit': proc.returncode,
                'changed': changed, 'undeclared': violations, 'stdout': proc.stdout[-2000:],
                'stderr': proc.stderr[-2000:], 'image': image,
                'observation': 'final state only; transient writes inside /work and /tmp not observed'}


def main(argv):
    parser = argparse.ArgumentParser(prog='skillwren sandbox')
    parser.add_argument('--image', required=True)
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--allow', action='append', default=[])
    parser.add_argument('--timeout', type=float, default=60)
    command = []
    if '--' in argv:
        cut = argv.index('--')
        argv, command = argv[:cut], argv[cut + 1:]
    args = parser.parse_args(argv)
    try:
        if not 0 < args.timeout <= 3600:
            raise ValueError('timeout must be in (0, 3600]')
        report = run(args.image, args.workspace, command, args.allow, args.timeout)
        print(json.dumps(report, indent=2))
        return 0 if report['ok'] else 1
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2
