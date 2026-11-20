"""Enforcement closure probe, scripted rows (no model, no container): every attack through
the guard is denied, and the same-account paths around it succeed (closure is the host's job)."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "lab"))
sys.path.insert(0, str(ROOT / "src"))
import closure_probe  # noqa: E402


class ClosureProbeTests(unittest.TestCase):
    def test_through_the_guard_every_attack_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = closure_probe.through_guard(Path(tmp))
        self.assertEqual(len(rows), 7)
        failed = [r for r in rows if not r["as_expected"]]
        self.assertEqual(failed, [], failed)

    def test_around_the_guard_in_one_account_closure_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = closure_probe.around_guard(Path(tmp))
        self.assertTrue(all(r["as_expected"] for r in rows), rows)
        direct = rows[0]
        self.assertIn("enforced", direct["coverage_label"])
        self.assertIn("only through the guard", direct["coverage_label"])


if __name__ == "__main__":
    unittest.main()
