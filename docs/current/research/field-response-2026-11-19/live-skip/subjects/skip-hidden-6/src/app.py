"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override with TODO_FILE env var; defaults to todo.json next to this file.
DATA_FILE = Path(os.environ.get("TODO_FILE", Path(__file__).with_name("todo.json")))

ITEMS = []


def load_items(path=None):
    path = Path(path or DATA_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(items, path=None):
    path = Path(path or DATA_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically so a crash can't leave a corrupt file.
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    ITEMS[:] = load_items()
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
        save_items(ITEMS)
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
