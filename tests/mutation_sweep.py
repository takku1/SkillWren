"""Mutation sweep (alpha): kill matrix for the mutant catalog.

Usage:
  python3 tests/mutation_sweep.py [--base NAME] [--mutant NAME] [--show-miss]

Runs every catalog mutant against its declared bases. Beta-misses (a
mutant validates clean) exit 1: a survivor is always a validator hole or
a bad mutant. Alpha-deviations (killed without an expected rule) are
reported but advisory here; the committed tripwire gates alpha.
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import skillwren
from mutation_catalog import BASES, MUTANTS


def validate_text(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(text)
        case = f.name
    try:
        return skillwren.validate_file(case)
    finally:
        Path(case).unlink()


def main(argv):
    only_base = None
    only_mutant = None
    show_miss = False
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == "--base":
            only_base = args.pop(0)
        elif arg == "--mutant":
            only_mutant = args.pop(0)
        elif arg == "--show-miss":
            show_miss = True
        else:
            print(f"unknown arg: {arg}")
            return 2

    texts = {b: (ROOT / rel).read_text() for b, rel in BASES.items()}
    misses = []
    deviations = []
    cells = []
    for mutant in MUTANTS:
        if only_mutant and mutant["name"] != only_mutant:
            continue
        for base, edit in mutant["edits"].items():
            if only_base and base != only_base:
                continue
            errors, _ = validate_text(edit(texts[base]))
            rules = sorted({d.rule for d in errors})
            if not errors:
                cells.append((mutant["name"], base, "SURVIVED"))
                misses.append((mutant["name"], base, edit(texts[base])))
            elif mutant["rules"] & set(rules):
                cells.append((mutant["name"], base, "kill " + ",".join(rules)))
            else:
                cells.append((mutant["name"], base,
                              "kill " + ",".join(rules) + "  <-- ALPHA?"))
                deviations.append((mutant["name"], base, rules))

    width = max(len(name) for name, _, _ in cells)
    for name, base, result in cells:
        print(f"{name:<{width}}  {base:<8}  {result}")
    print(f"\n{len(cells)} mutants, "
          f"{len(misses)} beta-misses, {len(deviations)} alpha-deviations")
    for name, base, rules in deviations:
        expected = next(m["rules"] for m in MUTANTS if m["name"] == name)
        print(f"  alpha: {name} on {base}: expected {sorted(expected)}, "
              f"got {rules}")
    if show_miss:
        for name, base, text in misses:
            print(f"\n--- survivor: {name} on {base} ---\n{text}")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
