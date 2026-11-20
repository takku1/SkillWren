"""Assemble the self-contained Claude Code plugin in `plugin/` from its sources.

    py -3 scripts/build_plugin.py          rewrite plugin/ from the sources
    py -3 scripts/build_plugin.py --check  exit 1 if plugin/ differs from what would be written

Sources (edit these, never plugin/ directly):
- skills/skillwren/            the authored skill (SKILL.md, references/language.md, scripts/)
- src/skillwren/               the library, bundled as lib/skillwren (standard library only)
- docs/current/<REFERENCES>    full references, copied into references/
- pyproject.toml               the version written into the manifests

The plugin is committed because a marketplace installs it straight from git;
`--check` in CI keeps it identical to its sources.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "plugin"
SKILL = "skillwren"
REFERENCES = ["SPEC.md", "authoring-guide.md", "skill-template.md", "fragment-template.md", "compiler.md"]
DESCRIPTION = ("Build new agent skills, or convert existing ones, as checked SkillWren logic: "
               "explicit steps, gates and ordering rules validated before the skill ships. "
               "Bundles the SkillWren checker (Python 3.9+, no installation).")


def version():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version = "([^"]+)"', text, re.M).group(1)


def text_bytes(data):
    """Plugin files are written with LF so the tree is identical on every platform."""
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def expected():
    """{relative posix path: bytes} for the whole plugin."""
    files = {}
    skill = ROOT / "skills" / SKILL
    for path in sorted(skill.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            files[f"{SKILL}/{path.relative_to(skill).as_posix()}"] = text_bytes(path.read_bytes())
    lib = ROOT / "src" / "skillwren"
    for path in sorted(lib.rglob("*.py")):
        if "__pycache__" not in path.parts:
            files[f"{SKILL}/lib/skillwren/{path.relative_to(lib).as_posix()}"] = text_bytes(path.read_bytes())
    for name in REFERENCES:
        files[f"{SKILL}/references/{name}"] = text_bytes((ROOT / "docs" / "current" / name).read_bytes())
    for name in ("LICENSE",):
        files[name] = text_bytes((ROOT / name).read_bytes())
    manifest = {
        "name": SKILL,
        "version": version(),
        "description": DESCRIPTION,
        "author": {"name": "takku1"},
        "repository": "https://github.com/takku1/SkillWren",
        "license": "MIT",
        "keywords": ["skills", "agent-skills", "workflow", "validation", "dsl"],
        "skills": [f"./{SKILL}/"],
    }
    files[".claude-plugin/plugin.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return files


def marketplace():
    data = {
        "name": "skillwren",
        "description": "SkillWren: build and check agent skills in a small, statically checked procedure language.",
        "owner": {"name": "takku1"},
        "plugins": [{"name": SKILL, "source": "./plugin", "description": DESCRIPTION, "version": version()}],
    }
    return (json.dumps(data, indent=2) + "\n").encode("utf-8")


def actual():
    if not OUT.exists():
        return {}
    return {path.relative_to(OUT).as_posix(): path.read_bytes()
            for path in sorted(OUT.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if plugin/ is out of date")
    args = parser.parse_args(argv)
    want, have = expected(), actual()
    market = ROOT / ".claude-plugin" / "marketplace.json"
    stale = sorted(p for p in set(want) | set(have) if want.get(p) != have.get(p))
    market_stale = not market.is_file() or market.read_bytes() != marketplace()
    if args.check:
        for path in stale:
            print(f"plugin out of date: {path}")
        if market_stale:
            print("plugin out of date: .claude-plugin/marketplace.json")
        if stale or market_stale:
            print("run: py -3 scripts/build_plugin.py")
            return 1
        print(f"plugin up to date: {len(want)} files, version {version()}")
        return 0
    for path in stale:
        target = OUT / path
        if path in want:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(want[path])
        else:
            target.unlink()
    market.parent.mkdir(exist_ok=True)
    market.write_bytes(marketplace())
    print(f"plugin written: {len(want)} files ({len(stale)} changed), version {version()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
