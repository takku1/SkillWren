"""Score a built skill against a source skill's frozen requirements: preservation and
introduction, reported separately (execution is a separate harness).

    py -3 scripts/lab/fidelity_score.py SOURCE_ID BUILT_SKILL.md [--candidates] [--out FILE]

- preservation: each frozen requirement is preserved, weakened or missing in the built
  skill. The judge must quote the built skill; a quote that is not found verbatim makes the
  verdict "unverified" (counted as not preserved).
- introduction: obligations, prohibitions, orderings or permissions in the built skill that
  the source never stated or authorized, each with a quote, and whether it widens what the
  agent may do (a permission or an effect) or only narrows it.

The judge is a model (`claude -p`, Sonnet): label results as model-judged. `--candidates`
scores against the unreviewed candidate list and stamps the result so; without it, the
frozen (human-reviewed) list is required. Spends model usage (about $0.05-0.15 per call).
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "docs" / "current" / "research" / "fidelity-benchmark"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fidelity_freeze import parse  # noqa: E402

SYSTEM = """You audit a translation of an agent skill. You get the SOURCE skill (natural
language), the BUILT skill (SkillWren: logic blocks, contract, step meanings, tables), and a
numbered list of the source's REQUIREMENTS.

For each requirement decide, from the BUILT skill alone:
- preserved: the built skill requires the same thing with the same strength and scope
  (same condition, same timing or order, same who-decides). Prose in step meanings or
  tables counts if the procedure points to it.
- weakened: present but softer, narrower, conditional where the source was not, moved
  later than the source requires, or turned from a rule into a suggestion.
- missing: not present.
Quote the exact built-skill text you relied on (copy it character for character, at most
200 characters). For missing, quote nothing.

