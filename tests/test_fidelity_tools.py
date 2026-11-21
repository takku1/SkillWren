"""Fidelity benchmark tooling: the answer key is bound to its bytes, quotes are verified,
judgments are routed to a human, and requirement-to-enforcement mapping is conservative."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "lab"))
sys.path.insert(0, str(ROOT / "src"))
import fidelity_freeze  # noqa: E402
import fidelity_score  # noqa: E402
from skillwren.coverage import requirement_tiers  # noqa: E402

SOURCE = "# Demo\n\nRead the config first. Never write outside build/. Ask before deleting.\n"


def bench(tmp, line):
    base = Path(tmp)
    (base / "sources" / "demo").mkdir(parents=True)
    (base / "review").mkdir()
    (base / "sources" / "demo" / "SKILL.md").write_text(SOURCE, encoding="utf-8")
    (base / "review" / "demo.md").write_text(
        "# Requirement review: demo\n\nSource: sources/demo/SKILL.md\nReviewed by: Ada\nDate: 2026-11-20\n"
        "Candidate status: AI-drafted.\n\n" + line + "\n", encoding="utf-8")
    return base


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FidelityToolTests(unittest.TestCase):
    def test_multi_span_quote_needs_every_span_verbatim(self):
        good = '- [x] DM-1 | ordering | Read config, then ask. | "Read the config first. ... Ask before deleting."'
        bad = '- [x] DM-1 | ordering | Read config, then ask. | "Read the config first. ... Ask before removing."'
        for line, ok in ((good, True), (bad, False)):
            with tempfile.TemporaryDirectory() as tmp, mock.patch.object(fidelity_freeze, "BENCH", bench(tmp, line)):
                _, items, problems = fidelity_freeze.parse(fidelity_freeze.BENCH / "review" / "demo.md")
                self.assertEqual(not problems, ok, problems)

    def test_freeze_records_digests_and_provenance(self):
        line = '- [x] DM-1 | prohibition | Never write outside build/. | "Never write outside build/."'
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(fidelity_freeze, "BENCH", bench(tmp, line)):
            self.assertEqual(fidelity_freeze.main([]), 0)
            frozen = json.loads((fidelity_freeze.BENCH / "frozen" / "demo.json").read_text(encoding="utf-8"))
            self.assertEqual(frozen["source_sha256"], sha(fidelity_freeze.BENCH / "sources" / "demo" / "SKILL.md"))
            self.assertEqual(frozen["candidate_provenance"], "AI-drafted.")
            self.assertEqual(frozen["reviewed_by"], "Ada")

    def test_scorer_refuses_a_source_or_review_changed_since_freezing(self):
        line = '- [x] DM-1 | prohibition | Never write outside build/. | "Never write outside build/."'
        with tempfile.TemporaryDirectory() as tmp:
            base = bench(tmp, line)
            with mock.patch.object(fidelity_freeze, "BENCH", base), \
                    mock.patch.object(fidelity_score, "BENCH", base):
                fidelity_freeze.main([])
                source, reqs, basis = fidelity_score.requirements("demo", candidates=False)
                self.assertEqual([r["id"] for r in reqs], ["DM-1"])
                self.assertIn("reviewed by Ada", basis)
                for changed in (base / "sources" / "demo" / "SKILL.md", base / "review" / "demo.md"):
                    original = changed.read_bytes()
                    changed.write_bytes(original + b"\nAn edit after freezing.\n")
                    with self.assertRaises(SystemExit) as raised:
                        fidelity_score.requirements("demo", candidates=False)
                    self.assertIn("new benchmark revision", str(raised.exception))
                    changed.write_bytes(original)

    def test_adjudication_lists_only_doubtful_verdicts_and_widening_additions(self):
        result = {"source": "demo", "built": "b.md", "judge": "model (sonnet)", "basis": "frozen",
                  "requirements": [
                      {"id": "DM-1", "kind": "prohibition", "verdict": "preserved", "judge_verdict": "preserved",
                       "quote": "q", "reason": "r"},
                      {"id": "DM-2", "kind": "ordering", "verdict": "weakened", "judge_verdict": "weakened",
                       "quote": "q2", "reason": "moved later."},
                      {"id": "DM-3", "kind": "obligation", "verdict": "unverified", "judge_verdict": "preserved",
                       "quote": "invented", "reason": "r3"}],
                  "introduced": [{"behavior": "Deletes caches.", "quote": "q", "widens": True},
                                 {"behavior": "Asks twice.", "quote": "q", "widens": False}]}
        sheet = fidelity_score.adjudication(result)
        self.assertNotIn("DM-1", sheet)
        self.assertIn("DM-2", sheet)
        self.assertIn("DM-3", sheet)
        self.assertIn("quote not found", sheet)
        self.assertIn("Deletes caches.", sheet)
        self.assertNotIn("Asks twice.", sheet)

    def test_report_refuses_until_adjudication_is_complete_and_applies_overturns(self):
        import fidelity_report
        result = {"source": "demo", "built": "b.md", "judge": "model (sonnet)",
                  "basis": "frozen, reviewed by Ada on 2026-11-20",
                  "requirements": [
                      {"id": "DM-1", "kind": "prohibition", "verdict": "preserved", "judge_verdict": "preserved",
                       "quote": "q", "reason": "r"},
                      {"id": "DM-2", "kind": "ordering", "verdict": "weakened", "judge_verdict": "weakened",
                       "quote": "q2", "reason": "moved later."}],
                  "introduced": [{"behavior": "Deletes caches.", "quote": "q", "widens": True}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(result), encoding="utf-8")
            sheet = path.with_suffix(".adjudication.md")
            self.assertEqual(fidelity_report.main([str(path)]), 1)  # no sheet yet
            sheet.write_text(fidelity_score.adjudication(result), encoding="utf-8")
            self.assertEqual(fidelity_report.main([str(path)]), 1)  # unmarked lines
            text = sheet.read_text(encoding="utf-8")
            sheet.write_text(text.replace("- [ ] DM-2", "- [!] DM-2").replace("- [ ] Deletes", "- [x] Deletes"),
                             encoding="utf-8")
            out = Path(tmp) / "report.json"
            self.assertEqual(fidelity_report.main([str(path), "--out", str(out)]), 0)
            row = json.loads(out.read_text(encoding="utf-8"))[0]
        self.assertEqual(row["preserved"], "2/2")  # DM-2 overturned to preserved
        self.assertEqual(row["overturned"], 1)
        self.assertEqual(row["widening_introductions"], 1)

    def test_report_refuses_candidate_basis(self):
        import fidelity_report
        result = {"source": "demo", "built": "b.md", "judge": "m", "basis": "candidates (unreviewed, model-drafted)",
                  "requirements": [], "introduced": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.json"
            path.write_text(json.dumps(result), encoding="utf-8")
            path.with_suffix(".adjudication.md").write_text("# Adjudication\n", encoding="utf-8")
            self.assertEqual(fidelity_report.main([str(path)]), 1)

    def test_requirement_mapping_is_conservative(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "SKILL.md"
            skill.write_text("x\nalpha beta\nalpha beta\ngamma\ndelta\n", encoding="utf-8")
            rows = [{"line": 4, "kind": "gate", "tier": "enforced", "why": "w"},
                    {"line": 5, "kind": "write", "tier": "instructed", "why": "w"}]
            score = {"requirements": [
                {"id": "A", "kind": "ordering", "verdict": "preserved", "quote": "alpha beta"},
                {"id": "B", "kind": "ordering", "verdict": "preserved", "quote": "gamma delta"},
                {"id": "C", "kind": "ordering", "verdict": "preserved", "quote": "gamma"},
                {"id": "D", "kind": "ordering", "verdict": "preserved", "quote": "not there"},
            ]}
            got = {r["id"]: r for r in requirement_tiers(skill, rows, score)}
        self.assertEqual(got["A"]["tier"], "ambiguous")  # occurs twice
        self.assertEqual(got["B"]["tier"], "instructed")  # spans enforced + instructed: weakest
        self.assertIn("spans 2 elements", got["B"]["why"])
        self.assertEqual(got["C"]["tier"], "enforced")
        self.assertIn("not proof", got["C"]["why"])
        self.assertEqual(got["D"]["tier"], "ambiguous")


if __name__ == "__main__":
    unittest.main()
