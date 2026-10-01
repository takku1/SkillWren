"""SkillWren: logic-first skills.

Skills written as logic instead of prose: a contract header for cheap,
headers-only routing plus a closed control vocabulary with gates,
authority, effects, and local recovery.
"""

__version__ = "0.4.0"

from .validator import validate_file, validate_files

__all__ = ["__version__", "validate_file", "validate_files"]
