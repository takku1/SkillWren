"""Measure the complete emitted prompt against explicitly selected originals."""
import argparse
import json
import math
import sys


class MeasurementError(ValueError):
    """The requested comparison cannot be measured honestly."""


def compare(originals, compiled, metric="tokens", tokenizer="cl100k_base", max_ratio=1.0):
    if isinstance(max_ratio, bool) or not isinstance(max_ratio, (int, float)) \
            or not math.isfinite(max_ratio) or not 0 < max_ratio <= 1:
        raise MeasurementError("max_ratio must be finite, greater than zero, and at most 1")
    if not originals:
        raise MeasurementError("at least one original document is required")
    if metric not in ("tokens", "characters"):
        raise MeasurementError("metric must be tokens or characters")
    original_text = "\n\n".join(raw.decode("utf-8-sig") for raw in originals)
    compiled_text = compiled.decode("utf-8-sig")
    counter = len
    encoding_name = None
    if metric == "tokens":
        try:
            import tiktoken
            encoder = tiktoken.get_encoding(tokenizer)
        except Exception as error:
            raise MeasurementError(
                f"exact token measurement needs tiktoken and the {tokenizer!r} vocabulary; "
                "install skillwren[tokens] or explicitly select --metric characters"
            ) from error
        encoding_name = encoder.name
        # Skill text can contain literal special-token spellings as ordinary data.
        counter = lambda text: len(encoder.encode(text, disallowed_special=()))
    original_count, compiled_count = counter(original_text), counter(compiled_text)
    if original_count == 0:
        raise MeasurementError("the original context is empty")
    smaller = compiled_count < original_count
    return {
        "metric": metric, "tokenizer": encoding_name,
        "original": {"count": original_count, "bytes": sum(map(len, originals)),
                     "lines": sum(len(raw.decode("utf-8-sig").splitlines()) for raw in originals),
                     "files": len(originals)},
        "compiled": {"count": compiled_count, "bytes": len(compiled),
                     "lines": len(compiled_text.splitlines())},
        "saved": original_count - compiled_count,
        "ratio": compiled_count / original_count,
        "reduction_percent": round(100 * (original_count - compiled_count) / original_count, 2),
        "max_ratio": max_ratio, "smaller": smaller,
        "accepted": smaller and compiled_count <= original_count * max_ratio,
    }


def main(argv):
    parser = argparse.ArgumentParser(prog="skillwren measure",
        description="Compare an original skill with the complete expanded candidate prompt.")
    parser.add_argument("original")
    parser.add_argument("candidate")
    parser.add_argument("--original-context", action="append", default=[], metavar="FILE")
    parser.add_argument("--metric", choices=("tokens", "characters"), default="tokens")
    parser.add_argument("--tokenizer", default="cl100k_base")
    parser.add_argument("--max-ratio", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        from .compiler import _compile
        from .review import read_originals
        originals = read_originals(args.original, args.original_context)
        compiled, _ = _compile(args.candidate)
        report = compare(list(originals.values()), compiled, args.metric, args.tokenizer, args.max_ratio)
    except (OSError, ValueError) as error:
        print(f"skillwren measure: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        units = report["metric"]
        name = f" ({report['tokenizer']})" if report["tokenizer"] else ""
        print(f"{report['original']['count']} -> {report['compiled']['count']} {units}{name}; "
              f"{report['reduction_percent']}% reduction")
        print("meets size target" if report["accepted"] else "does not meet size target")
    return 0 if report["accepted"] else 1
