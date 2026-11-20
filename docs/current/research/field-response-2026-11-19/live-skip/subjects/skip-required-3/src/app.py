"""Tiny todo CLI with JSON-file persistence."""
import json
import os
import sys

# Override with the TODO_FILE environment variable.
DATA_FILE = os.environ.get(
    "TODO_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")
)


def load_items(path=None):
    path = path or DATA_FILE
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in items] if isinstance(items, list) else []


def save_items(items, path=None):
    path = path or DATA_FILE
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    os.replace(tmp, path)


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
