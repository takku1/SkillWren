"""Tiny todo CLI."""
import json
import os
import sys
from pathlib import Path

# Override with the TODO_FILE environment variable.
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "todos.json"


def storage_path():
    return Path(os.environ.get("TODO_FILE") or DEFAULT_PATH)


def load_items(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"warning: {path} is corrupt; starting empty", file=sys.stderr)
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    os.replace(tmp, path)


def main(argv):
    path = storage_path()
    items = load_items(path)
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
