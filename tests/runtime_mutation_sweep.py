"""Mutation tripwire for the trusted controller's security decisions."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = {
    'allow-unverified': ('if approval != binding:', 'if False:'),
    'permit-replay': ('approval = self.approvals.pop(name, None)', 'approval = self.approvals.get(name)'),
    'ignore-target-version': ('binding = (digest(data), file_digest(target))', 'binding = (digest(data), None)'),
    'ignore-verifier-pin': ('file_digest(path) != expected', 'False'),
    'retain-failed-evidence': ('self.approvals.pop(name, None)\n                # Verifiers', 'self.approvals.get(name)\n                # Verifiers'),
}
results = []
for name, (old, new) in MUTATIONS.items():
    with tempfile.TemporaryDirectory(prefix='skillwren-mutant-') as directory:
        root = Path(directory)
        for folder in ('src', 'scripts', 'examples'):
            shutil.copytree(ROOT / folder, root / folder, ignore=shutil.ignore_patterns('__pycache__', '*.egg-info'))
        (root / 'tests').mkdir()
        shutil.copy2(ROOT / 'tests/test_guard.py', root / 'tests/test_guard.py')
        path = root / 'src/skillwren/guard.py'
        source = path.read_text()
        if source.count(old) != 1:
            raise ValueError('mutation location drift: ' + name)
        path.write_text(source.replace(old, new, 1))
        proc = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_guard.py', '-q'],
                              cwd=root, capture_output=True, text=True, timeout=60)
        # A syntax/import failure is not a valid kill.
        killed = proc.returncode != 0 and 'FAILED (' in proc.stderr and 'SyntaxError' not in proc.stderr
        results.append({'mutant': name, 'killed': killed, 'output_tail': proc.stderr[-1800:]})
print(json.dumps(results, indent=2))
raise SystemExit(0 if all(item['killed'] for item in results) else 1)
