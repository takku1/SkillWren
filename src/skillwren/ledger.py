"""Run ledger: record what a run did, then check its order rules on the trace.

    skillwren ledger start <flow-file> [--label TEXT] [--dir DIR]
    skillwren ledger exec  <run> --step TEXT [--dir DIR] -- <command> [args...]
    skillwren ledger note  <run> --step TEXT [--artifact PATH]... [--dir DIR]
    skillwren ledger check <run> [--require-evidence] [--json] [--dir DIR]
    skillwren ledger show  <run> [--dir DIR]

`<run>` is the id `start` printed, or `latest`. Records live in
DIR/<run>.jsonl (default `.skillwren/ledger`).

Design (docs/current/research/game-theory-2026-11.md):

- Commitment: `start` records the flow file's sha256 and its `order:` rules
  before any step, so the rules cannot be chosen after seeing the trace;
  `check` reports if the file changed since.
- Evidence classes: `exec` runs the command itself (no shell) and records its
  exit status and output digests: evidence the agent cannot simply assert.
  `note --artifact` records file digests (effect). A bare `note` is a
  self-report and is labelled so.
- Tamper evidence: each record carries the previous record's hash, so an
  edited, inserted, or deleted record breaks the chain on `check`. This makes
  manipulation detectable, not impossible: whoever controls the file can
  rewrite the whole chain.
- Ex post checking suffices when evidence is verifiable (evidence games): a
  required step with no record is a violation, not an unknown.

Exit codes: start/note/show 0 on success; exec returns the command's exit
status; check 0 when every rule holds and the chain is intact, 1 otherwise;
2 for usage or environment errors.
"""
import argparse
import datetime
import hashlib
import json
import secrets
import subprocess
import sys
import time
from pathlib import Path

from .validator.files import Document, looks_like_fragment
from .validator.ordering import matches

DEFAULT_DIR = Path(".skillwren") / "ledger"
TAIL = 2000


class LedgerError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seal(record, prev):
    body = dict(record, prev=prev)
    body.pop("hash", None)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["hash"] = _digest_bytes(((prev or "") + canonical).encode("utf-8"))
    return body


def run_path(directory, run):
    directory = Path(directory)
    if run == "latest":
        runs = sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not runs:
            raise LedgerError(f"no runs in {directory}")
        return runs[-1]
    path = directory / f"{run}.jsonl"
    if not path.is_file():
        raise LedgerError(f"no run {run!r} in {directory}")
    return path


def load(path):
    records = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise LedgerError(f"{path}:{number}: not JSON ({error.msg})")
    if not records or records[0].get("type") != "start":
        raise LedgerError(f"{path}: first record is not a start record")
    return records


def _append(path, record):
    records = load(path)
    sealed = _seal(dict(record, seq=len(records), time=_now()), records[-1].get("hash"))
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(sealed, sort_keys=True) + "\n")
    return sealed


def start(flow_file, directory=DEFAULT_DIR, label=None, required=()):
    flow_file = Path(flow_file)
    if not flow_file.is_file():
        raise LedgerError(f"no flow file {flow_file}")
    fragment = looks_like_fragment(flow_file)
    doc = Document(flow_file, fragment)
    rules = [{"line": r.line, "first": r.first, "then": r.then} for r in doc.contract.order]
    run = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    record = _seal({"type": "start", "seq": 0, "time": _now(), "run": run,
                    "file": str(flow_file), "file_sha256": _digest_file(flow_file),
                    "layout": "fragment" if fragment else "skill", "rules": rules,
                    "label": label, "required": list(required)}, None)
    path = directory / f"{run}.jsonl"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    return run, path, rules


def exec_step(path, step, argv):
    if not argv:
        raise LedgerError("exec needs a command after --")
    began = time.monotonic()
    try:
        proc = subprocess.run(argv, capture_output=True)
        code, out, err, failure = proc.returncode, proc.stdout, proc.stderr, None
    except OSError as error:
        code, out, err, failure = 127, b"", str(error).encode("utf-8"), str(error)
    seconds = round(time.monotonic() - began, 3)
    tail = (out + err)[-TAIL:].decode("utf-8", errors="replace")
    record = {"type": "step", "class": "evidence", "step": step, "argv": list(argv),
              "exit": code, "seconds": seconds, "stdout_sha256": _digest_bytes(out),
              "stderr_sha256": _digest_bytes(err), "output_tail": tail}
    if failure:
        record["error"] = failure
    _append(path, record)
    return code, out, err


def note_step(path, step, artifacts=()):
    digests = {}
    for artifact in artifacts:
        if not Path(artifact).is_file():
            raise LedgerError(f"artifact {artifact} does not exist")
        digests[str(artifact)] = _digest_file(artifact)
    record = {"type": "step", "class": "effect" if digests else "self", "step": step}
    if digests:
        record["artifacts"] = digests
    return _append(path, record)


def verify_chain(records):
    problems, prev = [], None
    for record in records:
        if record.get("prev") != prev:
            problems.append(f"record {record.get('seq')}: chain broken (prev does not match)")
        expected = _seal(record, record.get("prev")).get("hash")
        if record.get("hash") != expected:
            problems.append(f"record {record.get('seq')}: hash does not match its content")
        prev = record.get("hash")
    seqs = [r.get("seq") for r in records]
    if seqs != list(range(len(records))):
        problems.append("records are missing or out of order")
    return problems


def completed(event):
    return event.get("class") != "evidence" or event.get("exit") == 0