Then list what the BUILT skill introduces that the SOURCE never stated or implied: new
obligations, prohibitions, orderings, questions to the user, effects (files written,
commands run) or permissions. Quote each. Mark widens=true when it lets the agent do
more than the source authorized (a new effect or permission), false when it only adds a
constraint. Do not list restatements or formatting of source requirements."""

SCHEMA = {
    "type": "object",
    "properties": {
        "requirements": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string"},
                           "verdict": {"type": "string", "enum": ["preserved", "weakened", "missing"]},
                           "quote": {"type": "string"}, "reason": {"type": "string"}},
            "required": ["id", "verdict", "quote", "reason"]}},
        "introduced": {"type": "array", "items": {
            "type": "object",
            "properties": {"behavior": {"type": "string"}, "quote": {"type": "string"},
                           "widens": {"type": "boolean"}},
            "required": ["behavior", "quote", "widens"]}},
    },
    "required": ["requirements", "introduced"],
}


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def requirements(source_id, candidates):
    if candidates:
        header, items, problems = parse(BENCH / "review" / f"{source_id}.md")
        if problems:
            sys.exit(f"review file has problems: {problems}")
        return header["source"], [i for i in items if i["kept"]], "candidates (unreviewed, model-drafted)"
    frozen = BENCH / "frozen" / f"{source_id}.json"
    if not frozen.is_file():
        sys.exit(f"no frozen requirements for {source_id}: review and freeze first, or pass --candidates")
    data = json.loads(frozen.read_text(encoding="utf-8"))
    # The answer key is only valid for the bytes it was frozen against.
    for rel, key in ((data["source"], "source_sha256"), (f"review/{source_id}.md", "review_sha256")):
        actual = hashlib.sha256((BENCH / rel).read_bytes()).hexdigest()
        if actual != data[key]:
            sys.exit(f"{rel} changed since it was frozen ({key} differs): scoring would compare a "
                     "different text against the old answer key. Start a new benchmark revision: "
                     "move frozen/" + f"{source_id}.json aside, review again, and re-freeze.")
    return data["source"], data["requirements"], f"frozen, reviewed by {data['reviewed_by']} on {data['date']}"


def judge(source_text, built_text, reqs, model):
    prompt = ("SOURCE skill:\n```\n" + source_text + "\n```\n\nBUILT skill:\n```\n" + built_text
              + "\n```\n\nREQUIREMENTS:\n" + "\n".join(f"{r['id']} ({r['kind']}): {r['requirement']}" for r in reqs))
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(SYSTEM)
        system_file = f.name
    argv = [shutil.which("claude"), "-p", "--output-format", "json", "--model", model,
            "--system-prompt-file", system_file, "--json-schema", json.dumps(SCHEMA),
            "--setting-sources", "", "--strict-mcp-config", "--no-session-persistence",
            "--tools", "", "--max-turns", "3"]
    proc = subprocess.run(argv, input=prompt, capture_output=True, text=True, encoding="utf-8", timeout=900)
    Path(system_file).unlink(missing_ok=True)
    data = json.loads(proc.stdout)
    return data.get("structured_output") or json.loads(data["result"]), data.get("total_cost_usd", 0)


def adjudication(result):
    """The judgments most likely to be wrong in a way that matters, for a human to check."""
    lines = [f"# Adjudication: {result['source']}", "",
             f"Built: `{result['built']}`. Judge: {result['judge']}. Basis: {result['basis']}.", "",
             "Mark each line [x] agree or [!] overturn, with a reason.", "", "## Requirement verdicts", ""]
    for r in result["requirements"]:
        if r["verdict"] != "preserved":
            lines.append(f"- [ ] {r['id']} ({r['kind']}): judge says {r['judge_verdict']}"
                         f"{' (quote not found: unverified)' if r['verdict'] == 'unverified' else ''}. "
                         f"{r['reason']} Quote: \"{r['quote'][:200]}\"")
    lines += ["", "## Introduced behavior that widens what the agent may do", ""]
    for i in result["introduced"]:
        if i["widens"]:
            lines.append(f"- [ ] {i['behavior']} Quote: \"{i['quote'][:200]}\"")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source_id")
    parser.add_argument("built")
    parser.add_argument("--candidates", action="store_true", help="score against the unreviewed candidates")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--out")
    parser.add_argument("--adjudication", metavar="FILE",
                        help="write a Markdown sheet of every weakened, missing or unverified verdict and "
                             "every widening introduction, for a human to confirm or overturn")
    args = parser.parse_args(argv)
    source_rel, reqs, basis = requirements(args.source_id, args.candidates)
    source_text = (BENCH / source_rel).read_text(encoding="utf-8")
    built_text = Path(args.built).read_text(encoding="utf-8")
    verdicts, cost = judge(source_text, built_text, reqs, args.model)
    body = norm(built_text)
    by_id = {v["id"]: v for v in verdicts["requirements"]}
    rows = []
    for r in reqs:
        v = by_id.get(r["id"], {"verdict": "missing", "quote": "", "reason": "judge returned no verdict"})
        verdict = v["verdict"]
        if verdict != "missing" and (not v["quote"].strip() or norm(v["quote"]) not in body):
            verdict = "unverified"
        rows.append({"id": r["id"], "kind": r["kind"], "verdict": verdict, "judge_verdict": v["verdict"],
                     "quote": v["quote"], "reason": v["reason"]})
    introduced = [dict(i, quote_found=bool(i["quote"].strip()) and norm(i["quote"]) in body)
                  for i in verdicts["introduced"]]
    counts = {k: sum(r["verdict"] == k for r in rows) for k in ("preserved", "weakened", "missing", "unverified")}
    result = {
        "source": args.source_id, "built": str(args.built), "basis": basis, "judge": f"model ({args.model})",
        "preservation": {"total": len(rows), **counts,
                         "rate": round(counts["preserved"] / len(rows), 3) if rows else None},
        "introduction": {"total": len(introduced), "widening": sum(i["widens"] for i in introduced),
                         "unquoted": sum(not i["quote_found"] for i in introduced)},
        "requirements": rows, "introduced": introduced, "cost_usd": round(cost or 0, 4),
    }
    text = json.dumps(result, indent=2)
    if args.adjudication:
        Path(args.adjudication).write_text(adjudication(result), encoding="utf-8")
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("source", "basis", "preservation", "introduction", "cost_usd")}, indent=1))


if __name__ == "__main__":
    main()
