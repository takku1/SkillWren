"""Generate disposable subject repos for skill B (not test fixtures).

Usage: make_subjects.py <dest-dir>
Creates b-gap (README documents init/run; clean undocumented) and
b-clean (all three commands documented) subjects.
"""
import sys
from pathlib import Path

TOOL = '''"""Demo CLI with three commands."""
import argparse

parser = argparse.ArgumentParser(prog="tool", description="Demo tool")
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("init", help="initialise a project")
sub.add_parser("run", help="run the project")
sub.add_parser("clean", help="remove build artefacts")


def main():
    args = parser.parse_args()
    print(f"running {args.command}")


if __name__ == "__main__":
    main()
'''

READMES = {
    "b-gap": "# Demo tool\n\nCommands: `init` sets up, `run` executes.\n",
    "b-clean": ("# Demo tool\n\nCommands: `init` sets up, `run` executes, "
                "`clean` removes build artefacts.\n"),
}


def main():
    dest = Path(sys.argv[1])
    for name, readme in READMES.items():
        root = dest / name
        root.mkdir(parents=True, exist_ok=True)
        (root / "tool.py").write_text(TOOL, encoding="utf-8")
        (root / "README.md").write_text(readme, encoding="utf-8")
    print(f"subjects in {dest}")


if __name__ == "__main__":
    main()
