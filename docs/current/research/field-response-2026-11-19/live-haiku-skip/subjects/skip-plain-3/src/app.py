"""Tiny todo CLI with items persisted to a JSON file between runs."""
import json
import os
import sys
from pathlib import Path

DEFAULT_PATH = Path.home() / ".todo_items.json"


def data_path():
    override = os.environ.get("TODO_FILE")
    return Path(override) if override else DEFAULT_PATH


def load_items(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        items = json.load(handle)
    if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
        raise ValueError(f"{path} does not contain a JSON list of strings")
    return items


def save_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)
    os.replace(tmp, path)


def main(argv):
    path = data_path()
    try:
        items = load_items(path)
    except (OSError, ValueError) as exc:
        print(f"error: could not read todo list: {exc}", file=sys.stderr)
        return 1

    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)

    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
