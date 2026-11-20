"""Tiny todo CLI with items persisted to a JSON file."""
import json
import os
import sys
import tempfile

STORE = os.environ.get(
    "TODO_FILE", os.path.join(os.path.expanduser("~"), ".todo_items.json")
)


def load(path=STORE):
    """Return saved items, or an empty list if none/unreadable."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


def save(items, path=STORE):
    """Atomically write items so a crash can't corrupt the file."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
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
