# ADR-0002: Operational dynamic Task Contract orchestrator

Status: Proposed — human decision required
Date: 2026-09-17
Related: ADR-0001; the five target architecture artifacts; TASK-001 through TASK-005
Authority: framework/framework.yaml (this proposal does not override it)

## Context

The user explicitly requires real dynamic orchestration across Codex, Claude and
CI. Existing artifacts do not define an executable transition engine or trusted
approval channel. The present approval schema stores actor strings; any executor
with repository write access can manufacture such a record.

Independent read-only Claude architecture review confirmed this trust gap and
requested explicit authority and transition boundaries before orchestration.
The review also accepted linked-worktree isolation on the same authorized branch.

## Proposed decision

Implement a deterministic Python control plane under framework/, not an autonomous
agent persona and not a second methodology. It reads the canonical kernel,
project binding and task; selects only necessary roles; routes bounded execution
to Codex and independent review to Claude; records handoffs, evidence and blocks.

The orchestrator has no normative authority. It executes policies under
framework/framework.yaml. Role selection and transition rules belong in that
canonical registry or policies referenced by it; adapters cannot redefine them.

### Permitted automation

- Planning, schema validation, dependency analysis, role selection, fileset checks.
- Worktree setup within the human-authorized repository and branch scope.
- READY -> IN_PROGRESS only after required contract/architecture authorization.
- IN_PROGRESS -> IN_REVIEW after verification, fileset check and complete handoff.
- IN_REVIEW -> CHANGES_REQUESTED on independently produced findings.
- Any applicable running state -> BLOCKED, with reason and unblock condition.
- APPROVED only after authentic current-revision CI and all required reviews and
  human approvals; never from an adapter's self-reported success.
- No automatic merge, release, deploy, secret/permission changes or destructive
  migrations. These remain separate explicit human-authorized actions.

Ordinary transitions do not require repeated human confirmation. Architecture
conflicts, risk exceptions and irreversible actions do.

### Evidence and identity

Records bind task ID, contract digest, implementation commit, actor, timestamp and
evidence origin. Contract or code changes invalidate affected approvals.
Local records are audit bookkeeping; an actor string is not authentication.
CI must be queried from GitHub for the exact repository/revision and required jobs.
Missing, stale, failed or indeterminate checks block progression. Waivers cannot
turn failed mandatory CI into success or substitute for independent/human approval.

### Human decision required: trusted approval channel

Recommended MVP: a trusted human operator controls approval through a separate
explicit action; the runtime records that action and its scope. Codex/Claude
execution cannot grant human gates through their output. Claude review output is
recorded separately; the trusted operator accepts its provenance when necessary.
This is policy-level separation on a developer machine, not tamper-proof isolation.
GitHub CI remains externally verified.

Stronger alternative: protected GitHub PR reviews by an allowlisted human identity
or a separate authenticated approval service. The executor must lack the approver
credential. This requires account/permission provisioning outside current scope.

The repository currently contains organization labels, not authenticated approver
IDs, and the agent has access to the user's GitHub credential. A review under that
same credential cannot be claimed to prove that a human, rather than the agent,
acted. Decide which assurance model is required and designate the approval source.
No CLI --actor human flag, local JSON edit or model opinion resolves this boundary.

## Same-branch worktree procedure

1. Validate and commit authorized planning artifacts on the feature branch.
2. Confirm no uncommitted user changes; record the original checkout and SHA.
3. Detach the original checkout at that SHA; do not commit there.
4. Add a linked worktree checking out feat/intellix-multiagent-framework.
5. Implement and commit only there, sequentially with one active task owner.
6. After completion, require a clean linked checkout, detach it, and switch the
   original checkout back to the feature branch. Never force/delete dirty worktrees.

This creates no additional branch and preserves all commits on the authorized one.

## CI and compatibility

A draft PR may run the existing pull_request workflow without merging.
Portable CI improvements belong to TASK-005 with explicit fileset/review; they do
not require weakening permissions or branch protection. Local tests are not CI.
Preserve issues read compatibility only during migration. New work uses tasks.

## Alternatives rejected

Permanent database/backend/frontend agents; an LLM as deterministic arbiter;
self-approved JSON records; duplicated policy in adapters; unlimited retry loops;
implicit production authorization; mandatory human clicks for every safe step.

## Consequences and rollback

A useful operational MVP is feasible with an explicitly accepted local trust
boundary. Strong isolation needs infrastructure and separate identities.
Keep the kernel dependency-free, record failures, and test negative paths.
Revert scoped feature-branch commits to roll back; retain evidence.
No authority, schema or lifecycle changes are approved by this Proposed ADR.
