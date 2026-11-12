# Runtime assurance implementation and research

## Scope and ownership

Implement the review's missing operational slice while keeping the stdlib
Python package and conservative static analyzer. A trusted host owns policy,
verifier programs, protected outputs and audit checkpoints. The untrusted
agent supplies operation IDs and candidate content only. It cannot select a
verifier command or a destination path. The controller has no general shell
endpoint. Evidence lives in controller memory and expires on restart.

## Research basis (retrieved 2026-11-12)

- Saltzer and Schroeder, *The Protection of Information in Computer Systems*
  (1975), https://www.cs.virginia.edu/~evans/cs551/saltzer/ : complete mediation,
  least privilege and fail-safe defaults motivate routing every protected
  write through a small controller. A voluntary wrapper cannot establish this.
- NASA, *A Formal Verification Framework for Runtime Assurance* (2023),
  https://ntrs.nasa.gov/citations/20230017350 : separating an untrusted
  controller from a trusted deciding component motivates the architecture.
  This software is not a formal proof or a certified Simplex implementation.
- RFC 9162, https://www.rfc-editor.org/rfc/rfc9162.html : independently retained
  tree heads and consistency proofs motivate checkpoints outside the writer's
  authority. Our linear hash checkpoints are not a CT log or a signature.
- Docker run reference, https://docs.docker.com/reference/cli/docker/container/run/,
  and seccomp guide, https://docs.docker.com/engine/security/seccomp/ : read-only
  mounts, network isolation, dropped capabilities and syscall restrictions
  are complementary controls. None independently proves sandbox security.
- GitHub Python CI guide,
  https://docs.github.com/en/actions/tutorials/build-and-test-code/python :
  platform/version matrices and installed-package tests support release checks.

## Selected design

A JSON-lines controller accepts verify/write/status requests. Policy binds
stable operation IDs to a fixed target and verifier argv, with SHA256 pins
for executable and script files. Candidate bytes are the verifier's stdin;
its JSON response must contain literal `ok: true` and that input's digest.
Write requests must match verified bytes and unchanged protected-file state.
Verification is single-use. Rejected/malformed requests fail closed.

This deliberately restricts the first slice to verifying candidate content.
It does not infer that an arbitrary shell command performed a security review.
The administrator is responsible for the verifier's semantic adequacy.
Structured verifier predicates can express refinements without teaching the
static analyzer to infer arbitrary natural-language implications.

Protected directories must be owned exclusively by the controller account.
A same-account process with direct filesystem access remains outside this
threat model. Container tests will give the attacker no protected mount,
policy mount, credentials or Docker socket; the host controller receives only
JSON requests. Docker is currently installed but its daemon is unavailable.

## Failure and restart

Evidence is discarded before each verification attempt and consumed before
writes. Restart requires re-verification. Writes use temporary files plus
atomic replace in the protected directory. Audit failure prevents subsequent
operations; a crash between authorization and completion leaves a visible
pending intent, not a fabricated completed event. The host owns recovery.

## Assurance and acceptance

| Claim | Control owner | Check |
| --- | --- | --- |
| Wrong verifier cannot be selected | policy/controller | unknown fields and altered pins rejected |
| Unverified write denied | controller | real output absent before verifier passes |
| Stale/replayed evidence denied | controller | changed bytes, changed target and second use rejected |
| Restart fails closed | controller | new instance cannot reuse approval |
| Log rollback detectable | independent checkpoint holder | truncate/reseal log then check old checkpoint |
| Host isolation | deployment | attacker cannot access protected path or network; conditional on Docker |
| No empirical overclaim | benchmark runner | synthetic and model results labeled separately |
| Release portability | CI | supported Python/OS matrix, wheel install, mutation sweep |

No new datastore, hosting provider or language. Paid model runs and remote
branch protection are not silently enabled. Local tests establish mechanism
behavior, not causal improvement in model reliability.

## Evaluation research

AgentDojo (Debenedetti et al., NeurIPS 2024),
https://arxiv.org/abs/2406.13352, motivates evaluating both task utility and
adversarial policy failures, not only success on benign tasks. Anthropic's
*Demystifying evals for AI agents* (2026-01-09),
https://www.anthropic.com/research/demystifying-evals-for-ai-agents,
distinguishes tasks, repeated trials, graders, traces and real environment
outcomes. Our harness retains requests/responses and checks actual target
bytes; deterministic adversarial scripts are labeled mechanism tests and
cannot establish a prose-versus-structure model effect.

Python 3.15 is included in CI following the official release record:
https://www.python.org/downloads/release/python-3150/ . Python 3.9 remains a
compatibility lane because the package still declares it as the minimum.
