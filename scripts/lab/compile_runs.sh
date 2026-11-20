#!/usr/bin/env bash
# Compile-experiment runner (paid): one `skillwren compile` per named arm,
# all in parallel, each with its own usage log, stdout, and stderr.
#
#   scripts/lab/compile_runs.sh OUTDIR SOURCE_DIR ARM:LAYOUT[:noreverse]...
#
# SOURCE_DIR holds SKILL.md and optionally references/*.md (all passed as
# context). Example:
#   scripts/lab/compile_runs.sh runs src run3:fragments run4:inline
set -u
out=$1; src=$2; shift 2
contexts=()
for ref in "$src"/references/*.md; do
  [ -f "$ref" ] && contexts+=(--context "$ref")
done
mkdir -p "$out"
for arm in "$@"; do
  IFS=: read -r name layout flag <<<"$arm"
  extra=()
  [ "${flag:-}" = "noreverse" ] && extra+=(--no-reverse)
  (
    SW_ADAPTER_LOG="$out/$name-usage.jsonl" PYTHONPATH=src \
      py -3 -m skillwren compile "$src/SKILL.md" "${contexts[@]}" \
      --layout "$layout" "${extra[@]}" --out "$out/$name" --keep-failed "$out/$name-failed" \
      -- py -3 scripts/adapters/claude_compile.py \
      >"$out/$name-stdout.txt" 2>"$out/$name-stderr.txt"
    echo "exit $?" >>"$out/$name-stdout.txt"
  ) &
done
wait
