"""Tier 2 for the 2026-11-19 field response: code mutants of the new checks.

Each mutant disables one decision in the implementation (exclusion
analysis, ledger exclusions, package provenance, the shared grammar). The
mutant must be killed by the tier-1 suite: a survivor means a test is
missing, not that the feature works.

    py -3 tests/field_mutation_sweep.py        (exit 1 on any survivor)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ["test_field_2026_11_19.py", "test_guard_workflow.py", "test_mutations.py",
         "mutation_catalog.py", "test_guard_skill_load.py", "test_coverage.py",
    "test_fidelity_tools.py"]

# name -> (file, old, new). Each `old` must occur exactly once.
MUTANTS = {
    # Finding 5, static
    "exclusion-must-not-may": ("src/skillwren/validator/exclusion.py",
                               "new_in = set().union(*(out_facts[p] for p in preds[node] if p in reach))",
                               "new_in = set.intersection(*(out_facts[p] for p in preds[node] if p in reach))"),
    "exclusion-ignore-callee-later": ("src/skillwren/validator/exclusion.py",
                                      "return bool(target) and summaries.may_start(*target, pattern)",
                                      "return False"),
    "exclusion-not-exported": ("src/skillwren/validator/exclusion.py",
                               "rules += summaries.exported(*target)", "pass"),
    "exclusion-skip-nested-callees": ("src/skillwren/validator/exclusion.py",
                                      "                found += self.exported(callee, target)",
                                      "                pass"),
    "exclusion-never-parsed-as-before": ("src/skillwren/validator/document.py",
                                         'if body.startswith("never "):', "if False:"),
    "exclusion-no-coverage-warning": ("src/skillwren/validator/files.py",
                                      "               if k not in exclusions_seen]",
                                      "               if False]"),
    "exclusion-hint-generic": ("src/skillwren/validator/exclusion.py",
                               "return min(found, key=lambda n: n.line) if found else None",
                               "return None"),
    "prose-composition-ignored": ("src/skillwren/validator/exclusion.py",
                                  "            if not (other.readable and other.contract and other.contract.exclusions):",
                                  "            if True:"),
    "guard-exclusion-unenforced": ("src/skillwren/guard.py",
                                   "            if first in self.operations and then in self.operations:",
                                   "            if False:"),
    "guard-failed-check-not-run": ("src/skillwren/guard.py",
                                   "                self.ran.add(name)\n                self._run_verifier(op, data)",
                                   "                self._run_verifier(op, data)\n                self.ran.add(name)"),
    # Finding 6, host-load record
    "hostload-record-ignored": ("src/skillwren/ledger.py",
                                "    load = latest_load(loads_file, package[\"name\"], before)",
                                "    load = None"),
    "hostload-project-before-personal": ("src/skillwren/hostload.py",
                                         "        found.append(home / \".claude\" / \"skills\" / skill)\n        for directory in [cwd, *cwd.parents]:\n            found.append(directory / \".claude\" / \"skills\" / skill)",
                                         "        for directory in [cwd, *cwd.parents]:\n            found.append(directory / \".claude\" / \"skills\" / skill)\n        found.append(home / \".claude\" / \"skills\" / skill)"),
    # Skill-load assurance (SPEC 24)
    "skill-load-unchecked": ("src/skillwren/guard.py",
                             "            self._check_skill_load()\n            if 'target' not in op:",
                             "            if 'target' not in op:"),
    "skill-load-no-commit-recheck": ("src/skillwren/guard.py",
                                     "            # while this request ran (dpcc monitor, approval check) denies.\n            self._check_skill_load()",
                                     "            pass"),
    "skill-load-run-ignored": ("src/skillwren/guard.py",
                               "            if record.get('session') != self.run_id:",
                               "            if False:"),
    "skill-load-name-ignored": ("src/skillwren/guard.py",
                                "            if name in (record.get('skill'), record.get('name')):",
                                "            if True:"),
    "skill-load-tree-ignored": ("src/skillwren/guard.py",
                                "            if digests != {expected}:",
                                "            if False:"),
    "skill-load-ambiguity-flag-trusted": ("src/skillwren/guard.py",
                                          "            if record.get('ambiguous') is not False or len(digests) != 1:",
                                          "            if record.get('ambiguous') is True:"),
    "skill-load-malformed-skipped": ("src/skillwren/guard.py",
                                     "            except ValueError:\n                raise Denied('skill load records malformed')",
                                     "            except ValueError:\n                continue"),
    "skill-load-run-id-optional": ("src/skillwren/guard.py",
                                   "        if not isinstance(run_id, str) or not run_id.strip():",
                                   "        if False:"),
    "hostload-out-ignored": ("src/skillwren/hostload.py",
                             '    out = Path(out) if out else cwd / ".skillwren" / LOADS',
                             '    out = cwd / ".skillwren" / LOADS'),
    "hostload-package-ignored": ("src/skillwren/hostload.py",
                                 "([Path(package)] if package else candidates(skill, cwd, home))",
                                 "candidates(skill, cwd, home)"),
    "package-identity-eol-sensitive": ("src/skillwren/compiler.py",
                                       'return data if b"\\0" in data else data.replace(b"\\r\\n", b"\\n")',
                                       "return data"),
    # Enforcement coverage (0.13): never claim "enforced" without the guard's own conditions
    "coverage-ignores-binding": ("src/skillwren/coverage.py",
                                 "guarded = bound and first in ops", "guarded = first in ops"),
    "coverage-self-counts-as-evidence": ("src/skillwren/coverage.py",
                                         'outside = sorted(set(classes) - {"self"})',
                                         "outside = sorted(set(classes))"),
    "coverage-no-prerequisites": ("src/skillwren/coverage.py",
                                  "            if op in prerequisites:", "            if False:"),
    "coverage-unmediated-write-enforced": ("src/skillwren/coverage.py",
                                           '            if bound and op in ops and "target" in ops[op]:',
                                           "            if True:"),
    "coverage-write-ignores-binding": ("src/skillwren/coverage.py",
                                       '            if bound and op in ops and "target" in ops[op]:',
                                       '            if op in ops and "target" in ops[op]:'),
    "coverage-unmatched-rule-instructed": ("src/skillwren/coverage.py",
                                           "        if not classes:\n            return \"unverifiable\"",
                                           "        if False:\n            return \"unverifiable\""),
    # Fidelity benchmark integrity (revision 3, external review)
    "fidelity-digest-unchecked": ("scripts/lab/fidelity_score.py",
                                  "        if actual != data[key]:", "        if False:"),
    "fidelity-multispan-unchecked": ("scripts/lab/fidelity_freeze.py",
                                     'any(norm(span) not in body for span in quote[1:-1].split(" ... "))',
                                     'norm(quote[1:-1].split(" ... ")[0]) not in body'),
    "coverage-span-strongest": ("src/skillwren/coverage.py",
                                "            weakest = max(hits, key=lambda r: TIERS.index(r[\"tier\"]))",
                                "            weakest = min(hits, key=lambda r: TIERS.index(r[\"tier\"]))"),
    "coverage-duplicate-quote-accepted": ("src/skillwren/coverage.py",
                                          "        if at < 0 or flat.find(quote, at + 1) >= 0:",
                                          "        if at < 0:"),
    # Finding 5, ledger
    "ledger-exclusions-ignored": ("src/skillwren/ledger.py",
                                  "    excluded = any(r[\"violations\"] for r in report[\"exclusions\"])",
                                  "    excluded = False"),
    "ledger-attempts-ignored": ("src/skillwren/ledger.py",
                                'events = [r for r in records[1:] if r.get("type") in ("step", "attempt")]',
                                'events = [r for r in records[1:] if r.get("type") == "step"]'),
    # Finding 6
    "package-mismatch-tolerated": ("src/skillwren/ledger.py",
                                   "    if report[\"package_consistent\"] is False:\n        report[\"ok\"] = False",
                                   "    if False:\n        report[\"ok\"] = False"),
    "package-unrecorded-trusted": ("src/skillwren/ledger.py",
                                   '"match": recorded is not None and recorded == actual}',
                                   '"match": recorded is None or recorded == actual}'),
    "package-markdown-only": ("src/skillwren/compiler.py",
                              "        if name == \"manifest.json\":\n            continue",
                              "        if name == \"manifest.json\" or not name.endswith(\".md\"):\n            continue"),
    "package-flow-copy-unchecked": ("src/skillwren/ledger.py",
                                    "if _digest_bytes(identity_bytes(copy)) != _digest_bytes(identity_bytes(flow_file.read_bytes())):",
                                    "if False:"),
    # Finding 8
    "grammar-renderer-drift": ("src/skillwren/validator/workflow.py",
                               "    return statement_id(text)",
                               "    return re.findall(r\"#[A-Za-z][\\w-]*\", text)"),
    # A ledger-only drift (`[A-Za-z]+#\w+` in step_matches) is an equivalent
    # mutant: the prefix fallback already matches any step the typed branch
    # would, so no test can kill it. Recorded in the tier report.
    "grammar-shared-id-loosened": ("src/skillwren/validator/refs.py",
                                   'ID = r"[a-z][a-z0-9-]*"',
                                   'ID = r"[A-Za-z][\\w-]*"'),
}


def run(name, rel, old, new):
    with tempfile.TemporaryDirectory(prefix="skillwren-field-mutant-") as directory:
        root = Path(directory)
        for folder in ("src", "examples", "docs/current/research/lifecycle", "scripts/lab"):
            shutil.copytree(ROOT / folder, root / folder,
                            ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
        shutil.copytree(ROOT / "tests/fixtures", root / "tests/fixtures")
        for test in TESTS:
            shutil.copy2(ROOT / "tests" / test, root / "tests" / test)
        path = root / rel
        source = path.read_text(encoding="utf-8")
        if source.count(old) != 1:
            raise ValueError(f"mutation location drift: {name}")
        text = source.replace(old, new, 1)
        if "re.f" in new and "\nimport re\n" not in text:
            text = "import re\n" + text
        path.write_text(text, encoding="utf-8")
        # unittest, not pytest: CI installs nothing beyond the standard library.
        try:
            proc = subprocess.run([sys.executable, "-m", "unittest", "-q", "test_field_2026_11_19",
                                   "test_guard_workflow", "test_mutations",
                                   "test_guard_skill_load", "test_coverage", "test_fidelity_tools"],
                                  cwd=root / "tests", capture_output=True, text=True, timeout=300,
                                  env={**os.environ, "PYTHONPATH": str(root / "src")})
        except subprocess.TimeoutExpired:
            # A hang is not a kill: report it as a survivor and keep sweeping.
            return {"mutant": name, "killed": False, "tail": ["TIMEOUT after 300 s"]}
        out = proc.stdout + proc.stderr
        # A syntax or import failure is not a valid kill: the mutant never ran.
        broken = any(word in out for word in ("SyntaxError", "ImportError",
                                              "ModuleNotFoundError"))
        killed = proc.returncode != 0 and "FAILED (" in out and not broken
        return {"mutant": name, "killed": killed, "tail": out.strip().splitlines()[-1:]}


def main():
    results = [run(name, *spec) for name, spec in MUTANTS.items()]
    for r in results:
        print(f"{r['mutant']:36} {'killed' if r['killed'] else 'SURVIVED'}  {r['tail'][0] if r['tail'] else ''}")
    survivors = [r["mutant"] for r in results if not r["killed"]]
    print(json.dumps({"mutants": len(results), "killed": len(results) - len(survivors),
                      "survivors": survivors}))
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
