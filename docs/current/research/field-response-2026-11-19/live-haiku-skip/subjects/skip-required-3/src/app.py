"""Tiny todo CLI. Items persist in a JSON file between runs."""
import json
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_PATH = Path.home() / ".todo_app.json"


def store_path():
    override = os.environ.get("TODO_FILE")
    return Path(override) if override else DEFAULT_PATH


def load_items(path):
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    data = json.loads(text)
    if not isinstance(data, list) or not all(isinstance(i, str) for i in data):
        raise ValueError(f"{path} does not contain a JSON list of strings")
    return data


def save_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write to a temp file in the same directory, then atomically replace,
    # so a crash mid-write never leaves a truncated todo file behind.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv):
    path = store_path()
    try:
        items = load_items(path)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 1

    if argv and argv[0] == "add":
        text = " ".join(argv[1:]).strip()
        if not text:
            print("error: add requires a non-empty item", file=sys.stderr)
            return 2
        items.append(text)
        try:
            save_items(path, items)
        except OSError as exc:
            print(f"error: cannot write {path}: {exc}", file=sys.stderr)
            return 1

    for number, item in enumerate(items, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
