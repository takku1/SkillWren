"""Tiny todo CLI.

Items are stored as a JSON list in a file so they survive restarts. The file
defaults to ~/.todo_items.json and can be moved with the TODO_FILE env var.
"""
import json
import os
import sys
import tempfile

DATA_PATH = os.environ.get(
    "TODO_FILE", os.path.join(os.path.expanduser("~"), ".todo_items.json")
)


def load_items(path):
    """Return the saved items, or an empty list if no file exists yet."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Todo file {path} is corrupt: {exc}")
    if not isinstance(data, list) or not all(isinstance(i, str) for i in data):
        raise SystemExit(f"Todo file {path} does not contain a list of strings.")
    return data


def save_items(path, items):
    """Write items atomically so a crash never leaves a half-written file."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def main(argv, path=None):
    path = path or DATA_PATH
    items = load_items(path)
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        save_items(path, items)
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