def check(path, require_evidence=False):
    records = load(path)
    head = records[0]
    report = {"run": head.get("run"), "file": head.get("file"), "integrity": verify_chain(records),
              "file_changed": None, "rules": [], "steps": len(records) - 1}
    flow_file = Path(head.get("file", ""))
    if flow_file.is_file():
        report["file_changed"] = _digest_file(flow_file) != head.get("file_sha256")
    steps = [r for r in records[1:] if r.get("type") == "step"]
    for rule in head.get("rules", []):
        satisfied, violations, exercised = [], [], False
        for event in steps:
            text = event.get("step", "")
            if matches(rule["then"], text) and not matches(rule["first"], text):
                exercised = True
                if not satisfied:
                    violations.append({"seq": event["seq"], "step": text,
                                       "reason": "earlier step not completed"})
                elif require_evidence and set(satisfied) <= {"self"}:
                    violations.append({"seq": event["seq"], "step": text,
                                       "reason": "earlier step only self-reported"})
            if matches(rule["first"], text) and completed(event):
                satisfied.append(event["class"])
        report["rules"].append({"rule": f"{rule['first']} before {rule['then']}",
                                "line": rule.get("line"), "exercised": exercised,
                                "satisfied_by": sorted(set(satisfied)),
                                "violations": violations})
    report["ok"] = not report["integrity"] and not any(r["violations"] for r in report["rules"])
    report["ordering_valid"] = not any(
        v["reason"] == "earlier step not completed"
        for r in report["rules"] for v in r["violations"])
    report["evidence_valid"] = (not any(
        v["reason"] == "earlier step only self-reported"
        for r in report["rules"] for v in r["violations"])) if require_evidence else None
    required = head.get("required", [])
    report["missing_milestones"] = [name for name in required if not any(
        e.get("step") == name and completed(e)
        and (not require_evidence or e.get("class") != "self") for e in steps)]
    report["execution_complete"] = (
        not report["missing_milestones"] and not report["integrity"]
        if required else None)
    report["ok"] = report["ok"] and not report["missing_milestones"]
    report["outcome"] = ("violations" if report["integrity"] or any(r["violations"] for r in report["rules"])
                         else "incomplete" if not report["execution_complete"] else "complete")
    return report


def _print_check(report):
    print(f"run {report['run']}: {report['steps']} steps, file {report['file']}")
    for problem in report["integrity"]:
        print(f"  integrity: {problem}")
    if report["file_changed"]:
        print("  note: the flow file changed since the run started (rules were committed at start)")
    for rule in report["rules"]:
        basis = ", ".join(rule["satisfied_by"]) or "nothing"
        state = "not exercised" if not rule["exercised"] else f"earlier step from {basis}"
        print(f"  rule (line {rule['line']}) {rule['rule']!r}: {state}")
        if rule["exercised"] and rule["satisfied_by"] == ["self"]:
            print("    warning: the earlier step was only self-reported")
        for v in rule["violations"]:
            print(f"    violation at step {v['seq']} {v['step']!r}: {v['reason']}")
    print(f"ordering_valid={report['ordering_valid']}; execution_complete={report['execution_complete']}")
    for name in report["missing_milestones"]:
        print(f"  missing milestone: {name}")
    print(report["outcome"])


def show(path):
    for record in load(path):
        if record["type"] == "start":
            print(f"{record['seq']:>3} {record['time']} start {record['file']}"
                  f" ({len(record.get('rules', []))} order rules)")
            continue
        status = f"exit {record['exit']}" if record.get("class") == "evidence" else ""
        print(f"{record['seq']:>3} {record['time']} [{record['class']}] {record['step']} {status}".rstrip())


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren ledger",
                                     description="Record a run's steps and check its order rules.")
    sub = parser.add_subparsers(dest="action", required=True)
    p_start = sub.add_parser("start", help="commit to a flow file's order rules and open a run")
    p_start.add_argument("flow_file")
    p_start.add_argument("--label")
    p_start.add_argument("--require", action="append", default=[], dest="required",
                         help="exact required milestone name (repeatable)")
    p_exec = sub.add_parser("exec", help="run a command (no shell) and record its result as evidence")
    p_exec.add_argument("run")
    p_exec.add_argument("--step", required=True)
    p_note = sub.add_parser("note", help="record a step without running anything")
    p_note.add_argument("run")
    p_note.add_argument("--step", required=True)
    p_note.add_argument("--artifact", action="append", default=[])
    p_check = sub.add_parser("check", help="check the order rules against the recorded steps")
    p_check.add_argument("run")
    p_check.add_argument("--require-evidence", action="store_true")
    p_check.add_argument("--json", action="store_true")
    p_show = sub.add_parser("show", help="list the recorded steps")
    p_show.add_argument("run")
    for p in (p_start, p_exec, p_note, p_check, p_show):
        p.add_argument("--dir", default=str(DEFAULT_DIR))
    # The command after `--` is passed through untouched, so its own flags and
    # quoting never reach argparse.
    command = []
    if argv[:1] == ["exec"] and "--" in argv:
        cut = argv.index("--")
        argv, command = argv[:cut], argv[cut + 1:]
    args = parser.parse_args(argv)
    try:
        if args.action == "start":
            run, path, rules = start(args.flow_file, args.dir, args.label, args.required)
            if not rules:
                print("skillwren ledger: the flow file has no order rules; steps are recorded,"
                      " nothing is checked", file=sys.stderr)
            print(run)
            return 0
        path = run_path(args.dir, args.run)
        if args.action == "exec":
            code, out, err = exec_step(path, args.step, command)
            sys.stdout.buffer.write(out)
            sys.stderr.buffer.write(err)
            return code
        if args.action == "note":
            record = note_step(path, args.step, args.artifact)
            print(f"recorded step {record['seq']} as {record['class']}")
            return 0
        if args.action == "check":
            report = check(path, args.require_evidence)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                _print_check(report)
            return 0 if report["ok"] else 1
        show(path)
        return 0
    except (LedgerError, OSError) as error:
        print(f"skillwren ledger: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
