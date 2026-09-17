# Framework execution specification

## Required behaviors

1. A fresh checkout validates with Python's standard library only.
2. Framework, role, project and task artifacts reject unknown fields.
3. A task cannot assign the same executor and reviewer.
4. A task cannot write a forbidden path.
5. Risk level determines a minimum gate set; high and critical risk require a
   rollback plan.
6. Two active tasks cannot own overlapping writable filesets.
7. Plugin and marketplace versions cannot drift from the framework.
8. Adapters cannot override the normative framework.
9. CI runs validation and validator unit tests on every pull request.

## Acceptance criteria

- Given the repository as committed, when `python3 framework/validate.py --all`
  runs, then it exits zero.
- Given an invalid Task Contract, when task validation runs, then every detected
  violation is reported and the process exits non-zero.
- Given active tasks with overlapping paths, when directory validation runs,
  then the collision names both tasks and blocks the gate.
