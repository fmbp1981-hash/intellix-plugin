# IntelliX Workflow

Status: Proposed for human approval

Date: 2026-09-17

## Product-to-production flow

```text
Human idea
  → PRD .............................................. human approval
  → Architecture + ADRs ............................. human approval
  → SPEC
  → /break → draft Task Contracts
  → /plan → complete Task Contract
  → validate --root <project> → READY
  → /execute → thin dispatcher
       ├── validate dependencies, fileset and risk gates
       ├── resolve roles and executor
       ├── reserve branch/worktree when required
       └── dispatch bounded context
  → implementation by assigned adapter
  → draft PR + evidence
  → CI for exact revision
  → independent semantic review
       └── findings return to the executor, maximum three cycles
  → authenticated Human Gate when required
  → merge
  → deploy with explicit authorization
  → post-deploy verification and project handoff
```

## Four-command semantics

| Command | Output | Boundary |
|---|---|---|
| `/spec` | Testable product behavior | No implementation allocation |
| `/break` | Atomic draft Task Contracts | Decompose by outcome, not agent/file |
| `/plan` | READY contract | No production code |
| `/execute` | Validated dispatch and evidence | No implicit merge/deploy |

`/execute` is a thin dispatcher. It is not a model persona or full orchestration
product.

## Executor resolution

Resolution order:

1. explicit Task Contract assignment;
2. project default in `intellix.yaml`, when installed and permitted;
3. current adapter for legacy Claude-only projects, when policy permits;
4. otherwise block and request an explicit assignment.

Fallback is recorded. It never silently changes reviewer independence. If Claude
implements, Claude cannot be the approving reviewer for that task.

## Minimal task lifecycle

```text
DRAFT → READY → IN_PROGRESS → IN_REVIEW → DONE
                    ↘ BLOCKED ↗
IN_REVIEW → IN_PROGRESS when findings require changes
```

`APPROVED`, `MERGED`, `VERIFIED` and `RELEASED` are derived from GitHub/deployment
systems, not duplicated as authoritative Task Contract states.

## Worktree policy

- medium, high and critical risk: dedicated branch/worktree required;
- low risk: dedicated short-lived branch required; worktree optional;
- micro profile trivial documentation-only change: project policy may waive a
  worktree, but never the fileset or CI rules that apply;
- one active owner per writable fileset;
- reviewer returns findings and does not edit the executor worktree.

## Stop conditions

Block the flow when a source is missing, a dependency is unresolved, filesets
overlap, CI is stale/failing, reviewer independence is absent, or an irreversible
action lacks authenticated human authorization.
