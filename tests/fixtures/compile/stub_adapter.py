"""Scripted compile adapter for offline tests.

    stub_adapter.py SCRIPT.json STATE.json

SCRIPT maps each phase to a list of replies; the Nth call of a phase gets
the Nth reply (the last one repeats). STATE records call counts and every
request, so tests can assert what the compiler sent back.
"""
import json
from pathlib import Path
import sys


def main():
    script = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    state_path = Path(sys.argv[2])
    state = (json.loads(state_path.read_text(encoding="utf-8"))
             if state_path.exists() else {"counts": {}, "requests": []})
    request = json.load(sys.stdin)
    phase = request["phase"]
    count = state["counts"].get(phase, 0)
    state["counts"][phase] = count + 1
    state["requests"].append(request)
    state_path.write_text(json.dumps(state), encoding="utf-8")
    replies = script.get(phase)
    if not replies:
        print(f"no scripted reply for phase {phase}", file=sys.stderr)
        return 3
    print(json.dumps(replies[min(count, len(replies) - 1)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
