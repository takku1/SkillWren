"""Tiny todo CLI with items persisted to a JSON file."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override with TODO_FILE; defaults to todo.json beside this script.
DATA_FILE = Path(os.environ.get("TODO_FILE", Path(__file__).with_name("todo.json")))


def load_items(path=DATA_FILE):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(items, path=DATA_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)  # atomic: no half-written file on crash
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
