"""Tiny todo CLI with JSON-file persistence."""
import json
import os
import sys
import tempfile

# Override with the TODO_FILE environment variable.
DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".todo_items.json")


def _path():
    return os.environ.get("TODO_FILE", DEFAULT_PATH)


def load_items(path=None):
    """Return saved items; a missing or corrupt file yields an empty list."""
    try:
        with open(path or _path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return [str(i) for i in data]


def save_items(items, path=None):
    """Atomically write items so a crash can't leave a half-written file."""
    path = path or _path()
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
    items = load_items()
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
