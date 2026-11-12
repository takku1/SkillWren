# SkillWren research and implementation review

Date: 2026-10-21. Baseline: `d2735af` (0.5.0 documentation).

Follow-up: the [November review](research-review-2026-11.md) applies this
framework to full-stack field report 3 and recent procedure-following and
runtime-enforcement work, and records what format 0.6 changed. Section
references below to the SPEC predate 0.6.

This is a literature-informed engineering review and a proposed experimental
program, not a completed empirical study or a proof of soundness. The local
experiments below use synthetic sessions; no paid model experiments were run.

## Research question

Can a compact language for agent procedures preserve the complete instructional
context of a skill while improving readability, checking, and execution
reliability? The goal is not merely a shorter prompt. It is a representation
with explicit control flow, intact domain knowledge, and measurable fidelity.

Three distinct claims must be tested separately:

1. **Representation:** all source material and requirements survive conversion.
2. **Analysis:** the checker correctly reasons about the represented program.
3. **Execution:** the host/model follows that program and achieves its task.

A success at one layer does not establish the next. Section 16 of the existing
SPEC already correctly says that hosts read the logic as instructions; they
do not execute it. That qualification should govern the project's claims.

## Relationship to established research

| Research | Relevant result or method | Implication for SkillWren |
|---|---|---|
| [Hoare, 1969](https://www.cs.ox.ac.uk/publications/publication8205-abstract.html) | Program reasoning connects preconditions, statements, and postconditions through defined semantics. | A prose `verify` is not a proved predicate. Separate deterministic checks from model judgments. |
| [Cousot and Cousot, 1977](https://www.di.ens.fr/~cousot/COUSOTpapers/POPL77.shtml) | Abstract interpretation relates an approximate analysis to concrete computations. | Define the concrete transition system and approximation relation before calling the checker sound. |
| [SkillsBench, v1](https://arxiv.org/html/2602.12670v1) | Across diverse tasks, curated skills help on average but can hurt; harness behavior matters. Its limitations explicitly call for stronger length-matched controls. | Compare representations with matched content and measure actual loading, not just availability. |
| [SWE-Skills-Bench, v1](https://arxiv.org/html/2603.15401v1) | Reports limited average improvement in its SWE setting, with many ineffective skills and context interference. The study uses one model/harness configuration. | Do not generalize either its negative results or SkillsBench's gains to SkillWren. Test domain, model, and harness interactions. |
| [Rabanser et al., ICML 2026](https://arxiv.org/html/2602.16666v3) | Distinguishes consistency, robustness, predictability, and safety from average task success. | Repeated trials, perturbations, failure severity, and abstentions belong in the evaluation. |
| [AgentDojo, 2024](https://arxiv.org/html/2406.13352v3) | Evaluates agent utility and adversarial manipulation through untrusted tool data. | Test contract adherence under hostile documents/tool outputs, alongside benign task completion. |
| [LLMLingua, EMNLP 2023](https://aclanthology.org/2023.emnlp-main.825/) | Prompt compression is evaluated through downstream performance, with empirical tradeoffs. | Do not equate token deletion or approximate quality retention with lossless context preservation. |
| [Lost in the Middle, TACL 2024](https://aclanthology.org/2024.tacl-1.9/) | In the studied settings, performance depends on where relevant information occurs in context. | Keeping all text is necessary for source fidelity but does not ensure the model uses it. Test placement and retrieval. |

The two skills benchmarks address different populations and experimental
conditions. Their reported averages are not competing estimates of a single
universal effect. The defensible conclusion is heterogeneity, not that skills
always work or never work. Recent arXiv versions should be pinned in any
replication; this review does not assume all preprints are independently
validated.

## What the current pilots establish

The preserved [round 1](../../../benchmarks/benchmark-report.md) and
[round 2](../../../benchmarks/benchmark-report-r2.md) reports describe one paired
comparison per round, one model, parent-authored targets and scoring, and
simulated interactive questions. Both representations find eight seeded
issues in each round. The logic skill loads substantially fewer bytes.
Those are useful observations.

They do **not** isolate a causal benefit of syntax:

- The original and rewritten skills have different content and reference
  loading behavior. Round 1 omits report elements present in the original.
- Round 2 changes the target as well as the logic skill's rubric, gate, and
  report requirements. An improvement between rounds cannot distinguish
  content effects, syntax effects, target difficulty, or sampling variation.
- Eight findings within one generated report are not eight independent agent
  runs. Treating them as such would be pseudoreplication.
- Severity agreement measures agreement with this rubric, not universal
  security severity. Round 2 explicitly acknowledges a defensible alternative
  grade and a missed unseeded authorization problem.
- A self-reported step trace or `WOULD-ASK` is not independent evidence that
  real confirmation, refusal, or recovery behavior worked.
- `ceil(chars/4)` is a labeled estimate. It cannot support a model-specific
  tokenizer claim, particularly across code, punctuation, and non-English text.

Thus the phrase “attribution confirmed” should be treated as an historical
interpretation, not a validated conclusion. The archive should remain intact;
current summaries should state the narrower inference.

## Static analysis: useful structure, incomplete semantics

The validator implements an indentation AST, control-flow graph,
reachability/dominators, definite binding, and transitive same-skill mutation
propagation. This is a meaningful advance over checking prose for keywords.
The mutation catalog is a useful regression oracle for those implemented rules.

However, the analysis is not a proof about arbitrary agent behavior:

- `allow` matches a `never` using content-word overlap. Shared words do not
  establish logical implication or even compatible polarity.
- Gate predicates and transformations are mostly prose. There is no defined
  denotation for “the result is correct” or an arbitrary `apply` operation.
- Cross-skill effects are warned as unverified. Locals with unknown types skip
  some type checks. Both are documented open boundaries, not established safety.
- Mutation ordering can be checked structurally, but the model may perform a
  different action than the modeled node. The host needs an enforcement bridge.
- A returned binding can have the right name and still contain wrong evidence.
  Provenance, value refinements, and independent verifier results are distinct
  from definite assignment.
- Terminating paths are checked, but general termination and bounded repair
  loops are not established by the existence of a reachable return.

Recommended formal core: states `(pc, bindings, approvals, effects, evidence)`;
explicit transitions for reads, generation, verification, calls, branching,
and commits; and a finite abstract domain for initialization, types, effects,
and approval scope. Unknown effects must remain unknown rather than empty.
A proof obligation should state precisely which represented traces are
covered and which model/host assumptions remain outside the theorem.

## Reproduced engineering faults and repairs

See [runtime tests](../../../tests/test_conform.py) and
[input tests](../../../tests/test_input_robustness.py). Regressions were run against
the original behavior before fixes; further tests cover related boundaries.

| Fault | Consequence | Change |
|---|---|---|
| Return code/result status ignored | Failed or incomplete sessions could be labeled conforming | Require successful exit and a successful terminal result |
| Git status used as the observation oracle | Ignored files and committed mutations disappear | Compare before/after file hashes independently of the Git index |
| Human-oriented Git filename parsing | Quoted/non-ASCII paths misclassified | Observe filesystem paths directly |
| Installed skill directory excluded | Self-modification invisible | Include installed skill files in observations |
| Existing `.git` copied | Worktree pointers/history/hooks can contaminate setup | Exclude Git metadata when copying input trees |
| Input `.gitignore` overwritten | Workspace semantics changed before the experiment | Preserve the original ignore file |
| JSON followed by a plaintext verdict | `--json` is not parseable as one document | Put the verdict inside the JSON report |
| Environment exceptions escape | Traceback instead of documented exit 2 | Handle file/process/input errors at the CLI boundary |
| Invalid header maps analyzed anyway | `accepts`/`produces` lists crash map dereferences | Stop semantic analysis after structural/schema failures |
| Duplicate header keys silently overwrite | Ambiguous declarations pass | Reject duplicate keys in indented header maps |
| Nested objects in textual lists accepted | Invalid routing metadata; possible downstream type failures | Validate list element types and filter invalid batch triggers |
| Platform-default decoding | Platform-dependent interpretation | Explicit UTF-8 with optional BOM; invalid encoding yields diagnostics |

The new observer hashes contents, file modes, and link targets. It detects
final additions, removals, and modifications, including ignored files. Its
cost is linear in bytes scanned twice; large workspaces should be selected
deliberately. It does not capture changes reverted before the final snapshot.

## Remaining runtime limits

`conform` is an observation harness, not an OS sandbox or trace verifier.
It does not establish absence of network requests, external writes, transient
writes, empty-directory changes, or Git metadata changes. A preserved symbolic
link is not containment; the model can follow it. Read access is not audited.
Creates and mutates currently share a union of globs, so their distinct effect
semantics are not enforced at runtime.

Fresh `CLAUDE_CONFIG_DIR` alone is not a complete isolation argument. Project
configuration and host-managed behavior remain relevant. The official
[Claude programmatic-use documentation](https://code.claude.com/docs/en/headless)
describes project discovery under `-p` and a newer bare mode with different
authentication/loading behavior. Adopting that mode needs a pinned CLI version
and integration tests; blindly adding it would change profile authentication
and skill discovery. The previous claim of complete isolation is removed.

The official [Git status documentation](https://git-scm.com/docs/git-status)
explains ignore handling and filename representations. Switching to `-z`
would repair parsing, but would not fix commit/index-dependent observation;
that is why this patch uses a separate snapshot.

## Experiment that would answer the language question

Pre-register the primary hypothesis: with content held constant, the language
reduces observed procedure violations without unacceptable task-quality loss.
Measure compression separately. A proposed initial design is 30 task families,
six conditions, three fixed model/harness combinations, and ten repeated runs
per cell: 5,400 sessions before adversarial extensions. This is a planning
quantity, not a power calculation or a claim that ten runs suffice.

Conditions:

1. No skill (baseline task instructions only).
2. Complete original prose skill and references.
3. Edited concise prose with independently audited requirement equivalence.
4. SkillWren language with exactly the same requirements and domain content.
5. Condition 4 plus deterministic host-side enforcement of a supported subset.
6. Condition 4 with all context expanded, to measure any selective-loading loss.

For representation comparisons, hold the rubric, examples, tool access,
budgets, acceptance tests, and context placement as constant as possible.
Where exact length matching conflicts with equivalent meaning, report both
the mismatch and a separate length-controlled analysis; do not silently remove
requirements. Split task families into development and sealed evaluation
sets before revising the language or prompts.

Randomize condition order within task/model blocks. Pin source/skill hashes,
model identifiers, CLI versions, system prompt, permissions, settings, budgets,
and dataset revisions. Keep failures, timeouts, missing evidence, and abstentions
in the accounting. Run verifiers out of reach of the evaluated agent.

Primary outcomes are task pass rate and independently observed constraint
violations. Secondary outcomes include source retention, requirement coverage,
context-load completeness, false alarms, refusal accuracy, cost, latency,
token counts, and reproducibility across trials. Report effect sizes and
uncertainty clustered by task family, rather than counting each finding or
repeat as a new independent task. Determine final sample size from pilot
variance and a predeclared practically meaningful effect.

Adversarial cells should include ambiguous approval, revoked approval, missing
resources, conflicting instructions, malicious tool text, stale evidence,
retry exhaustion, nested calls, Unicode paths, symlinks, partial writes,
write-then-revert, timeout, and wrong-but-well-typed outputs. Evaluate utility
as well as safety so blanket refusal cannot win the benchmark.

## Recommended research contribution

The strongest plausible contribution is a **context-preserving intermediate
language for agent procedures**, with a small formal control core, explicit
evidence/authority boundaries, and multiple host backends. A terse syntax by
itself is unlikely to be the important novelty.

The [language design](../language-design.md) specifies
what preservation means, how source context connects to control nodes, and
which promises need a compiler, a verifier, or empirical evidence. The research
program should be judged by those explicit obligations, not a universal
compression ratio or a few successful demonstrations.

An [initial Markdown compiler](../compiler.md) now implements exact source
retention and full expansion of declared context. It reuses the existing
control-language checks and distinguishes opaque examples/data from executable
blocks. This is an implementation of the retention layer, not empirical
evidence that models preserve every requirement or proof of the proposed
stronger type/effect semantics. The compiler tests include deterministic builds,
exact byte spans, missing dependencies, and budget failure without truncation.
