# IntelliX agent contract

This file is a vendor-neutral adapter. The normative source is
`framework/framework.yaml`; policy, role, project and task contracts referenced
by it override prose in this file.

## Required operating sequence

1. Read `intellix.yaml`, the assigned `tasks/TASK-*.yaml`, and every source
   artifact referenced by the task.
2. Validate before editing: `python3 framework/validate.py --task <task>`.
3. Confirm branch/worktree and exact create/modify/forbidden filesets.
4. Implement only the approved contract. Record newly discovered architecture
   work as an ADR proposal or block the task; do not silently expand scope.
5. Run every verification command in the task plus repository CI checks.
6. Produce a handoff with changed files, evidence, remaining risk and next action.

## Separation of duties

- Claude is the default architect and independent reviewer.
- Codex is the default implementation and refactoring executor.
- Domain roles constrain permissions; they are not permanent autonomous agents.
- The executor must not approve its own work.
- CI is the deterministic arbiter. A model opinion never overrides a failed gate.
- Production deploy, destructive data changes, secret changes and privilege
  changes require explicit human approval.

## Scope and safety

Never edit outside the task fileset, expose secrets, weaken tests to obtain a
pass, or execute an irreversible action without its gate. If contract and code
disagree, stop and request an architecture/spec correction.
