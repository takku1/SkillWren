"""Tiny todo CLI."""
import json
import os
import sys
import tempfile

STORE_PATH = os.environ.get(
    "TODO_FILE", os.path.join(os.path.expanduser("~"), ".todo_items.json")
)

ITEMS = []


def load_items(path=None):
    """Load items from disk; return an empty list if missing or corrupt."""
    try:
        with open(path or STORE_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


def save_items(items, path=None):
    """Atomically write items to disk."""
    path = path or STORE_PATH
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
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
