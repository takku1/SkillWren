"""Tiny todo CLI with JSON-file persistence."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override with the TODO_FILE environment variable.
DEFAULT_PATH = Path(__file__).resolve().parent / "todo.json"


def _path():
    return Path(os.environ.get("TODO_FILE", DEFAULT_PATH))


def load_items(path=None):
    path = path or _path()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(items, path=None):
    path = Path(path or _path())
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write atomically so a crash can't leave a corrupt file.
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
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
