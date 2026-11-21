# Round 1 scores: awaiting adjudication

Ten artifacts scored once against the frozen **AI-reviewed baseline**
(88 requirements; not human-approved), judge Sonnet, $0.38:

- `skill-<source>.json`: the five published skill builds.
- `compiler-<source>.json`: the five drafts the compiler **refused** to
  publish, scored as diagnostics (`"publication": "refused (diagnostic)"`).
  Their fidelity is never combined with the compiler's publication rate
  (0/5).
- `<artifact>.coverage.json`: each preserved requirement's enforcement
  tier (no guard policy, so nothing is enforced; ambiguous mappings are
  their own category).

No comparison is published here. 18 judgments wait for adjudication, in
the `*.adjudication.md` sheets (every weakened, missing or unverified
verdict and every widening introduction): mark each line `[x]` agree or
`[!]` overturn, with a reason. Then, and only then:

```text
py -3 scripts/lab/fidelity_report.py scores/skill-*.json --out report-skill.json
py -3 scripts/lab/fidelity_report.py scores/compiler-*.json --out report-compiler-diagnostic.json
```

The report refuses while any line is unmarked. Whoever adjudicates is
named in each sheet; an AI adjudicator is labelled as one.
