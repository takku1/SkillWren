"""Generate a pinned, workflow-bound guard policy from an approved flow.

    skillwren policy FLOW --approvals DIR --map MAP.json --out policy.json

MAP names, for each guard operation, the verifier command and (for writes)
the protected target:

    {"verify#deps":   {"verifier": ["python", "-I", "checks/deps.py"]},
     "write#report":  {"verifier": ["python", "-I", "checks/report.py"],
                       "target": "out/REPORT.md"}}

Relative paths resolve against MAP's directory; the executable is resolved
on PATH. Every executable and script argument is pinned by digest, the
flow's bytes are pinned, and the policy binds the host approval directory,
so the guard refuses to start unless that exact flow is approved, and
enforces its typed order rules between policy operations. The command
reports which typed steps have no operation and which rules stay
unenforced. It writes nothing it cannot validate: the result is loaded by
the guard before it is saved. The policy, verifiers, target, approvals and
checkpoint must still live where the agent cannot write.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _resolve_argv(argv, base):
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise ValueError("verifier must be a non-empty list of strings")
    exe = argv[0]
    found = Path(exe) if Path(exe).is_absolute() else None
    if found is None:
        local = (base / exe)
        found = local if local.is_file() else (Path(shutil.which(exe)) if shutil.which(exe) else None)
    if found is None or not found.is_file():
        raise ValueError(f"verifier executable not found: {exe}")
    resolved = [str(found.resolve())]
    for arg in argv[1:]:
        candidate = Path(arg) if Path(arg).is_absolute() else base / arg
        if not arg.startswith("-") and candidate.is_file():
            resolved.append(str(candidate.resolve()))
        else:
            resolved.append(arg)
    pins = {a: _digest(a) for a in resolved if Path(a).is_absolute() and Path(a).is_file()}
    return resolved, pins


def generate(flow, approvals, mapping, map_dir, timeout=10):
    from .validator.workflow import dump_workflow
    from .validator.approval import enforceable_ids
    flow, approvals = Path(flow).resolve(), Path(approvals).resolve()
    operations = {}
    for name, spec in mapping.items():
        if not isinstance(spec, dict) or "verifier" not in spec or set(spec) - {"verifier", "target"}:
            raise ValueError(f"{name}: needs verifier and optional target only")
        argv, pins = _resolve_argv(spec["verifier"], map_dir)
        op = {"argv": argv, "pins": pins, "timeout": timeout}
        if "target" in spec:
            target = Path(spec["target"])
            op["target"] = str((target if target.is_absolute() else map_dir / target).resolve())
        operations[name] = op
    policy = {"version": 1, "workflow": {"flow": str(flow), "flow_sha256": _digest(flow),
                                         "approvals": str(approvals)},
              "operations": operations}
    dump = dump_workflow(flow, True)
    typed = enforceable_ids(dump)
    mapped_ids = {name.split("#", 1)[-1] for name in operations}
    report = {"unmapped_steps": [i for i in typed if i not in mapped_ids],
              "unknown_operations": sorted(n for n in operations
                                           if n.split("#", 1)[-1] not in typed)}
    return policy, report


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren policy",
                                     description="Generate a pinned, workflow-bound guard policy.")
    parser.add_argument("flow")
    parser.add_argument("--approvals", required=True, help="host-owned approval directory")
    parser.add_argument("--map", required=True, help="JSON: operation -> verifier, target")
    parser.add_argument("--out", required=True, help="policy file to create (never overwritten)")
    parser.add_argument("--timeout", type=float, default=10)
    args = parser.parse_args(argv)
    try:
        map_path = Path(args.map).resolve()
        mapping = json.loads(map_path.read_text(encoding="utf-8-sig"))
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError("map must be a non-empty object")
        policy, report = generate(args.flow, args.approvals, mapping, map_path.parent,
                                  args.timeout)
        from .guard import Controller
        status = Controller(policy).handle({"action": "status"})
        with Path(args.out).open("x", encoding="utf-8") as stream:
            json.dump(policy, stream, indent=2)
    except (OSError, ValueError) as error:
        print(f"skillwren policy: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"written": args.out, "enforced_rules": status["enforced_rules"],
                      "unenforced_rules": status["unenforced_rules"], **report}, indent=2))
    if report["unmapped_steps"] or report["unknown_operations"]:
        print("warning: typed steps without an operation stay unguarded; operations "
              "that match no typed step will never be requested by the flow",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
