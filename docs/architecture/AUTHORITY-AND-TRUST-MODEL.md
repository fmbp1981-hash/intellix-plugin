# Authority and Trust Model

Status: Proposed for human approval

Date: 2026-09-17

ADR-0002 is the accepted operational decision for the MVP trust boundary. This
document remains Proposed; its target-state recommendations do not supersede the
current `framework/framework.yaml` transitions or authorize new approvals.

## Fact ownership

| Fact | Canonical owner | Generated/derived consumers |
|---|---|---|
| Contracts, roles, gates, lifecycle | `framework/framework.yaml` and referenced schemas/policies | validators, adapters, templates |
| Claude phases, skills and hooks | `global-config/metodologia.yaml` adapter | installed `~/.claude` runtime |
| Project profile, paths, commands, defaults | project `intellix.yaml` | dispatcher and CI |
| Architectural decisions | accepted project ADRs | Task Contracts and reviews |
| Unit of implementation | `tasks/TASK-NNN.yaml` | runtime/evidence/PR |
| Deterministic result | CI on exact commit SHA | dispatcher and protected branch |
| Technical Task Contract approval | explicit human action in the controlling session, only where the kernel transition and applicable gate permit local technical completion | local advisory/audit record |
| Merge/production approval | authenticated external action with credentials separate from the executor | local audit reference |
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
| Local advisory | explicit human action in the controlling session, recorded locally | technical Task Contract completion after required exact-revision CI and independent review, only when the kernel permits the transition; not proof of identity or merge/production authority |
| GitHub authenticated | protected PR review/check from allowlisted identity | merge authorization |
| Production authenticated | provider/IAM approval separated from executor credential | deploy, secrets, permissions, destructive operations |

MVP boundary accepted in ADR-0002: Codex or Claude output cannot grant a human
gate. An explicit local human action may close a technical Task Contract only
after required exact-revision CI and independent review, and only through a
transition allowed by the canonical kernel. This local record does not satisfy
authenticated merge or production gates. Until separate approver credentials are
provisioned, merge and production remain blocked; the framework must not claim
cryptographic human provenance from a session message or editable record.

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

## Proposed target-state decisions

The following items are proposals in this document, not accepted changes to the
operational kernel. In particular, the current lifecycle and transition registry
in `framework/framework.yaml` remains authoritative; item 4 does not reduce it
to six states.

1. Keep the kernel in this repository for the MVP; make it extraction-ready.
2. Treat `global-config/metodologia.yaml` as the versioned Claude adapter source;
   `~/.claude` is the installed copy.
3. Distribute a pinned kernel snapshot/package to client projects and validate by
   explicit project root.
4. Use six task states; derive merge/release state externally.
5. Preserve Claude-only `/execute` through explicit adapter resolution/fallback.
6. Support `micro`, `standard` and `regulated` project profiles.
7. Require an end-to-end pilot before merge.
