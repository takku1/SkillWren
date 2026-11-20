"""Tiny todo CLI with items persisted to a JSON file."""
import json
import os
import sys
import tempfile

# Override with TODO_FILE; defaults to todo.json next to this module.
DATA_FILE = os.environ.get(
    "TODO_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")
)


def load(path=None):
    """Return saved items, or an empty list if none/corrupt."""
    try:
        with open(path or DATA_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save(items, path=None):
    """Atomically write items to disk."""
    path = path or DATA_FILE
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(items, fh, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    items = load()
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save(items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
