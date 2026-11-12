"""SkillWren validator (format 0.6, package 0.7): static checks for logic-first skills
and for logic blocks embedded in ordinary Markdown (fragments).

Stdlib-only. Usage: skillwren check [--fragment] [--explain] [--summary] [--audit] <file>...

Modules, in dependency order:
  syntax     lexical helpers, vocabulary, header profile reader
  document   fences, contract block (resources/always/never/inputs/order)
  schema     header schema (F1, B1, W7, W11)
  flowgraph  AST, CFG, dominators, must-dataflow (V1, O1, L1, L3, W9)
  ordering   `order:` rules over the CFG (P1)
  evidence   evidence classes and branch controllers (W15, --audit)
  analysis   per-flow checks (U1, E1-E4, T1-T2, R2-R4, A1-A2, M1, ...)
  files      skill/fragment validation and cross-file run resolution
  explain    plain-language text for every code
  cli        `skillwren check`

Rule IDs (SPEC Section 13):
  Errors: F1 frontmatter/schema, F2 fences/contract/body-order,
    F3 flow/fence set, V1 vocabulary, R1 requires match, R2 returns,
    R3 run target, R4 required-input gates, T1 for-each type,
    T2 run-argument type, U1 unbound reference,
    E1 effect target, E2 effect coverage, E3 immutable write,
    E4 impure apply, A1 allow/never, A2 ask/confirm structure,
    L1 label/loop, L2 recursion, L3 retry ownership,
    O1 otherwise/block structure, B1 budget, M1 mutation before ask,
    P1 order rule violated.
  Warnings: W1 trigger overlap, W2 system-may, W3 ask mapping, W4 appendix,
    W5 write-never-read, W6 effects unmatched, W7 unknown field,
    W8 foreign run (unverified effect boundary),
    W9 otherwise fall-through, W10 unreachable code,
    W11 body ceiling above default, W12 apply without appendix anchor,
    W13 order rule never applies, W14 fragment without logic,
    W15 order rule resting on self-report.

Token counts use ceil(chars/4), labeled approximate (SPEC Section 10);
`skillwren measure` gives exact counts.

Known limitations: run-argument types are checked only when the passed
binding has a known declared type; interpolated/wildcard paths are exempt
from the create/mutate overlap rule; dotted cross-skill runs are an
unverified effect boundary (W8); fragment inputs are inferred unless the
contract lists `inputs:`; order rules are checked per flow from its entry.
"""
import sys

from .analysis import analyze_flow, collect_flow_facts
from .document import parse_contract, parse_fences, read_contract
from .cli import USAGE, check_all, main
from .evidence import classify
from .explain import RULE_EXPLAIN
from .files import (Document, Workspace, audit, summarize, validate_file,
                    validate_files, validate_fragment)
from .flowgraph import build_cfg, build_tree, walk
from .schema import check_schema
from .syntax import (FORMAT_VERSION, Diag, match_resource, parse_block,
                     split_frontmatter, valid_type)

__all__ = ["Diag", "Document", "FORMAT_VERSION", "RULE_EXPLAIN", "USAGE",
           "Workspace", "analyze_flow", "audit", "build_cfg", "build_tree",
           "check_all", "check_schema", "classify", "collect_flow_facts",
           "main", "match_resource", "parse_block",
           "parse_contract", "parse_fences", "read_contract",
           "split_frontmatter", "summarize", "valid_type", "validate_file",
           "validate_files", "validate_fragment", "walk"]

if __name__ == "__main__":
    sys.exit(main(sys.argv))
