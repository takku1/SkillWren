"""Tiny todo CLI."""
import json
import os
import sys
from pathlib import Path

DATA_FILE = Path(os.environ.get("TODO_FILE", Path.home() / ".todo_items.json"))

ITEMS = []


def load_items(path=DATA_FILE):
    """Return saved items; a missing file means an empty list."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError("expected a JSON list of strings")
    return data


def save_items(items, path=DATA_FILE):
    """Write items atomically so a crash mid-write cannot corrupt the file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(items, handle, indent=2)
    os.replace(tmp, path)


def main(argv):
    try:
        ITEMS[:] = load_items()
    except (OSError, ValueError) as error:
        print(f"Cannot read {DATA_FILE}: {error}", file=sys.stderr)
        return 1
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
        save_items(ITEMS)
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
