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
10. Projects preserve their business `project.profile` and separately declare a
    required governance profile: `micro`, `standard` or `regulated`.
11. Task validation applies the union of risk gates and kernel-defined governance
    profile gates; neither dimension can weaken the other.
12. Required CI check names come from the project binding. Eligibility queries
    GitHub read-only for the exact configured repository and full reviewed SHA.
13. Missing, stale, incomplete, failed, malformed or unavailable CI is blocking.
    Local JSON and model output are not authoritative CI sources.
14. Linux and macOS run the same validation suite. A stable aggregate check passes
    only when every matrix job succeeds.
15. Authenticated human approval remains an external gate using credentials not
    available to the executor. Without it, merge eligibility remains blocked.

## Acceptance criteria

- Given the repository as committed, when `python3 framework/validate.py --all`
  runs, then it exits zero.
- Given an invalid Task Contract, when task validation runs, then every detected
  violation is reported and the process exits non-zero.
- Given active tasks with overlapping paths, when directory validation runs,
  then the collision names both tasks and blocks the gate.
- Given a task whose gates satisfy risk but not its governance profile, when task
  validation runs, then the missing profile gates are reported.
- Given GitHub checks for another SHA or a required check that is not successfully
  completed, when CI eligibility runs, then the result is blocked.
- Given GitHub cannot return authoritative evidence, when eligibility runs, then
  the result is indeterminate and blocking rather than skipped.
- Given exact-revision CI is green but no separately credentialed human approval
  exists, when merge readiness is evaluated, then merge remains blocked.
