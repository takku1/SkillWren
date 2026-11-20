"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path


def store_path():
    """Storage file: $TODO_FILE if set, else ~/.todo.json."""
    return Path(os.environ.get("TODO_FILE") or Path.home() / ".todo.json")


def load_items(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        raise ValueError(f"{path} is not a todo list")
    return [str(i) for i in data]


def save_items(path, items):
    """Write atomically so a crash can't leave a truncated file."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    path = store_path()
    try:
        ITEMS = load_items(path)
    except (ValueError, OSError) as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return 1
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
        save_items(path, ITEMS)
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
