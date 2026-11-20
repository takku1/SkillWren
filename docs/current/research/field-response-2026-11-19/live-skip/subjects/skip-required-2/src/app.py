"""Tiny todo CLI with items persisted to a JSON file."""
import json
import os
import sys
import tempfile

# Override with the TODO_FILE environment variable.
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")


def storage_path():
    return os.environ.get("TODO_FILE", DEFAULT_PATH)


def load_items(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"warning: {path} is not valid JSON; starting empty", file=sys.stderr)
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(path, items):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
        os.replace(tmp, path)  # atomic: never leaves a half-written file
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


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
