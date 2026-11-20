"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override with TODO_FILE env var; defaults to todo.json next to this file.
DATA_FILE = Path(os.environ.get("TODO_FILE", Path(__file__).with_name("todo.json")))

ITEMS = []


def load(path=None):
    """Load items from disk; missing or corrupt file yields an empty list."""
    path = Path(path or DATA_FILE)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


def save(items, path=None):
    """Atomically write items to disk."""
    path = Path(path or DATA_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
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
