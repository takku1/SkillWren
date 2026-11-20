"""Tiny todo CLI."""
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_PATH = Path.home() / ".todo_items.json"


def store_path():
    override = os.environ.get("TODO_FILE")
    return Path(override) if override else DEFAULT_PATH


def load_items(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError(f"{path} does not contain a JSON list of strings")
    return data


def save_items(path, items):
    # Write to a temp file in the same directory, then swap it in atomically,
    # so a crash mid-write never leaves a truncated todo file behind.
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)
        raise


def main(argv):
    path = store_path()
    try:
        items = load_items(path)
    except (OSError, ValueError) as error:
        print(f"error: could not read todo list: {error}", file=sys.stderr)
        return 1

    if argv and argv[0] == "add":
        items.append(" ".join(argv[1:]))
        try:
            save_items(path, items)
        except OSError as error:
            print(f"error: could not save todo list: {error}", file=sys.stderr)
            return 1
    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
