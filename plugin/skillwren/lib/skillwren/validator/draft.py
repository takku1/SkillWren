"""Propose a workflow from natural-language intent via a model adapter.

The adapter is an executable argv receiving `{"intent": text}` on stdin
and printing `{"flow": markdown, "assumptions": [...], "questions": [...]}`
on stdout. The adapter proposes only: it cannot approve, and its output
must still pass `check`, `explain-workflow`, and human `approve` before
anything is enforced. Assumptions and unresolved questions are part of the
deliverable, not hidden.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def draft(intent, adapter):
    proc = subprocess.run(adapter, input=json.dumps({"intent": intent}),
                          text=True, capture_output=True, timeout=300)
    if proc.returncode != 0:
        raise ValueError(f"adapter exited {proc.returncode}: "
                         f"{proc.stderr[-500:]}")
    try:
        proposal = json.loads(proc.stdout)
    except ValueError:
        raise ValueError("adapter did not return JSON")
    if not isinstance(proposal, dict) or not proposal.get("flow"):
        raise ValueError("adapter must return an object with a flow string")
    for key in ("assumptions", "questions"):
        if not isinstance(proposal.get(key, []), list):
            raise ValueError(f"adapter {key!r} must be a list")
    return {"flow": proposal["flow"],
            "assumptions": proposal.get("assumptions", []),
            "questions": proposal.get("questions", [])}


def _unbacked(flow_text):
    """Unbacked verify gates in a proposal; empty if it does not parse."""
    import tempfile
    from .evidence import unbacked_verifies
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "proposal.md"
        path.write_text(flow_text, encoding="utf-8")
        try:
            return unbacked_verifies(path, fragment=True)
        except Exception:  # an unparseable proposal is reported by `check`
            return []


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren draft",
                                     description="Propose a workflow from intent. "
                                                 "Proposal only: still needs check, "
                                                 "explanation, and human approval.")
    parser.add_argument("--intent-file", required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--adapter", help="adapter argv as JSON array")
    group.add_argument("--adapter-file",
                       help="file holding the adapter argv as a JSON array "
                            "(avoids shell quoting)")
    parser.add_argument("--out", help="write the proposed flow markdown here")
    parser.epilog = ("The adapter can also follow `--` as plain words, with no JSON "
                     "quoting: skillwren draft --intent-file i.md -- py -3 adapter.py")
    command = []
    if "--" in argv:
        cut = argv.index("--")
        argv, command = argv[:cut], argv[cut + 1:]
    args = parser.parse_args(argv)
    given = [bool(command), args.adapter is not None, args.adapter_file is not None]
    if sum(given) != 1:
        parser.error("give the adapter exactly once: after --, --adapter, or --adapter-file")
    try:
        intent = Path(args.intent_file).read_text(encoding="utf-8-sig")
        if command:
            adapter = command
        elif args.adapter is not None:
            adapter = json.loads(args.adapter)
        else:
            adapter = json.loads(Path(args.adapter_file).read_text(encoding="utf-8-sig"))
        if (not isinstance(adapter, list) or not adapter
                or not all(isinstance(part, str) for part in adapter)):
            raise ValueError("adapter must be a non-empty list of strings")
        proposal = draft(intent, adapter)
    except (OSError, ValueError) as error:
        print(f"skillwren draft: {error}", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(proposal["flow"], encoding="utf-8")
    else:
        print(proposal["flow"], end="" if proposal["flow"].endswith("\n") else "\n")
    print("assumptions:", file=sys.stderr)
    for assumption in proposal["assumptions"]:
        print(f"  - {assumption}", file=sys.stderr)
    print("unresolved questions:", file=sys.stderr)
    for question in proposal["questions"]:
        print(f"  - {question}", file=sys.stderr)
    unbacked = _unbacked(proposal["flow"])
    if unbacked:
        print("verify gates without recorded evidence (the model's own judgment; "
              "cite an exec result with `from`, or confirm this is intended):",
              file=sys.stderr)
        for gate in unbacked:
            print(f"  - {gate['flow']} line {gate['line']}: {gate['text']}",
                  file=sys.stderr)
    print("Not approved. Run check, explain-workflow, and approve before use.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
