"""Tiny todo CLI with persistence."""
import json
import os
import sys
import tempfile

STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")


def load(path=STORE):
    """Return saved items, or [] if the file is missing or unreadable."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save(items, path=STORE):
    """Write items atomically so a crash cannot corrupt the file."""
    directory = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


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
