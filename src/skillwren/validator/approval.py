"""Human approval and activation gate for workflows.

`approve` records who approved the exact bytes of a flow file, which
typed operations it exposes for enforcement, and whether the
administrator's guard policy defines matching operations. Any substantive
edit changes the digest and invalidates the approval; `approve --check`
reports that. Approval confirms intended meaning, not formal equivalence,
and it never grants capabilities by itself: activation still requires a
policy that covers the workflow's operations.
"""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path

from .workflow import DUMP_VERSION, dump_workflow

DEFAULT_DIR = Path(".skillwren") / "approvals"


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def enforceable_ids(dump):
    """Typed IDs on guard verbs: the operations a policy could enforce."""
    import re
    ids = set()
    pattern = re.compile(r"#([A-Za-z][\w-]*)")
    for flow in dump["flows"].values():
        for node in _flatten(flow):
            if node.get("kind") in ("action", "gate"):
                text = node.get("text", "")
                head = text.split(None, 1)[0] if text else ""
                if head in ("verify", "write", "exec"):
                    ids.update(pattern.findall(text))
    return sorted(ids)


def _flatten(statements):
    for statement in statements:
        yield statement
        yield from _flatten(statement.get("children", []))


def policy_operations(policy_path):
    policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    operations = policy.get("operations", {})
    if not isinstance(operations, dict):
        raise ValueError("policy operations must be a map")
    return sorted(operations)


def coverage(enforceable, operations):
    """Map each workflow ID to the policy operation covering it, if any."""
    covered, uncovered = {}, []
    for ident in enforceable:
        match = next((op for op in operations
                      if op.split("#")[-1] == ident), None)
        if match is None:
            uncovered.append(ident)
        else:
            covered[ident] = match
    return covered, uncovered


def record_path(directory, flow_file):
    return Path(directory) / (Path(flow_file).stem + ".approvals.jsonl")


def approve(flow_file, fragment, by, policy, directory=DEFAULT_DIR):
    digest = file_digest(flow_file)
    dump = dump_workflow(flow_file, fragment)
    ids = enforceable_ids(dump)
    operations = policy_operations(policy) if policy else []
    covered, uncovered = coverage(ids, operations)
    record = {"type": "approval", "time": _now(), "file": str(flow_file),
              "file_sha256": digest, "dump_version": DUMP_VERSION,
              "enforceable": ids, "by": by,
              "policy": str(policy) if policy else None,
              "covered": covered, "uncovered": uncovered}
    path = record_path(directory, flow_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def check(flow_file, directory=DEFAULT_DIR):
    path = record_path(directory, flow_file)
    if not path.is_file():
        return {"approved": False, "reason": "no approval recorded"}
    records = [json.loads(line) for line in
               path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records:
        return {"approved": False, "reason": "no approval recorded"}
    latest = records[-1]
    current = file_digest(flow_file)
    if current != latest["file_sha256"]:
        return {"approved": False, "reason": "file changed since approval",
                "approved_time": latest["time"], "by": latest.get("by")}
    return {"approved": True, "time": latest["time"], "by": latest.get("by"),
            "uncovered": latest.get("uncovered", [])}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren approve",
                                     description="Record or check human approval "
                                                 "of a workflow's exact bytes.")
    parser.add_argument("flow")
    parser.add_argument("--fragment", action="store_true")
    parser.add_argument("--by", help="approver identity (required to approve)")
    parser.add_argument("--policy", help="guard policy JSON to check coverage against")
    parser.add_argument("--dir", default=str(DEFAULT_DIR))
    parser.add_argument("--check", action="store_true",
                        help="report whether the current bytes are approved")
    args = parser.parse_args(argv)
    try:
        if args.check:
            report = check(args.flow, args.dir)
            print(json.dumps(report, indent=2))
            return 0 if report["approved"] else 1
        if not args.by:
            parser.error("--by is required to approve")
        record = approve(args.flow, args.fragment, args.by, args.policy, args.dir)
        print(json.dumps(record, indent=2))
        if record["uncovered"]:
            print("warning: no policy operation covers: "
                  + ", ".join("#" + i for i in record["uncovered"]),
                  file=sys.stderr)
        return 0
    except (OSError, ValueError) as error:
        print(f"skillwren approve: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
