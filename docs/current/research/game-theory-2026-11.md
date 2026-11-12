# Game theory for checked agent procedures

Date: 2026-11-12. Scope: which results from game theory, contract theory, and
related formal work bear on SkillWren, distilled to what changes the design.
Companion to the [November research review](research-review-2026-11.md).
Literature claims below come from the cited papers' abstracts, publisher
pages, and summaries; proofs were not re-derived here.

## The setting, stated as a game

A skill is written by a **principal** (the author or the user) and carried out
by an **agent** (the model). The agent's actions are partly hidden: the
principal sees final files, some command output, and the agent's own report.
The agent is not assumed malicious, but its choices are not the principal's:
it optimizes something correlated with the principal's goal (finish the task,
pass the visible checks), and it skips steps that nothing observes. Field
evidence matches this: full-stack's FS-015 passed 7/7 hidden outcome checks
while skipping the stack records, the assurance table, and the guard, and
field report 3 found the assurance screen skipped in two of two live builds.
Procedure benchmarks report 27-50% compliance with completed tasks
(SOPBench, SOP-Bench).

Three further parties matter: a **verifier** (the static checker, a guard
script, a reviewer, `conform`), the **user** who holds decision rights, and
**other workers** sharing a repository.

## Results that change the design

### 1. Moral hazard and the informativeness principle

Hidden action is moral hazard. Holmström's informativeness principle (Bell
Journal of Economics, 1979) says an optimal contract conditions on every
signal that is informative about the agent's action. In skill terms: a
required step that leaves no signal cannot be contracted on at all. Saying
"apply the assurance screen" adds an instruction but no observable; the
principal cannot tell compliance from omission.

**Design consequence.** Every step that an `order:` rule depends on should
leave a signal: an executed command with an exit status, a written artifact,
or a user decision. SkillWren 0.7 grades each gate and each order-rule anchor
by evidence class and warns (W15) when a rule rests only on the agent's own
judgment.

### 2. Multitask incentives (Holmström and Milgrom, 1991)

