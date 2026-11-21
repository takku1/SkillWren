"""Deterministic I7 probe: which landed statements satisfy which demanded evidence.

Runs the unchanged checker (`inventory.check_landing`) on small candidates
shaped like the round 1/2 refusals and on counterexamples. No model calls.

    py -3 docs/current/research/fidelity-benchmark/i7-investigation/probe_i7.py
"""
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "src"))
from skillwren import inventory as inv  # noqa: E402

HEAD = """---
name: probe
description: I7 probe candidate.
---

# Probe

```logic
probe:
{body}
  return result as result
```
"""

CASES = [
    # (case id, evidence tag, kind, logic body, anchors, what it shows)
    ("IC-read-effect", "effect", "effect",
     "  read examples/3p-updates.md as guideline\n  apply follow guideline with guideline as result",
     ["read examples/3p-updates.md as guideline"],
     "internal-comms shape: loading a file, tagged effect, lands on a read"),
    ("IC-read-exec-verify", "exec", "gate",
     "  read examples/3p-updates.md as guideline\n"
     "  verify #loaded guideline is the 3P format from guideline\n"
     "    otherwise:\n      abort with \"No guideline.\"\n"
     "  apply follow guideline with guideline as result",
     ["read examples/3p-updates.md as guideline",
      "verify #loaded guideline is the 3P format from guideline"],
     "same step tagged exec: a verify citing the read result already counts"),
    ("IC-read-self", "self", "effect",
     "  read examples/3p-updates.md as guideline\n  apply follow guideline with guideline as result",
     ["read examples/3p-updates.md as guideline"],
     "same step tagged self: no evidence demanded"),
    ("IC-invented-exec", "effect", "effect",
     "  read examples/3p-updates.md as guideline\n"
     "  exec guideline load check from checks as loaded\n"
     "  verify #loaded the guideline was loaded from loaded\n"
     "    otherwise:\n      abort with \"No guideline.\"\n"
     "  apply follow guideline with guideline as result",
     ["read examples/3p-updates.md as guideline", "exec guideline load check from checks as loaded",
      "verify #loaded the guideline was loaded from loaded"],
     "round 2 repair shape: an invented exec check does not satisfy an effect tag"),
    ("IC-invented-write", "effect", "effect",
     "  read examples/3p-updates.md as guideline\n  write #copy guideline with notes\n"
     "  apply follow guideline with guideline as result",
     ["read examples/3p-updates.md as guideline", "write #copy guideline with notes"],
     "the only way past an effect tag: invent a write the source never asked for"),
    ("CR-show-effect", "effect", "effect",
     "  apply report assembly with verdict as result\n  show result",
     ["apply report assembly with verdict as result", "show result"],
     "code-reviewer shape: the report is shown to the user, tagged effect"),
    ("CR-invented-write", "effect", "effect",
     "  apply report assembly with verdict as result\n  write #report result with review_file\n  show result",
     ["apply report assembly with verdict as result", "write #report result with review_file"],
     "passes only by saving the report to a file the source never names"),
    ("CR-output-in-prose", "effect", "output",
     "  apply report assembly with verdict as result\n  show result",
     ["# Probe"],
     "code-reviewer R26 shape: an output requirement lands in prose, as the lowering prompt says"),
    ("TF-show-effect", "effect", "effect",
     "  show theme_showcase\n  apply theme choice with theme_showcase as result",
     ["show theme_showcase"],
     "theme-factory shape: display a PDF unmodified, tagged effect"),
    # Counterexamples: I7 must keep firing.
    ("X-exec-self-report", "exec", "gate",
     "  verify #tests the test suite passes\n    otherwise:\n      abort with \"Tests fail.\"\n"
     "  apply merge with change as result",
     ["verify #tests the test suite passes"],
     "source: run the tests and do not merge unless they pass; built: a self-reported verify"),
    ("X-effect-lost", "effect", "effect",
     "  apply migration plan with change as plan\n  apply migration with plan as result",
     ["apply migration plan with change as plan"],
     "source: save the plan to docs/plan.md before migrating; built: the plan is never written"),
    ("X-user-lost", "user", "decision",
     "  apply approval judgment with change as approval\n  apply deploy with approval as result",
     ["apply approval judgment with change as approval"],
     "source: the owner approves before deploy; built: the model decides approval itself"),
]


def run(case):
    ident, evidence, kind, body, anchors, _ = case
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "SKILL.md"
        path.write_text(HEAD.format(body=body), encoding="utf-8")
        candidate = inv.Candidate(path)
        inventory = {"requirements": [{"id": "R1", "kind": kind, "evidence": evidence,
                                       "text": ident, "lands": anchors}]}
        findings = inv.check_landing(inventory, candidate)
        classes = sorted({h.cls for a in anchors for h in candidate.resolve(a)})
    return [f["rule"] for f in findings], classes


if __name__ == "__main__":
    print(f"{'case':22} {'tag':7} {'landed classes':28} findings")
    for case in CASES:
        rules, classes = run(case)
        print(f"{case[0]:22} {case[1]:7} {','.join(classes):28} {','.join(rules) or 'pass'}")
