"""SkillWren: checked procedures for agent skills.

Skills keep their prose meaning, and their control flow (gates, authority,
effects, recovery, ordering) is written in a closed vocabulary that a static
checker can read. Complete SkillWren skills carry a contract header; flow
fragments embed `logic` blocks in ordinary Markdown next to a SKILL.md that
keeps only the host fields.
"""

__version__ = "0.8.0"

from .validator import validate_file, validate_files, validate_fragment

__all__ = ["__version__", "validate_file", "validate_files", "validate_fragment"]
