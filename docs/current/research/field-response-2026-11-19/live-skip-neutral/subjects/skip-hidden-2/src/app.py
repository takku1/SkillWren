"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path


def data_file():
    """Storage path; override with the TODO_FILE environment variable."""
    return Path(os.environ.get("TODO_FILE") or Path.home() / ".todo_items.json")


def load_items(path):
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in items] if isinstance(items, list) else []


def save_items(path, items):
    """Write atomically so a crash can't leave a corrupt file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    path = data_file()
    items = load_items(path)
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
