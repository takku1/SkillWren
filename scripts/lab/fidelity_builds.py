"""Build every fidelity-benchmark source with both paths, once, before any scoring.

    py -3 scripts/lab/fidelity_builds.py OUT_DIR [--model sonnet]

Paths, both Sonnet:
- compiler: `skillwren compile <source>/SKILL.md --layout inline` through
  scripts/adapters/claude_compile.py (SW_COMPILE_MODEL and SW_JUDGE_MODEL both pinned);
- skill: a headless agent with only the skillwren plugin, asked to convert the source
  (scripts/lab/skill_build_live.py, two turns: request, then "Confirmed").

Pinned in OUT_DIR/manifest.json before anything runs: git commit, SkillWren version, source
and review digests, model, adapter and plugin skill digests, the exact commands and
prompts. Every raw output, log, cost and failure is kept; nothing is repaired, rerun or
scored here (the candidate requirement lists are not read). Spends model usage.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "docs" / "current" / "research" / "fidelity-benchmark"
SOURCES = ["code-reviewer", "full-stack", "webapp-testing", "theme-factory", "internal-comms"]
ADAPTER = ROOT / "scripts" / "adapters" / "claude_compile.py"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_build_live  # noqa: E402


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def skill_prompt(source):
    return (f"Use skillwren to convert the existing skill at ./source/{source}/SKILL.md into checked "
            f"SkillWren logic, written to ./{source}-logic. Keep the original unchanged.")


def compile_one(source, out, model):
    dest = out / "compiler"
    dest.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "SW_COMPILE_MODEL": model, "SW_JUDGE_MODEL": model,
           "SW_ADAPTER_LOG": str(dest / f"{source}-usage.jsonl")}
    argv = [sys.executable, "-m", "skillwren", "compile", str(BENCH / "sources" / source / "SKILL.md"),
            "--layout", "inline", "--out", str(dest / source), "--keep-failed", str(dest / f"{source}-failed"),
            "--", sys.executable, str(ADAPTER)]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    proc = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=ROOT, encoding="utf-8")
    (dest / f"{source}-stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (dest / f"{source}-stderr.txt").write_text(proc.stderr, encoding="utf-8")
    cost = 0.0
    log = dest / f"{source}-usage.jsonl"
    if log.is_file():
        for line in log.read_text(encoding="utf-8").splitlines():
            try:
                cost += json.loads(line).get("cost_usd") or 0.0
            except ValueError:
                pass
    built = (dest / source / "SKILL.md").is_file()
    return {"path": "compiler", "source": source, "exit": proc.returncode, "built": built,
            "artifact": f"compiler/{source}/SKILL.md" if built else None, "cost_usd": round(cost, 4),
            "started": started}


def skill_one(source, out, model):
    spec = {"files": {f"source/{source}/SKILL.md": BENCH / "sources" / source / "SKILL.md"},
            "turns": [skill_prompt(source), skill_build_live.CONFIRM],
            "expect": [], "build": f"{source}-logic"}
    dest = out / "skill"
    dest.mkdir(parents=True, exist_ok=True)
    record = skill_build_live.run_scenario(source, spec, model, dest)
    s = record["score"]
    rel = f"skill/{source}-{model}/files/{s['packages'][0]}/SKILL.md" if s["packages"] else None
    return {"path": "skill", "source": source, "built": bool(s["packages"]), "artifact": rel,
            "packages": s["packages"], "nothing_written_before_confirmation": s["nothing_written_before_confirmation"],
            "check": s.get("check"), "cost_usd": record["cost_usd"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--paths", nargs="+", choices=["compiler", "skill"], default=["compiler", "skill"],
                        help="which build paths to run (round 2 reruns only the compiler)")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        sys.exit(f"{out} is not empty: builds run once into a fresh folder")
    out.mkdir(parents=True, exist_ok=True)
    import skillwren
    manifest = {
        "purpose": "fidelity benchmark builds, made before the requirement lists were frozen; not scored here",
        "started": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(git("status", "--porcelain", "--", "src", "scripts", "plugin")),
        "skillwren_version": skillwren.__version__, "model": args.model,
        "sources": {s: sha(BENCH / "sources" / s / "SKILL.md") for s in SOURCES},
        "compiler": {"command": "skillwren compile <source>/SKILL.md --layout inline --out <dir> --keep-failed <dir> -- "
                                "python scripts/adapters/claude_compile.py",
                     "SW_COMPILE_MODEL": args.model, "SW_JUDGE_MODEL": args.model,
                     "adapter_sha256": sha(ADAPTER), "context": "SKILL.md only (benchmark scope)"},
        "skill": {"plugin_skill_sha256": sha(ROOT / "plugin" / "skillwren" / "SKILL.md"),
                  "harness_sha256": sha(Path(__file__).parent / "skill_build_live.py"),
                  "turns": [skill_prompt("<source>"), skill_build_live.CONFIRM]},
        "paths": args.paths,
        "rules": "one build per source and path; failures kept; no repair, rerun or scoring",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with ThreadPoolExecutor(max_workers=5) as pool:
        jobs = [pool.submit(compile_one, s, out, args.model) for s in SOURCES] if "compiler" in args.paths else []
        jobs += [pool.submit(skill_one, s, out, args.model) for s in SOURCES] if "skill" in args.paths else []
        results = []
        for job in jobs:
            try:
                results.append(job.result())
            except Exception as error:  # keep the failure, do not retry
                results.append({"error": repr(error)})
    manifest["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    manifest["results"] = results
    manifest["cost_usd_total"] = round(sum(r.get("cost_usd") or 0 for r in results), 4)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for r in results:
        print(json.dumps({k: r.get(k) for k in ("path", "source", "built", "exit", "cost_usd", "error") if k in r}))
    print(json.dumps({"builds": len(results), "built": sum(bool(r.get("built")) for r in results),
                      "cost_usd": manifest["cost_usd_total"]}))


if __name__ == "__main__":
    main()
