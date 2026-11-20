"""Tiny todo CLI."""
import json
import os
import sys
import tempfile

STORE = os.environ.get(
    "TODO_FILE", os.path.join(os.path.expanduser("~"), ".todo_items.json")
)

ITEMS = []


def load(path=None):
    """Load items from disk; missing or corrupt file yields an empty list."""
    try:
        with open(path or STORE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return [str(x) for x in data] if isinstance(data, list) else []


def save(items, path=None):
    """Atomically write items to disk."""
    path = path or STORE
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
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
    ITEMS[:] = load()
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
        save(ITEMS)
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
