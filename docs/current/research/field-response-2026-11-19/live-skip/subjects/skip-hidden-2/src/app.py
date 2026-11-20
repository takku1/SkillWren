"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override the storage location with the TODO_FILE environment variable.
DATA_FILE = Path(os.environ.get("TODO_FILE") or Path.home() / ".todo.json")


def load_items(path=None):
    path = Path(path or DATA_FILE)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return []
    return [str(x) for x in data] if isinstance(data, list) else []


def save_items(items, path=None):
    path = Path(path or DATA_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file then replace, so a crash can't corrupt the list.
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    items = load_items()
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
