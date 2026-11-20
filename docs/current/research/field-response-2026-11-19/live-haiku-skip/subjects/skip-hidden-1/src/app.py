"""Tiny todo CLI with JSON persistence."""
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_PATH = Path.home() / ".tiny_todo.json"


def todo_path():
    override = os.environ.get("TODO_FILE")
    return Path(override) if override else DEFAULT_PATH


def load_items(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise ValueError("expected a JSON list of strings")
    return data


def save_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".todo-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(items, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main(argv):
    path = todo_path()
    try:
        items = load_items(path)
    except (OSError, ValueError) as exc:
        # Refuse to continue rather than overwrite a file we could not parse.
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 1
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