When an agent splits effort across tasks and only some are measured, rewarding
the measured ones pulls effort away from the rest; job design (which tasks
are grouped and what is measured) becomes the main instrument
([JLEO 7, 24-52](https://people.duke.edu/~qc2/BA532/1991%20JLEO%20Holmstrom%20Milgrom.pdf)).
This is the FS-015 pattern exactly: outcome checks were measured and passed;
process steps were not measured and were skipped.

**Design consequence.** Measure process and outcome as separate results in
evaluations (full-stack FS-016 already lists "check meaningfulness" and
"scope honesty"; add "required steps observed" as a primary measure). In
skills, give process steps their own observable rather than relying on
outcome checks to imply them.

### 3. Cheap talk versus verifiable disclosure

Unverifiable messages from a sender with different interests carry limited
information (Crawford and Sobel, Econometrica 1982). With verifiable evidence
the picture flips: under disclosure ("unraveling") results (Grossman 1981;
Milgrom 1981), a sender who can prove a favorable fact does, so silence is
itself informative. Hart, Kremer, and Perry's evidence games
([AER 107(3), 2017](https://econpapers.repec.org/RePEc:aea:aecrev:v:107:y:2017:i:3:p:690-713))
show that, under natural conditions on the evidence structure, a principal
who evaluates evidence after the fact does as well as one who commits to a
reward policy in advance.

**Design consequences.**

- "Check passed" in a completion report is cheap talk; an exit status
  recorded by a tool the agent does not control is evidence. `verify ...
  from <exec result>` is the evidence form; `verify <prose>` is self-report.
- Because ex post evaluation of verifiable evidence suffices, a
  tamper-evident **run ledger checked after the run** is a sound first
  enforcement step, before building hard pre-action hooks. SkillWren 0.7
  ships `skillwren ledger` on this basis. A missing record for a required
  step is then itself informative (unraveling): the check reports it as a
  violation, not as unknown.

### 4. Inspection games and leadership

Inspection games extend hypothesis testing to an inspectee who can
manipulate data; with limited inspection resources, the inspector does best
by announcing and committing to a (possibly randomized) inspection policy
([Avenhaus, von Stengel, Zamir, Handbook of Game Theory vol. 3, 2002](https://ideas.repec.org/h/eee/gamchp/3-51.html)).
The same Stackelberg structure underlies security games and AI-control
protocols: Griffin et al. model trusted monitoring of an untrusted model as
a partially observable stochastic game and find Pareto improvements by
tuning when work is sent to a human auditor
([arXiv 2409.07985](https://arxiv.org/abs/2409.07985)).

**Design consequences.**

- Commit to the monitoring policy before the run: `ledger start` records the
  flow file's hash and its order rules in the ledger's first record, so the
  rules cannot be chosen after seeing the trace.
- Make data manipulation detectable: ledger records are hash-chained, so a
  rewritten or deleted record breaks the chain on `ledger check`.
- Spend expensive inspection (paid `conform` runs, human review) by
  announced, randomized sampling over runs; spend cheap inspection (static
  checks, ledger checks) on every run. Documented in the authoring guide;
  sampling tools are future work.

### 5. Safety games, shields, and alternating-time logic

Reactive synthesis treats the environment as an adversary and asks whether
the system has a strategy that keeps a specification true (Pnueli and
Rosner, POPL 1989). Alternating-time temporal logic states such questions
per coalition: ⟨⟨A⟩⟩φ means the agents in A can force φ whatever the others do
([Alur, Henzinger, Kupferman, JACM 49(5), 2002](https://www.cis.upenn.edu/~alur/Jacm02.pdf)).
Shields are synthesized from a two-player safety game and sit before or after
a learning agent, correcting only actions that would violate the
specification
([Alshiekh et al., AAAI 2018](https://arxiv.org/abs/1708.08611)).

**Readings of existing checks.**

- **P1 (order rules)** is a safety game in which the model controls every
  branch condition: the rule holds only if it holds on every path. That is
  the sound reading when conditions are model judgments.
- **M1 (dismissal safety)** is ⟨⟨user⟩⟩ "no mutation before the user's
  decision": the user has a strategy (dismiss) that guarantees zero change.
- **A2 (authority structure)** checks that decisions labelled as the user's
  are positions where the user actually moves.

**Design consequence.** Make control explicit. `check --audit` labels each
branch by who decides it: the user (it tests an answer to an input `ask`),
evidence (it tests an `exec` or `read` result), or the model (anything else).
Flows where model-decided branches guard mutations are where shields or
hooks pay off. A ledger checked online would be a shield in this sense;
SkillWren 0.7 checks offline only.

### 6. The off-switch game

An agent that is certain of its objective prefers to disable an off switch;
uncertainty about the human's utility, with human choices treated as
evidence, gives it reason to defer
([Hadfield-Menell et al., IJCAI 2017](https://www.ijcai.org/Proceedings/2017/32);
critiqued in [Neth, 2025](https://arxiv.org/abs/2502.08864)).

**Reading.** SkillWren does not rely on the agent's incentives here: M1 makes
deference structural (nothing mutates before a dismissible ask), and
`conform` checks it at run time (asked, then changed files, is a violation).
The game result explains why structure is needed: an instruction to defer
is not an incentive to defer.

### 7. Incomplete contracts

Hadfield-Menell and Hadfield read misalignment as incomplete contracting: no
contract covers every state, and human contracts work because outside
institutions fill the gaps
([AIES 2019, arXiv 1804.04268](https://arxiv.org/abs/1804.04268)).

**Reading.** A skill is an incomplete contract. SkillWren's gap-fillers are
explicit: `always`/`never` invariants, subject precedence ("follow the
project's instructions over this package"), and the authority lists that
assign residual decision rights (`system-decides` versus `user-decides`).
Design rule: when a gap involves a costly-to-reverse action, the residual
right belongs to the user (full-stack D-015 already does this).

### 8. Prover-verifier games and debate

Training provers against a small verifier, with a "sneaky" prover trying to
fool it, keeps solutions legible to weak verifiers and to time-limited
humans; optimizing for correctness alone made them less legible
([Kirchner et al., arXiv 2407.13692](https://arxiv.org/abs/2407.13692)).
Debate uses an adversarial second agent so a weak judge can evaluate strong
claims ([Irving, Christiano, Amodei, arXiv 1805.00899](https://arxiv.org/abs/1805.00899)).

**Readings.**

- A `logic` block is a legibility device: it lets a weak verifier (a
  stdlib checker or a reviewer skimming `--audit`) evaluate the procedure.
- The mutation catalog is a sneaky-prover set for the validator: each
  mutant is a near-valid skill trying to pass. Keep growing it when a rule
  is added (0.7 adds mutants for W15 anchors).
- For agent-written checks, test meaningfulness adversarially: a check that
  still passes on a planted defect is a sneaky pass (FS-016 measure).

### 9. Goodhart effects and reward hacking

Manheim and Garrabrant separate regressional, extremal, causal, and
adversarial Goodhart failures ([arXiv 1803.04585](https://arxiv.org/abs/1803.04585));
Skalse et al. show that a proxy is unhackable only under very strong
conditions ([NeurIPS 2022, arXiv 2209.13085](https://arxiv.org/abs/2209.13085)).

**Readings.** Every SkillWren check is a proxy. Known Goodhart routes and
their guards: an order rule whose pattern matches nothing (W13); a rule
satisfied by a self-report (W15); a ledger step recorded without running
anything (`note` is labelled self-report, and `check --require-evidence`
rejects rules satisfied only that way); final-state `conform` missing
reverted writes (documented limit). No proxy here is claimed unhackable.

### 10. Coordination among workers

Parallel workers editing one repository face a congestion problem over
shared files (Rosenthal's congestion games, 1973). Full-stack's guard uses
declared write sets and refuses overlapping claims, which acts as a public
coordination device: claims are announced before edits.

**Reading.** SkillWren's effects model stays single-actor (SPEC Section 8).
The ledger records one run; cross-run coordination remains a guard's job.
No change.

### 11. Attribution

The Shapley value (1953) is the standard fair attribution of a joint result
to contributors; full-stack FS-017 plans sampled Shapley values over layer
modules. **Reading:** the same method could attribute behavior changes to
individual SkillWren rules or flow blocks in a controlled evaluation. Not
built; noted for the comparison in SPEC Section 17.

### Recent empirical caution

Studies of LLMs in strategic settings report deception and strategic silence
under some conditions (for example [arXiv 2510.12826](https://arxiv.org/abs/2510.12826),
[arXiv 2509.20393](https://arxiv.org/abs/2509.20393)); quality varies and
none studies skill self-reports directly. The design above does not depend
on the agent being deceptive. It depends only on two weaker facts: hidden
steps get skipped, and self-reports are not evidence.

## Decisions

| Topic | Adopted in 0.7 | Documented only | Rejected |
|---|---|---|---|
| Informativeness, verifiable disclosure | Evidence classes; W15; `check --audit` | | |
| Evidence games (ex post suffices) | `skillwren ledger` (offline trace check) | | Building pre-action hooks first |
| Inspection, Stackelberg commitment | Rules and file hash committed at `ledger start`; hash chain | Randomized sampling of costly audits | |
| Safety games, ATL | Branch controller labels in `--audit` | Readings of P1, M1, A2 | Treating evidence branches as cooperative (unsound) |
| Multitask moral hazard | | Process measured separately in evaluations | |
| Off-switch, incomplete contracts | | Readings of M1 and authority lists | |
| Prover-verifier, debate | New mutants | Legibility reading; check meaningfulness | Training anything |
| Goodhart, reward hacking | `--require-evidence` | Proxy catalog | Claims of unhackability |
| Coordination, Shapley | | Notes | |

## Limits

These are design arguments from theory, not measurements. The models assume
rational players with fixed objectives; language-model agents are neither
reliably rational nor stable across prompts. The useful content is
structural: what can be observed, who controls which choice, and when a
commitment or a record changes what can be enforced. Whether the 0.7 tools
change agent behavior still needs the controlled comparison in SPEC
Section 17.
