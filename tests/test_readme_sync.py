"""The README's evidence and status summary must not lag the release.

External review of 0.9.0 found the README still titled v0.7, claiming the
model A/B/C runs were pending, and quoting stale test counts. These checks
fail the build when the top-level summary drifts from release metadata.
"""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import skillwren
from skillwren.cli import COMMANDS

README = (ROOT / 'README.md').read_text(encoding='utf-8')
CHANGELOG = (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8')


class ReadmeSyncTests(unittest.TestCase):
    def test_status_names_the_package_version(self):
        self.assertIn(f'v{skillwren.__version__} (', README)

    def test_changelog_top_release_is_the_package_version(self):
        released = re.findall(r'^## (\d+\.\d+\.\d+) ', CHANGELOG, re.M)
        self.assertEqual(released[0], skillwren.__version__)

    def test_title_carries_no_version(self):
        title = README.splitlines()[0]
        self.assertIsNone(re.search(r'v?\d+\.\d+', title), title)

    def test_no_hard_coded_test_counts(self):
        self.assertIsNone(re.search(r'\b\d{2,4} tests\b', README))

    def test_every_cli_command_is_documented(self):
        for command in COMMANDS:
            self.assertIn(f'`{command}`', README, command)

    def test_no_stale_pending_claims(self):
        for phrase in ('pending a provider', 'arms are pending', 'unreleased'):
            self.assertNotIn(phrase, README.lower(), phrase)


if __name__ == '__main__':
    unittest.main()
