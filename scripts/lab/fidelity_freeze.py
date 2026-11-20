"""Validate and freeze human-reviewed requirement lists for the fidelity benchmark.

    py -3 scripts/lab/fidelity_freeze.py --validate     check every review file, freeze nothing
    py -3 scripts/lab/fidelity_freeze.py                 freeze the reviewed lists

Review files live in docs/current/research/fidelity-benchmark/review/<source>.md. Each
requirement is one line:

    - [x] CR-3 | obligation | Read the PR description first. | "Read PR description"

`[x]` keeps the line, `[ ]` drops it. Kinds: obligation, prohibition, exception, ordering,
authority, output. The quote must appear verbatim in the source (whitespace-normalized); a
requirement supported by several passages joins them with " ... ", each checked verbatim.
A verified quote proves the text exists, not that the requirement represents it: that is
the human reviewer's judgment;
a line whose quote is `inferred` records something the reviewer accepts without a source
span. Freezing refuses a file without `Reviewed by:` and `Date:` filled in, writes
frozen/<source>.json with the source and review digests, and never overwrites a frozen
file whose digests differ (re-freezing needs a new version).
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "docs" / "current" / "research" / "fidelity-benchmark"
KINDS = {"obligation", "prohibition", "exception", "ordering", "authority", "output"}
LINE = re.compile(r"^- \[( |x)\] ([A-Z]{2}-\d+) \| (\w+) \| (.+?) \| (.+)$")


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def parse(review):
    """(header, requirements, problems) for one review file."""
    text = review.read_text(encoding="utf-8")
    header = {k: (m.group(1).strip() if m else "") for k, m in
              (("source", re.search(r"^Source: (\S+)", text, re.M)),
               ("reviewed_by", re.search(r"^Reviewed by:(.*)$", text, re.M)),
               ("date", re.search(r"^Date:(.*)$", text, re.M)),
               ("candidate_status", re.search(r"^Candidate status:(.*(?:\n(?![-#\n]).*)*)", text, re.M)))}
    source = BENCH / header["source"] if header["source"] else None
    body = norm(source.read_text(encoding="utf-8")) if source and source.is_file() else None
    problems, items, seen = [], [], set()
    if body is None:
        problems.append(f"source not found: {header['source']}")
    for number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("- ["):
            continue
        m = LINE.match(line)
        if not m:
            problems.append(f"line {number}: not '- [x] ID | kind | requirement | \"quote\"'")
            continue
        keep, rid, kind, requirement, quote = m.groups()
        if rid in seen:
            problems.append(f"line {number}: duplicate ID {rid}")
        seen.add(rid)
        if kind not in KINDS:
            problems.append(f"line {number}: {rid} unknown kind {kind!r}")
        quote = quote.strip()
        inferred = quote == "inferred"
        if not inferred:
            if not (quote.startswith('"') and quote.endswith('"')):
                problems.append(f"line {number}: {rid} quote must be \"...\" or inferred")
            elif body is not None and any(norm(span) not in body for span in quote[1:-1].split(" ... ")):
                problems.append(f"line {number}: {rid} quote not found verbatim in the source"
                                " (each span of a ' ... '-joined quote must be)")
        items.append({"id": rid, "kept": keep == "x", "kind": kind, "requirement": requirement.strip(),
                      "quote": None if inferred else quote[1:-1], "inferred": inferred})
    return header, items, problems


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--validate", action="store_true", help="check the review files only")
    args = parser.parse_args(argv)
    reviews = sorted((BENCH / "review").glob("*.md"))
    failed = False
    for review in reviews:
        header, items, problems = parse(review)
        kept = [i for i in items if i["kept"]]
        if not args.validate:
            for field in ("reviewed_by", "date"):
                if not header[field] or header[field].startswith("<"):
                    problems.append(f"'{field.replace('_', ' ')}' is not filled in")
        status = "ok" if not problems else "PROBLEMS"
        print(f"{review.name}: {len(kept)} kept of {len(items)} ({status})")
        for p in problems:
            print(f"  {p}")
        failed |= bool(problems)
        if args.validate or problems:
            continue
        out = BENCH / "frozen" / f"{review.stem}.json"
        record = {"source": header["source"], "source_sha256": digest(BENCH / header["source"]),
                  "review_sha256": digest(review), "reviewed_by": header["reviewed_by"],
                  "date": header["date"],
                  "candidate_provenance": " ".join(header["candidate_status"].split()),
                  "requirements": kept,
                  "dropped": [i["id"] for i in items if not i["kept"]]}
        if out.is_file():
            old = json.loads(out.read_text(encoding="utf-8"))
            if (old["source_sha256"], old["review_sha256"]) != (record["source_sha256"], record["review_sha256"]):
                print(f"  refusing to overwrite {out.name}: it froze other bytes; move it aside first")
                failed = True
                continue
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"  frozen -> frozen/{out.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
