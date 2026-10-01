"""SkillWren: logic-first skills.

Skills written as logic instead of prose: a contract header for cheap,
headers-only routing plus a 16-verb logic body with gates, authority,
effects, and local recovery.
"""

__version__ = "0.3.0"

from .validator import validate_file, validate_files

__all__ = ["__version__", "validate_file", "validate_files"]
