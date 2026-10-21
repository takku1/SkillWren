"""SkillWren console entry point."""
import sys

from .validator import main as _main


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "measure":
        from .metrics import main as measure_main
        sys.exit(measure_main(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        from .compiler import main as build_main
        sys.exit(build_main(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == "conform":
        from .conform import main as conform_main
        sys.exit(conform_main(sys.argv[2:]))
    sys.exit(_main(sys.argv))
