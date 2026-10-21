"""Check manual requirement-review records without claiming prose equivalence."""
import hashlib
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_originals(original, supporting=()):
    entry = Path(original).resolve()
    originals = {entry.name: entry.read_bytes()}
    seen_paths = {entry}
    for reference in supporting:
        path = Path(reference).resolve()
        try:
            name = path.relative_to(entry.parent).as_posix()
        except ValueError:
            raise ValueError(f"original context must be inside {entry.parent}: {reference}") from None
        if path in seen_paths or name in originals:
            raise ValueError(f"duplicate original context: {name}")
        seen_paths.add(path)
        originals[name] = path.read_bytes()
    return originals


def validate_review(originals, candidate, compiled, review):
    if not isinstance(review, dict):
        raise ValueError("review must be a JSON object")
    first = next(iter(originals))
    if review.get("original_sha256") != digest(originals[first]):
        raise ValueError("original changed: review the conversion before building")
    expected_context = {name: digest(raw) for name, raw in list(originals.items())[1:]}
    if review.get("original_context_sha256", {}) != expected_context:
        raise ValueError("original context changed or does not match the reviewed files")
    if review.get("logic_sha256") != digest(candidate):
        raise ValueError("candidate changed: update its requirement review before building")
    requirements = review.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("review must contain a nonempty requirements list")
    text = compiled.decode("utf-8-sig")
    lines = {name: raw.decode("utf-8-sig").splitlines() for name, raw in originals.items()}
    covered = {name: set() for name in originals}
    seen = set()
    for item in requirements:
        if not isinstance(item, dict):
            raise ValueError("every reviewed requirement must be an object")
        name = item.get("id")
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError("requirement ids must be nonempty and unique")
        seen.add(name)
        source = item.get("original_file", first)
        if not isinstance(source, str) or source not in originals:
            raise ValueError(f"unknown original file for requirement {name!r}")
        span = item.get("original_lines")
        if not isinstance(span, list) or len(span) != 2 \
                or any(type(number) is not int for number in span) \
                or not 1 <= span[0] <= span[1] <= len(lines[source]):
            raise ValueError(f"invalid original line span for requirement {name!r}")
        anchors = item.get("logic_contains")
        if not isinstance(anchors, list) or not anchors \
                or any(not isinstance(anchor, str) or not anchor.strip() or anchor not in text
                       for anchor in anchors):
            raise ValueError(f"missing compiled instruction anchor for requirement {name!r}")
        covered[source].update(range(span[0], span[1] + 1))
    for source, source_lines in lines.items():
        missing = [i for i, line in enumerate(source_lines, 1) if line.strip() and i not in covered[source]]
        if missing:
            raise ValueError(f"unmapped original lines in {source}: {missing}")
    return {"kind": "manual-requirement-review", "requirements": len(seen),
            "original_files": list(originals), "semantic_equivalence_proven": False}
