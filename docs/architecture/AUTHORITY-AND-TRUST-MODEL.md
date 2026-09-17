# Authority and Trust Model

Status: Proposed for human approval

Date: 2026-09-17

## Fact ownership

| Fact | Canonical owner | Generated/derived consumers |
|---|---|---|
| Contracts, roles, gates, lifecycle | `framework/framework.yaml` and referenced schemas/policies | validators, adapters, templates |
| Claude phases, skills and hooks | `global-config/metodologia.yaml` adapter | installed `~/.claude` runtime |
| Project profile, paths, commands, defaults | project `intellix.yaml` | dispatcher and CI |
| Architectural decisions | accepted project ADRs | Task Contracts and reviews |
| Unit of implementation | `tasks/TASK-NNN.yaml` | runtime/evidence/PR |
| Deterministic result | CI on exact commit SHA | dispatcher and protected branch |
| Human approval | authenticated external action | local audit reference |
| Merge/release/deploy state | GitHub and deployment provider | reports and handoff |

No weaker layer may redefine a stronger layer. `AGENTS.md` and `CLAUDE.md` are
short entry-point adapters only.

## Source and installation direction

```text
repository framework source
  → validated release/snapshot
  → project pin and digest
  → generated AGENTS/CLAUDE adapter files
  → installed runtime (~/.claude for Claude Code)
```

The reverse direction is never automatic. Changes made in a live installation
must be proposed back to the repository and reviewed; they do not silently become
normative. A sync/doctor check must detect drift.

## Approval assurance levels

| Level | Evidence | Permitted use |
|---|---|---|
| Local advisory | explicit operator action recorded locally | development progression only; not proof of identity |
| GitHub authenticated | protected PR review/check from allowlisted identity | merge authorization |
| Production authenticated | provider/IAM approval separated from executor credential | deploy, secrets, permissions, destructive operations |

MVP policy: agents may prepare PRs and evidence but cannot satisfy human gates.
Until the agent and human use separated credentials, merge and production remain
manual and the framework must not claim cryptographic human provenance.

## Credential boundary

Provision a separate bot/GitHub App identity for automation before enforcing
authenticated review. It may write the authorized branch and report checks but
must not approve PRs, change branch protection or access production secrets. The
human uses a separate identity. Credential provisioning is external to this branch
and requires explicit authorization.

## Waivers

Waivers require owner, reason, expiry and compensating controls. They may relax a
documented optional policy but cannot override failed mandatory CI, reviewer
independence, branch protection or human authorization for irreversible actions.

## Decisions

1. Keep the kernel in this repository for the MVP; make it extraction-ready.
2. Treat `global-config/metodologia.yaml` as the versioned Claude adapter source;
   `~/.claude` is the installed copy.
3. Distribute a pinned kernel snapshot/package to client projects and validate by
   explicit project root.
4. Use six task states; derive merge/release state externally.
5. Preserve Claude-only `/execute` through explicit adapter resolution/fallback.
6. Support `micro`, `standard` and `regulated` project profiles.
7. Require an end-to-end pilot before merge.
