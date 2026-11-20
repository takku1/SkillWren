"""`skillwren check`: command-line front end for the validator."""
import json
from pathlib import Path

from .explain import RULE_EXPLAIN
from .files import audit, summarize, validate_files

USAGE = ("usage: skillwren check [--json] [--all | [--fragment] [--explain] [--summary] [--audit] <file>...]\n"
         "  --fragment  check logic blocks inside ordinary Markdown (flow files)\n"
         "  --explain   add a plain-language paragraph to each diagnostic\n"
         "  --summary   list each flow's inputs, writes, and runs\n"
         "  --audit     list each gate's evidence class, each branch's controller,\n"
         "              and what each order rule rests on\n"
         "  --json      print one JSON object instead (for tools and repair loops);\n"
         "              includes each file's unbacked verify gates")
FLAGS = ("--explain", "--fragment", "--summary", "--audit", "--json")


def _plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def all_markdown():
    return sorted(p for p in Path(".").rglob("*.md")
                  if Path("benchmarks/archive") not in p.parents)


def check_all():
    """Check every *.md under the cwd except benchmarks/archive/.

    Prints a one-line summary per file; exit 1 when any file fails."""
    files = all_markdown()
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


def _diag_json(diags, explain):
    out = []
    for d in sorted(diags, key=lambda x: x.line):
        item = {"line": d.line, "rule": d.rule, "message": d.msg, "fix": d.fix}
        if explain and d.rule in RULE_EXPLAIN:
            item["explain"] = RULE_EXPLAIN[d.rule]
        out.append(item)
    return out


def _unbacked(path, fragment):
    from .evidence import unbacked_verifies
    try:
        return unbacked_verifies(path, fragment=fragment)
    except Exception:  # unreadable or unparseable: the diagnostics say why
        return []


def check_json(paths, fragment, args):
    """Machine-readable check result: one object, exit code as for text."""
    explain = "--explain" in args
    files = {}
    for path, (errors, warnings) in validate_files(paths, fragment=fragment).items():
        entry: dict = {"errors": _diag_json(errors, explain),
                 "warnings": _diag_json(warnings, explain),
                 "unbacked_verifies": _unbacked(path, fragment)}
        if "--summary" in args:
            entry["summary"] = summarize(path, fragment)
        if "--audit" in args:
            report = audit(path, fragment)
            entry["audit"] = {
                "flows": {flow: {kind: [{"line": line, "text": text, "class": label}
                                        for line, text, label in facts[kind]]
                                 for kind in ("gates", "branches")}
                          for flow, facts in report["flows"].items()},
                "rules": [{"line": rule.line, "rule": rule.text, "rests_on": list(classes)}
                          for rule, classes in report["rules"]]}
        files[path] = entry
    ok = not any(entry["errors"] for entry in files.values())
    print(json.dumps({"format": "skillwren-check-1", "fragment": fragment,
                      "ok": ok, "files": files}, indent=2))
    return 0 if ok else 1


def main(argv):
    if len(argv) < 3 or argv[1] != "check":
        print(USAGE)
        return 2
    args = argv[2:]
    if "--help" in args or "-h" in args:
        print(USAGE)
        return 0
    if "--all" in args:
        if "--json" in args:
            return check_json([str(p) for p in all_markdown()], "--fragment" in args, args)
        return check_all()
    paths = [a for a in args if a not in FLAGS]
    if not paths or any(p.startswith("--") for p in paths):
        print(USAGE)
        return 2
    fragment = "--fragment" in args
    if "--json" in args:
        return check_json(paths, fragment, args)
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
