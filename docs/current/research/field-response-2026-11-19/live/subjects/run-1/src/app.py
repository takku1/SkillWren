"""Tiny todo CLI."""
import sys

VERSION = "1.0"
ITEMS = []


def main(argv):
    if argv and argv[0] == "--version":
        print(VERSION)
        return 0
    if argv and argv[0] == "add":
        ITEMS.append(" ".join(argv[1:]))
    for number, item in enumerate(ITEMS, 1):
        print(f"{number}. {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
