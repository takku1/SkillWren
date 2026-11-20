"""Tiny todo CLI with JSON persistence."""
import json
import os
import sys

# Override with TODO_FILE; default lives next to this script's package.
STORE = os.environ.get(
    "TODO_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json"),
)


def load(path=STORE):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save(items, path=STORE):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f)
    os.replace(tmp, path)


def main(argv):
    items = load()
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save(items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
