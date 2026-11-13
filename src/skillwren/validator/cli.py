"""`skillwren check`: command-line front end for the validator."""
from pathlib import Path

from .explain import RULE_EXPLAIN
from .files import audit, summarize, validate_files

USAGE = ("usage: skillwren check [--all | [--fragment] [--explain] [--summary] [--audit] <file>...]\n"
         "  --fragment  check logic blocks inside ordinary Markdown (flow files)\n"
         "  --explain   add a plain-language paragraph to each diagnostic\n"
         "  --summary   list each flow's inputs, writes, and runs\n"
         "  --audit     list each gate's evidence class, each branch's controller,\n"
         "              and what each order rule rests on")
FLAGS = ("--explain", "--fragment", "--summary", "--audit")


def _plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def check_all():
    """Check every *.md under the cwd except benchmarks/archive/.

    Prints a one-line summary per file; exit 1 when any file fails."""
    files = sorted(p for p in Path(".").rglob("*.md")
                   if Path("benchmarks/archive") not in p.parents)
    if not files:
        print("no markdown files found")
        return 0
    results = validate_files([str(p) for p in files])
    code = 0
    for p in files:
        errors, warnings = results[str(p)]
        if not errors and not warnings:
            print(f"{p}: clean")
        else:
            print(f"{p}: {_plural(len(errors), 'error')},"
                  f" {_plural(len(warnings), 'warning')}")
        if errors:
            code = 1
    return code


def _print_diags(path, diags, kind, explain):
    for d in sorted(diags, key=lambda x: x.line):
        print(f"{path}:{d.line}: {kind} {d.rule}: {d.msg} -- {d.fix}")
        if explain and d.rule in RULE_EXPLAIN:
            print(f"  {RULE_EXPLAIN[d.rule]}")


def _counts(items):
    tally = {}
    for _line, _text, label in items:
        tally[label] = tally.get(label, 0) + 1
    return ", ".join(f"{n} {label}" for label, n in sorted(tally.items())) or "none"


def _print_summary(path, fragment):
    for flow, facts in summarize(path, fragment=fragment).items():
        print(f"{path}: flow {flow}: inputs {', '.join(facts['inputs']) or '-'};"
              f" writes {', '.join(facts['writes']) or '-'};"
              f" runs {', '.join(facts['runs']) or '-'}")


def _print_audit(path, fragment):
    report = audit(path, fragment=fragment)
    for flow, facts in report["flows"].items():
        print(f"{path}: flow {flow}: gates {_counts(facts['gates'])};"
              f" branches {_counts(facts['branches'])}")
        for line, text, label in facts["gates"]:
            print(f"  {line}: gate [{label}] {text}")
        for line, text, label in facts["branches"]:
            print(f"  {line}: branch [{label}] {text}")
    for rule, classes in report["rules"]:
        print(f"{path}:{rule.line}: order rule {rule.text!r} rests on"
              f" {', '.join(classes) or 'nothing'}")


def main(argv):
    if len(argv) < 3 or argv[1] != "check":
        print(USAGE)
        return 2
    args = argv[2:]
    if "--help" in args or "-h" in args:
        print(USAGE)
        return 0
    if "--all" in args:
        return check_all()
    paths = [a for a in args if a not in FLAGS]
    if not paths or any(p.startswith("--") for p in paths):
        print(USAGE)
        return 2
    fragment = "--fragment" in args
    code = 0
    for path, (errors, warnings) in validate_files(paths, fragment=fragment).items():
        _print_diags(path, errors, "error", "--explain" in args)
        _print_diags(path, warnings, "warning", "--explain" in args)
        if errors:
            code = 1
        if "--summary" in args:
            _print_summary(path, fragment)
        if "--audit" in args:
            _print_audit(path, fragment)
    if code == 0:
        print("clean")
    return code
