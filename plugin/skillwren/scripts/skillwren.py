"""SkillWren command line for this skill: no installation, Python 3.9+, standard library only.

Inside an installed plugin the library is bundled beside this script (`../lib`);
in the SkillWren repository checkout it is the repository's `src/`.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "lib", HERE.parents[2] / "src"):
    if (candidate / "skillwren" / "__init__.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    sys.exit("skillwren: bundled library not found beside this script")

if sys.version_info < (3, 9):
    sys.exit("skillwren: needs Python 3.9 or later")

from skillwren.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
