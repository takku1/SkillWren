"""Tiny todo CLI."""
import json
import os
import sys
from pathlib import Path

DATA_FILE = Path(os.environ.get("TODO_FILE", Path(__file__).parent / "todos.json"))


def load_items(path=DATA_FILE):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    return [str(i) for i in data] if isinstance(data, list) else []


def save_items(items, path=DATA_FILE):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(items, indent=2), encoding="utf-8")
    os.replace(tmp, path)


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
