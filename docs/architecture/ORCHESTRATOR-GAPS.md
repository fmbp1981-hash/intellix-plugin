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
| P0 | TASK-001 | Absolute/traversal filesets, missing sources and unknown domain roles are accepted; identity is not bound to filename. |
| P0 | TASK-002 | No executable dynamic planner, dependency graph or enforced lifecycle; approvals and waivers are schemas without enforced provenance. |
| P0 | TASK-003 | No operational worktree ownership; intersecting globs can escape collision detection. |
| P0 | TASK-004 | /execute instructs handoff to Codex rather than dispatching bounded work and collecting independent review. |
| P0 | TASK-005 | CI runs on PR/main only, not feature push; no exact-revision task gate, macOS matrix or complete pilot. |

The sequencing is deliberate: establish trusted input, durable state, exclusive
ownership, bounded dispatch, then end-to-end adoption. DRAFT task filesets may
overlap because tasks are sequential; promote only after dependencies complete.

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
