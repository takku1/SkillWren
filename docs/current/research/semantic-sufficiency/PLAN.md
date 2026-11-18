# Semantic sufficiency: research plan (2026-11-17)

Follow-up design: [risk-constrained selection formulation](FORMULATION.md)
and [working notes](NOTES.md). These extend the research program; the
existing pilot and main-run preregistration retain their original scoring
and decision rules.

First real certification study (draft, unexecuted): [FS-01 full-stack
representation preregistration](select-fs01/PREREGISTRATION.md) with a
[schema-2 study skeleton](select-fs01/study.json). It tests the new
inline-logic form against the original skill content and the FS-009
brief; placeholder hashes and empty samples must be replaced with frozen
artifacts and collected observations before the single `select` call.

Question: which parts of a skill's text actually carry the behaviour a task
needs, and what is the smallest representation that keeps that behaviour,
for a given model and task? This is a research track beside SkillWren's
checker and guard, which stay unchanged.

## Why behaviour, not similarity

Prompt-compression research mostly scores reconstructed meaning or
downstream task accuracy. Agent skills fail differently: a short skill
can complete the task while silently dropping a side constraint. Recent
work fits that worry:

- Prompt compression families (survey, NAACL 2025): hard-prompt token
  pruning (Selective Context, LLMLingua, LongLLMLingua, LLMLingua-2) and
  soft-prompt methods (gist tokens, ICAE, 500x-style compressors) that need
  model access, so only hard-prompt methods apply to hosted agents.
- CDCT (arXiv 2512.17920): constraint compliance is U-shaped in prompt
  length across nine models; medium compression violates most. Scored by
  an LLM jury, factual prompts only.
- Compact constraint encoding (arXiv 2604.07192): compact headers cut
  constraint tokens about 71% with no significant compliance change
  across 11 models, but counter-intuitive constraints fail 10-100%.
- Lost in context compaction (arXiv 2608.11242): side constraints are
  dropped when context is compacted; prompt wording alone helped little.
- Instruction stacking collapse (arXiv 2608.02639): follow rates fall as
  constraints accumulate; an instruction compiler helped weaker models and
  was neutral-to-negative for stronger ones.
- ContextCite (arXiv 2409.00729), AttriBoT, JoPA: counterfactual context
  attribution by ablating sentences and fitting a sparse surrogate; scored
  on the likelihood of the original output, not on whether it was right.

SkillWren's opening: score ablations and compressions on executable,
host-checked obligations (did it edit a forbidden file, is the report
backed by the real check), which none of the above do.

## Lessons from our own nulls

Every comparison so far (72 skill-form runs, 90+90 A/B/C trials, 48
preregistered repair runs) hit a ceiling. A task only discriminates when
the compliant path is costly and the shortcut cheap. So the first step is
a task where removing one sentence visibly changes behaviour; without it,
every compression result is vacuous.

## Program

1. **Discriminating task (pilot running):** `scripts/sufficiency_lab.py`.
   The skill says the audit is read-only; the user asks to make it pass.
   Units: run, readonly, blocked, report, nofake, final. Pilot variants:
   full, -readonly, -blocked, -readonly-blocked on Haiku and Sonnet.
   Success criterion: full is compliant and an ablation is not.
2. **Leave-one-out attribution:** drop each unit; the behavioural weight of
   a unit is the change in compliance it causes (with intervals). Pairs of
   units test redundancy (two units that only matter together).
3. **Compressor comparison at matched outcomes:** the same skill as full
   prose, human-concise prose, SkillWren logic (`never:` invariant),
   contrastive rules ("read-only != fix it"), LLMLingua-2 at two rates, and
   the minimal sufficient unit set from step 2. Score compliance and cost.
4. **Risk-weighted redundancy:** for units with high behavioural weight,
   test whether repetition or structural enforcement (guard) is cheaper
   than more words.

Deferred until 1-3 give a non-null signal: model-specific encodings,
dependency graphs over requirements, progressive loading. All three need a
measurement that can see a difference first.

## Rules carried over

Outcomes are scored deterministically by the host; model judges are not
used for primary outcomes. Task success, procedural adherence and
authorized effects are separate measures; none substitutes for another
(the protocol-1 A/B/C artefact showed completion can reward deviation).
Variants and hypotheses are fixed before a main run; pilots only check
that the task discriminates.
