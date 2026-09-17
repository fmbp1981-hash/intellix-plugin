# IntelliX Multi-Agent Engineering Framework

Status: adopted architecture

Normative source: `framework/framework.yaml`

Project binding: `intellix.yaml`

## 1. Decision

IntelliX adopts an artifact-driven, vendor-neutral engineering kernel with
Claude Code and Codex as interchangeable adapters with different defaults:

- Claude: architecture, decomposition review, threat/design analysis and
  independent review;
- Codex: primary implementation, testing, refactoring and repository execution;
- CI: deterministic arbiter of schemas, build, tests, security and policy;
- human owner: product decisions and approval of irreversible or production
  actions.

The framework does not create a permanent hierarchy of autonomous agents.
The “Tech Lead plus database/backend/frontend agents” diagram is retained only
as a responsibility map. The useful part is specialist ownership and review.
The harmful part—always-on specialists, per-file orchestration and a model as
final authority—is rejected because it increases handoff cost, context loss,
fileset collisions and circular approval.

## 2. Authority model

From strongest to weakest:

1. `framework/framework.yaml` and its policies/schemas;
2. the repository's `intellix.yaml`;
3. accepted ADRs;
4. the assigned `tasks/TASK-NNN.yaml`;
5. vendor adapters (`AGENTS.md`, then `CLAUDE.md`);
6. conversational instructions and generated suggestions.

This hierarchy prevents duplicate normative prose. Markdown explains; machine-
readable contracts decide. A conflict is fixed at the weaker layer.

## 3. Artifact pipeline

```text
Product owner
    │
    ▼
PRD ── product problem, users, outcomes, constraints
    │ product approval
    ▼
Architecture + ADRs ── boundaries, quality attributes, contracts, trade-offs
    │ architecture approval
    ▼
SPEC ── testable behavior, edge/error cases, no agent assignment
    │ spec approval
    ▼
Task Contracts ── fileset, owner, risk, gates, acceptance and verification
    │ contract validation
    ▼
Worktree + implementation ── default owner: Codex, domain role as needed
    │ handoff with evidence
    ▼
Independent review ── default owner: Claude plus specialist gates by risk
    │
    ▼
CI ── deterministic verdict ── human production approval ── release
```

PRD does not mention Claude or Codex. Architecture does not allocate files to
agents. Agent routing belongs only in Task Contracts and adapter configuration.

## 4. Task Contract

The Task Contract is the unit of execution and concurrency. It includes:

- immutable links to PRD, Architecture, SPEC and relevant ADRs;
- a single outcome and Given/When/Then acceptance criteria;
- risk level and irreversible actions;
- architect, executor, independent reviewer and optional domain role;
- exact create/modify/forbidden filesets;
- verification commands and mandatory gates;
- rollback plan for high/critical risk;
- evidence required for handoff.

A task is `READY` only after schema validation, architecture review and explicit
fileset ownership. Two active tasks with overlapping writable filesets are
rejected by `framework/validate.py`.

## 5. Execution protocol

1. Select one `READY` Task Contract.
2. Create a short-lived branch. For medium or higher risk, use an isolated Git
   worktree. One task owns one branch/worktree.
3. Run task validation and baseline tests before editing.
4. Implement within the fileset, using the selected domain role only when the
   task needs that expertise.
5. Add or change tests for every changed behavior. Do not weaken assertions.
6. Run every task verification command; capture evidence.
7. Produce a handoff and move the task to `IN_REVIEW`.
8. An independent reviewer checks contract traceability, architecture, security,
   maintainability and evidence. At most three review cycles are allowed before
   escalation to a human/architectural decision.
9. CI reruns deterministic gates. Only a green result plus required approvals
   permits merge.

## 6. Risk and gates

Low risk needs schema, lint, tests and independent review. Medium adds worktree
and fileset enforcement. High adds security review, rollback and human approval.
Critical adds staged release. Authentication, payments, personal data, public
APIs, uploads, admin access and infrastructure require a threat model.

Waivers are explicit artifacts with an owner, expiry and compensating controls.
They never silently change policy and cannot waive an unmitigated critical issue.

## 7. Quality system

Acceptance criteria trace to tests and evidence. CI should execute, in order:

1. framework/project/task schema validation and fileset collision detection;
2. formatting, lint and type checks;
3. unit, integration and contract tests appropriate to risk;
4. build and migration checks;
5. secret, dependency and static security scans;
6. E2E/accessibility/performance checks when applicable;
7. policy and approval verification.

An LLM review can find semantic issues; it cannot convert a failing CI result
into a pass.

## 8. Observability and release

Features define actionable logs, metrics, traces, alert ownership and runbook
updates before release. Logs must not contain secrets or personal data. High-
risk releases are staged and define health signals, rollback triggers and a
maximum decision window. Deployment records connect commit, CI evidence,
approver and environment. Post-deploy verification includes health, smoke,
metrics and error-budget checks.

## 9. Governance and evolution

Framework changes use semantic versions and an ADR when they change authority,
roles, gates or lifecycle. Schema-breaking changes require a migration guide.
Plugin and marketplace versions must match the canonical `plugin_version`.
Quarterly governance reviews inspect lead time, change failure rate, escaped
defects, waiver age, review cycles and security findings—not agent activity.

## 10. Anti-patterns

- duplicating normative rules in prompts, skills and markdown;
- creating one permanent agent per technical layer for every task;
- assigning the same model instance as executor and approver;
- splitting a cohesive change merely to keep specialists busy;
- parallel work without non-overlapping filesets;
- using chat history as acceptance criteria or audit evidence;
- letting “senior agent” opinion bypass tests or approvals;
- broad `**/*` ownership, silent scope expansion or unbounded retries;
- direct commits to protected branches or production deploy from an agent;
- treating generated code volume as delivery quality.

## 11. Adoption boundary

Existing IntelliX phases, skills, DevSecOps hooks and the four-command workflow
remain useful. They become adapters and automation around the new contracts.
`global-config/metodologia.yaml` remains a compatibility mirror during migration;
it is no longer the top-level normative source. Existing `issues/*.md` can be
converted incrementally; all new work should use `tasks/TASK-*.yaml`.
