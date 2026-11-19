"""Compile logic skills, optionally accepting a reviewed, smaller conversion.

The control language is the existing SkillWren logic/contract grammar. This
compiler adds one authoring declaration, outside fences in the appendix:
    @context <id> from "relative/path.md" as instruction|example|data

Context imports are packaging, not compression. Optimized builds compare the
complete emitted prompt with reviewed originals and archive those originals
outside the prompt. Semantic rewriting remains the author/agent's job.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import sys
import tempfile

from .validator import validate_file
from .validator.files import Workspace, validate_fragment

CONTEXT = re.compile(
    r'@context ([a-z][a-z0-9]*(?:-[a-z0-9]+)*) from '
    r'("(?:[^"\\]|\\.)*") as (instruction|example|data)\s*')


class BuildError(ValueError):
    """An invalid or incomplete source package cannot be compiled."""


def _source_record(data):
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), "base64": base64.b64encode(data).decode("ascii")}


def _compile(source):
    source = Path(source).resolve()
    raw = source.read_bytes()
    text = raw.decode("utf-8-sig")
    sources = {source.name: _source_record(raw)}
    chunks, contexts, seen = [], [], set()
    size = 0
    fence = None

    def emit(data):
        nonlocal size
        chunks.append(data)
        size += len(data)

    for number, line in enumerate(text.splitlines(keepends=True), 1):
        stripped = line.strip()
        opening = re.match(r"^(`{3,}|~{3,})(.*)$", stripped)
        if fence:
            if stripped == fence:
                fence = None
            emit(line.encode("utf-8"))
            continue
        if opening:
            fence = opening.group(1)
            emit(line.encode("utf-8"))
            continue
        if not stripped.startswith("@context"):
            emit(line.encode("utf-8"))
            continue
        match = CONTEXT.fullmatch(stripped)
        if not match or line[:1].isspace():
            raise BuildError(f"{source.name}:{number}: malformed @context declaration")
        name, quoted, role = match.groups()
        if name in seen:
            raise BuildError(f"{source.name}:{number}: duplicate context id {name!r}")
        seen.add(name)
        relative = json.loads(quoted)
        if Path(relative).is_absolute() or PureWindowsPath(relative).drive:
            raise BuildError(f"context path must be relative, not outside the source directory: {relative}")
        path = (source.parent / relative).resolve()
        try:
            key = path.relative_to(source.parent).as_posix()
        except ValueError:
            raise BuildError(f"context path is outside the source directory: {relative}") from None
        payload = path.read_bytes()
        payload.decode("utf-8")  # Text context only; reject rather than replace invalid bytes.
        sources[key] = _source_record(payload)
        # A fence longer than every payload backtick run cannot collide.
        width = max([3] + [len(run) for run in re.findall(rb"`+", payload)]) + 1
        delimiter = b"`" * width
        emit(delimiter + f"context {name} {role}\n".encode("ascii"))
        start = size
        emit(payload)
        end = size
        if not payload.endswith(b"\n"):
            emit(b"\n")
        emit(delimiter + b"\n")
        contexts.append({"id": name, "role": role, "source": key,
                         "declaration_line": number, "start_byte": start,
                         "end_byte": end, "sha256": sources[key]["sha256"]})
    compiled = b"".join(chunks)
    manifest = {"format": "skillwren-build-1", "mode": "full",
                "entry": source.name, "output_sha256": hashlib.sha256(compiled).hexdigest(),
                "sources": sources, "contexts": contexts, "deferred_contexts": []}
    return compiled, manifest


SKIP_PARTS = {".git", "__pycache__", ".skillwren", "node_modules"}


def fragment_set(source):
    """Files of a fragment-set skill directory, sorted, as {relative: bytes}.

    The set is everything a host could load from the directory: `SKILL.md`
    plus every other file, skipping VCS, caches and SkillWren run state."""
    root = Path(source).resolve()
    if not (root / "SKILL.md").is_file():
        raise BuildError(f"fragment set needs SKILL.md at its root: {root}")
    files = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_file() and not SKIP_PARTS & set(relative.parts):
            files[relative.as_posix()] = path.read_bytes()
    return files


def expanded_text(source):
    """The complete loadable Markdown of a fragment set, for measurement."""
    files = fragment_set(source)
    return b"".join(b"<!-- file: " + name.encode("utf-8") + b" -->\n" + raw
                    + (b"" if raw.endswith(b"\n") else b"\n")
                    for name, raw in files.items() if name.endswith(".md"))


def build_fragments(source, output):
    """Validate every logic fragment of a skill directory and package the set.

    Every Markdown file holding a `logic` block must pass `check
    --fragment` with cross-file runs resolved inside the set, including an
    inline-form `SKILL.md` (contract and logic beside name and description,
    the 0.9 recommended form). A `SKILL.md` without logic stays ordinary."""
    root = Path(source).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise BuildError(f"output already exists: {output}")
    files = fragment_set(root)
    workspace = Workspace()
    checked, warnings, problems = [], [], []
    for name in files:
        if not name.endswith(".md") or b"```logic" not in files[name]:
            continue
        errors, warns = validate_fragment(root / name, workspace=workspace)
        checked.append(name)
        problems += [f"{name}:{d.line}: {d.rule}: {d.msg}" for d in errors]
        warnings += [{"file": name, "line": d.line, "rule": d.rule, "message": d.msg}
                     for d in warns]
    if not checked:
        raise BuildError("fragment set has no logic fragments to check")
    if problems:
        raise BuildError("fragment set is invalid:\n" + "\n".join(problems))
    expanded = expanded_text(root)
    manifest = {"format": "skillwren-build-1", "mode": "fragments", "entry": "SKILL.md",
                "checked_fragments": checked,
                "expanded_sha256": hashlib.sha256(expanded).hexdigest(),
                "expanded_bytes": len(expanded),
                "sources": {name: {"sha256": hashlib.sha256(raw).hexdigest(),
                                   "bytes": len(raw)} for name, raw in files.items()},
                "contexts": [], "deferred_contexts": [], "warnings": warnings}
    with tempfile.TemporaryDirectory(prefix="skillwren-build-", dir=output.parent) as temporary:
        artifact = Path(temporary) / "artifact"
        for name, raw in files.items():
            target = artifact / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (artifact / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        if output.exists():
            raise BuildError(f"output already exists: {output}")
        artifact.rename(output)
    return manifest


def build(source, output, *, original=None, review=None, original_context=(),
          metric="tokens", tokenizer="cl100k_base", max_ratio=1.0):
    """Validate and create a new output directory; never overwrite an old build."""
    output = Path(output).resolve()
    if Path(source).is_dir():
        if original is not None or review is not None or original_context:
            raise BuildError("optimized builds take a single-file skill; for a fragment "
                             "set, package it here and compare sizes with `measure DIR DIR`")
        return build_fragments(source, output)
    try:
        if (original is None) != (review is None):
            raise BuildError("optimized builds require both original and review")
        if original is None and (original_context or metric != "tokens"
                                 or tokenizer != "cl100k_base" or max_ratio != 1.0):
            raise BuildError("size-comparison options require original and review")
        if output.exists():
            raise BuildError(f"output already exists: {output}")
        compiled, manifest = _compile(source)
        with tempfile.TemporaryDirectory(prefix="skillwren-build-", dir=output.parent) as temporary:
            artifact = Path(temporary) / "artifact"
            artifact.mkdir()
            skill = artifact / "SKILL.md"
            skill.write_bytes(compiled)
            errors, warnings = validate_file(skill)
            if errors:
                raise BuildError("compiled skill is invalid:\n" + "\n".join(
                    f"SKILL.md:{d.line}: {d.rule}: {d.msg}" for d in errors))
            if original is not None:
                from .metrics import compare
                from .review import read_originals, validate_review
                originals = read_originals(original, original_context)
                review_bytes = Path(review).read_bytes()
                candidate_bytes = base64.b64decode(manifest["sources"][Path(source).resolve().name]["base64"])
                result = validate_review(originals, candidate_bytes, compiled,
                                         json.loads(review_bytes))
                comparison = compare(list(originals.values()), compiled, metric, tokenizer, max_ratio)
                if not comparison["accepted"]:
                    raise BuildError(
                        f"compiled prompt does not meet size target: {comparison['original']['count']} -> "
                        f"{comparison['compiled']['count']} {metric}; max ratio {max_ratio}; "
                        "a conversion must be strictly smaller")
                manifest["optimization"] = {**comparison, "review": result,
                                            "audit_in_prompt": False}
                for name, raw in originals.items():
                    manifest["sources"][f"audit/originals/{name}"] = _source_record(raw)
                manifest["sources"]["audit/review.json"] = _source_record(review_bytes)
            manifest["warnings"] = [{"line": d.line, "rule": d.rule, "message": d.msg}
                                    for d in warnings]
            (artifact / "manifest.json").write_text(
                json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            if output.exists():
                raise BuildError(f"output already exists: {output}")
            artifact.rename(output)
        return manifest
    except (OSError, UnicodeError, ValueError) as error:
        if isinstance(error, BuildError):
            raise
        raise BuildError(str(error)) from error


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren build",
        description="Validate/package a logic skill; optionally require a reviewed size reduction.")
    parser.add_argument("source", help="a SkillWren skill file, or a skill directory whose "
                        "flow files hold logic fragments (fragment set)")
    parser.add_argument("--out", required=True, help="new output directory (parent must exist)")
    parser.add_argument("--original", help="original skill for an optimized build")
    parser.add_argument("--review", help="reviewed requirement-map JSON")
    parser.add_argument("--original-context", action="append", default=[], metavar="FILE")
    parser.add_argument("--metric", choices=("tokens", "characters"), default="tokens")
    parser.add_argument("--tokenizer", default="cl100k_base")
    parser.add_argument("--max-ratio", type=float, default=1.0)
    args = parser.parse_args(argv)
    try:
        manifest = build(args.source, args.out, original=args.original, review=args.review,
                         original_context=args.original_context, metric=args.metric,
                         tokenizer=args.tokenizer, max_ratio=args.max_ratio)
    except BuildError as error:
        print(f"skillwren build: {error}", file=sys.stderr)
        return 1
    if manifest.get("mode") == "fragments":
        print(f"built {args.out}: fragment set, {len(manifest['checked_fragments'])} "
              f"fragment(s) checked, {len(manifest['sources'])} file(s), "
              f"{len(manifest['warnings'])} warning(s)")
        return 0
    print(f"built {args.out}: {len(manifest['contexts'])} context(s), "
          f"{len(manifest['sources'])} source(s) retained, {len(manifest['warnings'])} warning(s)")
    if "optimization" in manifest:
        comparison = manifest["optimization"]
        print(f"{comparison['original']['count']} -> {comparison['compiled']['count']} "
              f"{comparison['metric']}; {comparison['reduction_percent']}% reduction")
    return 0
