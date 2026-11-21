"""Publish a fidelity comparison only after the human adjudication is complete.

    py -3 scripts/lab/fidelity_report.py RESULT.json [RESULT.json ...] [--coverage COV.json ...] [--out FILE]

Each RESULT.json is a `fidelity_score.py --out` result; beside it must lie its adjudication
sheet (same name, `.adjudication.md`, from `--adjudication`). The report refuses while any
sheet line is unmarked: every doubtful verdict and every widening introduction needs a human
mark first, `[x]` agree or `[!]` overturn (with a reason). An overturned requirement verdict
counts as the opposite (preserved becomes not preserved, and the reverse); an overturned
widening introduction is dropped. Results must use frozen ground truth, not candidates.

`--coverage` adds enforcement tiers from `skillwren coverage --fidelity --json`, with
`ambiguous` mappings reported in their own column, never as enforcement failures.
"""
import argparse
import json
from pathlib import Path
import re
import sys

MARK = re.compile(r"^- \[(.)\] (\S+)")


def adjudicated(result_path):
    """(result with human marks applied, problems)."""
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    sheet = Path(result_path).with_suffix(".adjudication.md")
    problems = []
    if not result["basis"].startswith("frozen"):
        problems.append(f"{result_path}: scored against {result['basis']}; publish only frozen ground truth")
    if not sheet.is_file():
        return result, problems + [f"{sheet}: adjudication sheet missing (fidelity_score.py --adjudication)"]
    overturned_ids, overturned_intro, section = set(), set(), "requirements"
    for number, line in enumerate(sheet.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## Introduced"):
            section = "introduced"
        m = MARK.match(line)
        if not m:
            continue
        mark, first = m.groups()
        if mark not in ("x", "!"):
            problems.append(f"{sheet.name}:{number}: not adjudicated (mark [x] agree or [!] overturn)")
        elif mark == "!":
            if section == "requirements":
                overturned_ids.add(first)
            else:
                overturned_intro.add(line[len("- [!] "):].split(" Quote:")[0].strip())
    for r in result["requirements"]:
        if r["id"] in overturned_ids:
            r["verdict"] = "preserved" if r["verdict"] != "preserved" else "missing"
            r["overturned"] = True
    result["introduced"] = [i for i in result["introduced"] if i["behavior"].strip() not in overturned_intro]
    return result, problems


def row(result, coverage):
    reqs = result["requirements"]
    preserved = sum(r["verdict"] == "preserved" for r in reqs)
    out = {"source": result["source"], "built": result["built"],
           "preserved": f"{preserved}/{len(reqs)}",
           "weakened": sum(r["verdict"] == "weakened" for r in reqs),
           "missing": sum(r["verdict"] in ("missing", "unverified") for r in reqs),
           "overturned": sum(bool(r.get("overturned")) for r in reqs),
           "widening_introductions": sum(i["widens"] for i in result["introduced"])}
    if coverage:
        tiers = [r["tier"] for r in coverage.get("requirements", [])]
        for tier in ("enforced", "recorded", "instructed", "unverifiable", "ambiguous"):
            out[tier] = tiers.count(tier)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("results", nargs="+")
    parser.add_argument("--coverage", nargs="*", default=[], help="one coverage JSON per result, same order")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    rows, problems = [], []
    for k, path in enumerate(args.results):
        result, issues = adjudicated(path)
        problems += issues
        coverage = None
        if k < len(args.coverage):
            data = json.loads(Path(args.coverage[k]).read_text(encoding="utf-8"))
            coverage = next(iter(data.values()))
        rows.append(row(result, coverage))
    if problems:
        print("refusing to report: human adjudication is incomplete or the basis is not frozen")
        for p in problems:
            print(f"  {p}")
        return 1
    text = json.dumps(rows, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
