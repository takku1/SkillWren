"""Fragment-set packaging (`build DIR`) and directory measurement (`measure DIR`)."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from skillwren.compiler import BuildError, build, expanded_text

GOOD = ROOT / 'examples/host-demo/dep-audit'
BAD = ROOT / 'tests/fixtures/fragments/skill'


class FragmentBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_valid_set_is_packaged_with_manifest(self):
        out = self.root / 'out'
        manifest = build(GOOD, out)
        self.assertEqual(manifest['mode'], 'fragments')
        self.assertIn('flow.md', manifest['checked_fragments'])
        self.assertIn('SKILL.inline.md', manifest['checked_fragments'])
        self.assertEqual((out / 'flow.md').read_bytes(), (GOOD / 'flow.md').read_bytes())
        recorded = json.loads((out / 'manifest.json').read_text())
        self.assertEqual(recorded['sources']['check_deps.py']['bytes'],
                         (GOOD / 'check_deps.py').stat().st_size)

    def test_invalid_fragment_fails_and_leaves_no_output(self):
        out = self.root / 'out'
        with self.assertRaises(BuildError) as caught:
            build(BAD, out)
        self.assertIn('build-gap.md', str(caught.exception))
        self.assertFalse(out.exists())

    def test_set_without_skill_entry_or_fragments_is_rejected(self):
        bare = self.root / 'bare'
        bare.mkdir()
        (bare / 'notes.md').write_text('# notes\n')
        with self.assertRaises(BuildError):
            build(bare, self.root / 'o1')
        (bare / 'SKILL.md').write_text('---\nname: x\ndescription: y\n---\n')
        with self.assertRaises(BuildError):
            build(bare, self.root / 'o2')

    def test_optimized_options_rejected_for_sets(self):
        with self.assertRaises(BuildError):
            build(GOOD, self.root / 'o', original=GOOD / 'SKILL.md', review=GOOD / 'flow.md')

    def test_expanded_text_counts_every_markdown_file_once(self):
        text = expanded_text(GOOD).decode('utf-8')
        for name in ('SKILL.md', 'flow.md', 'SKILL.prose.md'):
            self.assertEqual(text.count(f'<!-- file: {name} -->'), 1)
        self.assertNotIn('<!-- file: check_deps.py -->', text)

    def test_measure_accepts_directories(self):
        smaller = self.root / 'smaller'
        shutil.copytree(GOOD, smaller)
        for name in ('SKILL.prose.md', 'SKILL.logic.md', 'SKILL.inline.md'):
            (smaller / name).unlink()
        proc = subprocess.run([sys.executable, str(ROOT / 'scripts/skillwren.py'), 'measure',
                               str(GOOD), str(smaller), '--metric', 'characters', '--json'],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertTrue(report['accepted'])
        self.assertLess(report['compiled']['count'], report['original']['count'])


if __name__ == '__main__':
    unittest.main()
