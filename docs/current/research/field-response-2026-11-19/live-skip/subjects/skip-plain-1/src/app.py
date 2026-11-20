"""Tiny todo CLI."""
import json
import os
import sys

# Override with TODO_FILE; defaults to todos.json next to this module.
DATA_FILE = os.environ.get(
    "TODO_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")
)


def load_items(path=None):
    path = path or DATA_FILE
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(items, path=None):
    path = path or DATA_FILE
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f)
    os.replace(tmp, path)


ITEMS = load_items()


def main(argv):
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
        save_items(ITEMS)
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
