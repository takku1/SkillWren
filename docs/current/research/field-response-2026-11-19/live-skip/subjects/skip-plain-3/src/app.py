"""Tiny todo CLI."""
import json
import os
import sys
import tempfile

# Override with the TODO_FILE environment variable.
DATA_FILE = os.environ.get(
    "TODO_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "todos.json"),
)


def load_items(path=None):
    path = path or DATA_FILE
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return items if isinstance(items, list) else []


def save_items(items, path=None):
    path = path or DATA_FILE
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    # Write atomically so a crash can't leave a corrupt file.
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
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
