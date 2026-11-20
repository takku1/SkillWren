"""Tiny todo CLI with JSON-file persistence."""
import json
import os
import sys
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "todos.json"


def store_path():
    return Path(os.environ.get("TODO_FILE") or DEFAULT_PATH)


def load_items(path):
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"warning: {path} is corrupt; starting empty", file=sys.stderr)
        return []
    if not isinstance(items, list):
        return []
    return [str(i) for i in items]


def save_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    os.replace(tmp, path)  # atomic: never leaves a half-written file


def main(argv):
    path = store_path()
    items = load_items(path)
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
