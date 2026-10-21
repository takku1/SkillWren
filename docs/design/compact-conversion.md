# Compact skill conversion

SkillWren's primary workflow is a human/agent-authored conversion of an original
SKILL.md into a smaller, explicit control flow. The compiler checks the result;
it does not infer equivalent procedures by deleting or summarizing prose.

## Acceptance criteria

- The compiled instruction text is statically valid SkillWren.
- An optimized build is strictly smaller than the declared original context,
  measured with the same explicit metric on both sides. The default is exact
  cl100k_base tokenization; character counts are a separately labeled option.
- All declared original files have reviewed requirement mappings. Hashes bind
  the review to the original inputs and candidate; stale or incomplete maps fail.
- Original bytes and review records live in the manifest, outside the prompt.
- Measure expanded context, not just the authoring file. No automatic truncation,
  unreported reference removal, or universal compression target.
- Existing check, plain build, context imports, and conform remain compatible.

## Ownership and contracts

- `metrics.py`: consistent counts and comparison; optional tokenizer dependency,
  with no silent estimate fallback. It owns the `measure` CLI.
- `review.py`: review schema, input digests, source spans, and requirement anchors.
  It verifies review bookkeeping, not semantic equivalence or model behavior.
- `compiler.py`: validate and stage the final artifact, apply optional optimization
  acceptance checks, archive inputs, then publish a new output directory.
- Authoring guidance and the reusable conversion skill: perform the semantic
  rewrite, retain constraints/examples needed for decisions, and review parity.

`build(source, output)` remains a packaging operation. Optional original/review
arguments enable the stricter optimization contract. No LLM calls or paid
sessions are added. Review records use the existing TECHNologic field names
where possible so the proven local conversion can be checked by the core tool.

## Work and evidence

1. Implement measurement and review validation with failure tests for equal or
   expanded candidates, stale digests, missing requirements, and opaque context.
2. Integrate the optimized-build gate before output publication; exercise both
   API and CLI, including preservation of existing build behavior.
3. Ship a small, fully mapped conversion example and a conversion skill. Rework
   README, authoring, compiler guidance, and current spec claims around this path.
4. Run the complete offline suite plus the existing TECHNologic integration tests.

Optional exact tokenization can need a vocabulary download. Missing dependencies
or tokenizer failures are errors when exact tokens were requested. Large original
reference sets must be declared explicitly; the tool cannot know which documents
an LLM would have loaded. An approved mapping is evidence of a human review,
not a theorem about prose or proof that a model follows the resulting language.
