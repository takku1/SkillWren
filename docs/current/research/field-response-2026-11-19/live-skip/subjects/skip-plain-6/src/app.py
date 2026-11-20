"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path

# Override with the TODO_FILE environment variable.
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "todos.json"


def store_path():
    return Path(os.environ.get("TODO_FILE") or DEFAULT_PATH)


def load_items(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"Corrupt todo file {path}: {exc}")
    if not isinstance(data, list) or not all(isinstance(i, str) for i in data):
        raise SystemExit(f"Corrupt todo file {path}: expected a list of strings")
    return data


def save_items(path, items):
    """Write atomically so a crash can't leave a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


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
