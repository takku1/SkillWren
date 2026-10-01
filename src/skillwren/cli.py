"""SkillWren console entry point."""
import sys

from .validator import main as _main


def main() -> None:
    sys.exit(_main(sys.argv))
