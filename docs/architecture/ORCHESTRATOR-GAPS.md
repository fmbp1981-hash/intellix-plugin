# Operational orchestrator gap register

Date: 2026-09-17
Baseline: dfba13ed8f57b765144c6c9bc89e5e29eee198f9
Reference: Arquitetura IntelliX AI para Engenharia de Software Multiagente v1.0.
Reference SHA-256: b32679f12e8b5dc77af6069be4329caa5cb2423668d5afed36f6fea64ac9d9e6
Normative authority: framework/framework.yaml.

## Finding

Dynamic multiagent orchestration is a required deliverable. Only fixed permanent
agent hierarchies are rejected. The contracts, roles, policies and adapters provide
a foundation, not an operational orchestrator.

Baseline passed: validate.py --all; seven unittest tests; validate-hooks.sh
(one command reference). These results do not prove omitted controls.

## Prioritized work

| Priority | Task | Gap |
| --- | --- | --- |
| P0 | TASK-001 | Authority is duplicated; validation resolves paths against the plugin instead of an explicit project root. |
| P0 | TASK-002 | The kernel is not pinned/distributed to client projects and adapters are manually duplicated. |
| P0 | TASK-003 | No thin dispatcher, minimal lifecycle, role resolution or Claude-only compatibility path. |
| P0 | TASK-004 | No operational worktree ownership, bounded adapter handoff or independent-review enforcement. |
| P0 | TASK-005 | CI is not bound end-to-end to the reviewed revision; no portable pilot proves the method. |

The sequencing is deliberate: establish one authority and trusted project root,
distribute a pinned kernel, add a thin dispatcher, isolate execution/review, then
prove the method end to end. DRAFT filesets may overlap because tasks are
sequential; promote only after dependencies complete.

## Drift requiring reconciliation

- Framework lifecycle lists VERIFIED before RELEASED; the reference requires
  post-release verification. Correct via the accepted ADR, never silently.
- Deployment policy requires staged releases at high risk, while the task gate
  list adds it only at critical risk. Distinguish execution from release gates.
- Roles use hyphen gate names; risk gates use underscores. Establish canonical IDs.
- --all does not validate approval/waiver/handoff records or all normative shapes.
- Version bindings, source links, dependencies and cycles are incompletely checked.
- Legacy four-commands/master-workflow still describe issues; opus-plan claims
  MASTER-ARCHITECTURE as sole authority. Compatibility cannot override the kernel.
- Existing hook check is portable but checks only one command reference here.
- Local actor strings do not establish independent or human identity.

## Architecture review

An actual read-only Claude CLI session reviewed the normative files and proposal.
It identified the absence of an operational-authority ADR, CI trigger mismatch
and untrusted local approval records. It accepted same-branch linked worktrees
with a documented detached-checkout procedure. See ADR-0002 (Proposed).

Reviewer suggestions are findings, not new policy: requiring a human at every
ordinary transition would undermine the requested dynamic orchestration. ADR-0002
instead proposes automatic administrative transitions and verified protected gates.

## Delivery authorization

The user authorizes edits, tests, commits and push only on
feat/intellix-multiagent-framework. No merge, deploy, release, secrets, permission
changes, destructive migration or production action is authorized.

No implementation task is complete. The architecture approval trust boundary
must be decided before an orchestrator can enforce approvals honestly.
