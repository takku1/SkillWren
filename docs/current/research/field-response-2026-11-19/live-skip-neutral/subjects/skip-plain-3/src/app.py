"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path


def storage_path():
    """Where items are stored; override with the TODO_FILE env var."""
    return Path(os.environ.get("TODO_FILE") or Path.home() / ".todo_items.json")


def load_items(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(path, items):
    """Write atomically so a crash can't leave a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    path = storage_path()
    ITEMS = load_items(path)
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
        save_items(path, ITEMS)
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
