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


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren draft",
                                     description="Propose a workflow from intent. "
                                                 "Proposal only: still needs check, "
                                                 "explanation, and human approval.")
    parser.add_argument("--intent-file", required=True)
    parser.add_argument("--adapter", required=True,
                        help="adapter argv as JSON array")
    parser.add_argument("--out", help="write the proposed flow markdown here")
    args = parser.parse_args(argv)
    try:
        intent = Path(args.intent_file).read_text(encoding="utf-8-sig")
        proposal = draft(intent, json.loads(args.adapter))
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
    print("Not approved. Run check, explain-workflow, and approve before use.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
