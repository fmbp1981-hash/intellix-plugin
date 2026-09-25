# IntelliX operational pilot acceptance

## Scope

The pilot proves a clean consumer bootstrap for `micro`, `standard` and
`regulated` governance profiles. It covers explicit-root validation, profile and
risk gate union, bounded Codex dispatch, durable checkpoint, independent read-only
handoff and externally queried exact-revision CI evidence.

It does not perform or authorize merge, release, deploy, permission changes,
secret provisioning or production activity.

## Deterministic protocol

1. Copy the clean consumer fixture into a temporary project root.
2. Set its governance profile without changing its business profile.
3. Install the repository snapshot and generated lock in the supported one-way
   direction.
4. Validate from an unrelated shell directory using explicit `--root`.
5. Dispatch only the required executor/domain role and record the transition.
6. Create a complete resumable checkpoint and independent read-only handoff.
7. Query the configured GitHub repository for the exact 40-character revision.
8. Accept CI only when every configured check is completed successfully for that
   revision; otherwise block or report indeterminate.
9. Keep merge blocked unless an authenticated external human approval uses a
   credential unavailable to the executor.

## Profile expectations

| Governance profile | Kernel minimum | Additional rule |
|---|---|---|
| `micro` | schema, tests | Risk gates still apply; fileset remains explicit. |
| `standard` | schema, lint, tests, independent review | Exact-revision project CI is required for merge readiness. |
| `regulated` | schema, fileset, lint, tests, security review, independent review, rollback, human approval, worktree | Evidence retention and separately credentialed approval remain external requirements. |

## Automated evidence

`framework/tests/test_pilot.py` executes all three profiles in clean temporary
roots. `framework/tests/test_ci.py` proves successful exact-SHA evaluation and the
negative paths for missing, stale, incomplete, failed, cancelled, unauthorized,
rate-limited, malformed and unavailable evidence.

The GitHub workflow runs the complete suite on `ubuntu-latest` and
`macos-latest`, verifies the checked-out SHA and exposes the stable aggregate
check `framework-validation`. Push runs bind that check to the pushed commit SHA;
pull-request merge-ref results cannot substitute for an absent head-SHA check.

## Acceptance state

Local run on 2026-09-18: repository validation and snapshot check passed; all 75
unit/pilot tests passed; Python compilation, hook validation and whitespace check
passed. The run exercised the three governance profiles from an unrelated working
directory and confirmed that absent external credentials fail closed.

Local deterministic evidence may establish implementation readiness. Final merge
readiness additionally requires GitHub links for the final commit, independent
Claude review and an authenticated human decision. Until those exist, the correct
status is **blocked for merge**, not implicitly approved.
