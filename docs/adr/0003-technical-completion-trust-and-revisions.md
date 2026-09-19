# ADR-0003: Local technical completion and revision binding

Status: Proposed — human acceptance not yet recorded
Date: 2026-09-19
Related: ADR-0002 (Accepted); TASK-007, TASK-008 and TASK-009
Authority: `framework/framework.yaml` and its referenced policies remain normative

## Context

ADR-0002 accepts a local, explicit human decision for technical Task Contract
completion, but not as authenticated merge or production approval. The current
kernel does not permit `IN_REVIEW -> APPROVED`. Adding that edge alone would be
unsafe: the generic dispatcher accepts a caller-chosen target state, the runtime
checks only the transition registry, CI can be queried for a caller-chosen older
SHA, and a writable handoff JSON cannot prove reviewer identity. `APPROVED`,
`MERGED`, `VERIFIED` and `RELEASED` currently satisfy dependencies in the
dispatcher, so an incorrect result propagates. The dependency-satisfying set
belongs in the kernel rather than remaining an independent dispatcher rule.

A status change is itself a repository edit. The implementation/review commit
and the later commit recording task completion cannot be the same SHA. This ADR
proposes how to bind both revisions without pretending that local records prove
identity. It does not add a kernel transition or authorize TASK-008 execution.

## Proposed decision

### Assurance boundary

For technical completion only, a separate Claude review performed in a
read-only session and an explicit human decision in the controlling session are
process-level evidence. Record their origin, task, contract digest, reviewed
SHA, time and references. An executor-written `actor`, editable JSON or model
output alone never satisfies the human gate. Local evidence is auditable but
forgeable by someone with repository/runtime write access; it must not be called
authenticated identity. GitHub CI is queried independently for the exact
repository and revision. Merge and production remain blocked until their
separately credentialed external gates are met.

### Reviewed revision R

Derive R from the clean, authorized task worktree rather than accepting an
arbitrary caller-supplied SHA. Require its branch to be the authorized branch
and R to equal the remote branch tip when the completion decision is made.
Require the independent review to cover the final task fileset at R and bind
its handoff to the same task ID and contract digest. Pin the project binding
and normative kernel/policy digests observed at R. Require a valid, non-empty
set of required checks and query those configured GitHub checks live for R;
missing, stale, failed or indeterminate evidence blocks. A caller cannot reduce
the check set or change repositories to make eligibility vacuously green. Local
CI JSON is only an audit copy and cannot replace that query.

The local Claude review reference is not cryptographic proof of origin. The
control plane can verify structural consistency and that executor and reviewer
assignments differ, but must disclose that a writer can forge local evidence.
The explicit human decision must occur after the final review and CI result;
the executor cannot infer it from a prior planning approval.

### Guarded completion and status revision A

Only a dedicated completion path may request any state that satisfies a
downstream dependency. The generic dispatcher and generic runtime transition
API must reject direct executor-requested `APPROVED`, `MERGED`, `VERIFIED` or
`RELEASED` (and any later kernel-listed satisfying state), even after the kernel
adds an edge. The guarded technical path may grant only `APPROVED`; external
merge/release states require their own authority. The guarded path checks the
canonical risk/profile gates, task fileset and dependencies, live CI for R,
independent review and the explicit local human decision before writing a
technical-only completion event. There is no `--actor human` bypass.

The completion edit creates a later status commit A. Its diff must be confined
to permitted completion metadata; executable code or other fileset changes
require a new review and CI cycle. Because A cannot be known before it is
committed, its SHA is derived from Git history after commit, not self-declared
inside its own content. CI must pass for A before `APPROVED` can release a
dependent task. A successful CI result for R alone is insufficient for that
downstream gate. The approval record binds R and the pre/post contract digests;
the dependency checker derives A and verifies its CI and ancestry. The existing
`approval.schema.json` cannot represent these fields; TASK-008 must explicitly
extend that schema and its validation before any guarded transition is enabled.

An `APPROVED` status in an editable Task Contract is therefore historical local
technical bookkeeping, not by itself proof that the dependency is currently
satisfied. The dispatcher must check the completion evidence and A's exact CI
before treating it as such. This also prevents a hand-edited status label from
opening downstream work.

### Invalidation without silent revocation

Current eligibility depends on the task contract and its declared source files,
the writable fileset reviewed at R, the independent review and human-decision
references, the approval record, the project binding (including repository and
required checks), the normative kernel/policies, Git ancestry and exact CI for
R and A. Missing or unevaluable input is blocking. If any of these inputs
changes or no longer matches, the prior approval remains in the audit trail
but downstream eligibility is blocked with an explicit reason. Unrelated later
commits do not invalidate R or A merely because the branch tip advanced; the
checker compares the enumerated inputs rather than requiring A to remain the
global tip forever.

If CI on A fails, the task remains historically marked `APPROVED` but cannot
release dependencies. Recovery requires a separate, approved corrective Task
Contract using a guarded supersession path to produce a status/evidence commit
A' and repeat the applicable review, human-decision and exact-revision CI gates.
Until A' passes, the dependent task remains blocked. No executor may silently
edit approval evidence or use a generic `APPROVED -> IN_PROGRESS` transition to
escape this state; an explicit kernel lifecycle rule would be needed for
reopening.

The implementation Task Contract must choose an evidence representation that
can be validated in a fresh checkout. Ignored local runtime files alone are
insufficient for cross-session dependency checks. Versioned references remain
auditable, not authenticated, and must be checked against live CI and Git
history. The exact schema and storage path belong in the revised TASK-008
fileset and security review, not in an adapter or a second policy source.

## Alternatives considered

- **Add the transition edge alone:** rejected; it exposes a direct
  self-approval path through the current dispatcher.
- **Trust a caller-provided SHA or saved CI JSON:** rejected; older green checks
  can be replayed and local files are editable.
- **Treat local Claude output as authenticated review:** rejected; it provides
  process separation but no independent credential attestation.
- **Require external authenticated identity for every technical completion:**
  deferred; it exceeds the accepted ADR-0002 MVP boundary and needs separately
  provisioned credentials. It remains mandatory for merge and production.
- **Use the task's `APPROVED` label alone for dependencies:** rejected; it can
  be edited without valid current evidence or status-commit CI.

## Consequences and implementation gate

If accepted, TASK-008 must be re-planned before READY with an expanded, exact
fileset for the guarded path, approval schema and validation, fresh-checkout
evidence checks, revision derivation and negative tests. Its tests must reject
direct dependency-satisfying transitions, stale R, unclean or wrong worktrees,
self-declared reviewer/human strings, empty or changed CI configuration, CI
indeterminacy, changed contracts or normative inputs, invalid status-commit CI
and downstream dependency release without current evidence. The proposal does
not solve cryptographic local identity; reports must state that residual risk
plainly.

No part of this Proposed ADR overrides the current kernel, changes an approval
schema, grants production authority, authorizes merge or marks ADR-0001 or the
target architecture set as Accepted. Human acceptance of this precise decision
is required before TASK-008 can use it as an architectural source.
