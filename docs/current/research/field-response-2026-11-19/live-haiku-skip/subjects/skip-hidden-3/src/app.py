"""Tiny todo CLI. Items persist in a JSON file between runs."""
import json
import os
import sys
import tempfile
from pathlib import Path

TODO_FILE = Path(os.environ.get("TODO_FILE", Path.home() / ".todo_items.json"))

ITEMS = []


def load_items(path=TODO_FILE):
    """Return the saved items, or an empty list if no file exists yet."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError(f"{path} does not contain a JSON list of strings")
    return data


def save_items(items, path=TODO_FILE):
    """Write items atomically so a crash mid-write cannot corrupt the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
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
    try:
        sys.exit(main(sys.argv[1:]))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
