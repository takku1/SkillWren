"""Tiny todo CLI."""
import json
import os
import sys
import tempfile

DATA_FILE = os.environ.get(
    "TODO_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")
)


def load_items(path=None):
    try:
        with open(path or DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(items, path=None):
    path = path or DATA_FILE
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
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
