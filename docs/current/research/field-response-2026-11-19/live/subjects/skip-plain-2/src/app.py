"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override with the TODO_FILE environment variable.
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "todo.json"


def data_path():
    return Path(os.environ.get("TODO_FILE", DEFAULT_PATH))


def load_items(path):
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"warning: {path} is corrupt; starting with an empty list", file=sys.stderr)
        return []
    return [str(i) for i in items] if isinstance(items, list) else []


def save_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file then replace, so a crash can't truncate the list.
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main(argv):
    path = data_path()
    items = load_items(path)
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
