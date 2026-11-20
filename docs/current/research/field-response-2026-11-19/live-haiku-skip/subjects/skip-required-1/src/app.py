"""Tiny todo CLI with JSON persistence.

Items are stored as a JSON list of strings in TODO_FILE (environment
variable), defaulting to todos.json next to this script.
"""
import json
import os
import sys
import tempfile

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def todo_path():
    return os.environ.get("TODO_FILE") or DEFAULT_PATH


def load_items(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError(f"{path} does not contain a JSON list of strings")
    return data


def save_items(items, path):
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".todos-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def main(argv):
    path = todo_path()
    try:
        items = load_items(path)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read todo list: {exc}", file=sys.stderr)
        return 1
    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        try:
            save_items(items, path)
        except OSError as exc:
            print(f"error: cannot save todo list: {exc}", file=sys.stderr)
            return 1
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
