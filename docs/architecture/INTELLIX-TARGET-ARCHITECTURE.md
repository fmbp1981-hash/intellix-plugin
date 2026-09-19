# IntelliX Target Architecture

Status: Proposed for human approval

Date: 2026-09-17

## Objective

Define a vendor-neutral engineering kernel that coordinates humans, Claude Code,
Codex and CI without making any tool the methodology or an LLM the deterministic
authority.

## System boundaries

```text
IntelliX Engineering Framework
├── Kernel (normative)
│   ├── contracts and schemas
│   ├── role registry
│   ├── policies and gates
│   └── lifecycle rules
├── Control plane (deterministic)
│   ├── project-root validation
│   ├── thin dispatcher
│   ├── fileset/dependency checks
│   └── worktree ownership
├── Adapters (non-normative)
│   ├── Claude Code
│   ├── Codex
│   ├── GitHub/CI
│   └── human operator
└── Project binding
    ├── intellix.yaml
    ├── pinned kernel version
    ├── PRD / Architecture / SPEC / ADRs
    └── Task Contracts
```

## Authority

The canonical kernel remains in this repository for the MVP. It must not contain
plugin-specific versioning or preferred vendors. The Claude plugin is one adapter
and the current distribution vehicle, not the owner of framework semantics.

Project repositories consume a version-pinned snapshot or package generated from
the kernel. Generated copies are never manually edited and must carry a digest.
`~/.claude` is an installed runtime target, not a source of truth.

The precedence model is defined in `AUTHORITY-AND-TRUST-MODEL.md`.

## Responsibilities

| Component | Responsible for | Must not do |
|---|---|---|
| Kernel | Contracts, roles, gates, lifecycle, policy | Choose a vendor implicitly |
| Project binding | Profile, paths, defaults, commands, pinned version | Redefine kernel rules |
| Dispatcher | Validate and route bounded work | Make architecture or product decisions |
| Claude adapter | Architecture, investigation, implementation when assigned, review | Approve its own implementation |
| Codex adapter | Implementation, tests, refactoring, review when assigned | Expand scope silently |
| CI adapter | Exact-revision deterministic evidence | Perform semantic judgment |
| Human | Product approval, exceptions, merge, production authority | Delegate identity through a text field |

## Dynamic specialization

Roles are data describing permissions, inputs, outputs and gates. They are selected
only when the Task Contract requires them. The database/backend/frontend diagram is
a capability map, not a permanent hierarchy.

Role definitions must not name a preferred adapter. Assignment is resolved from
the Task Contract and project binding.

## Deployment topology

For the MVP, keep `framework/` in `intellix-plugin`, but enforce extraction-ready
boundaries:

- no `${CLAUDE_PLUGIN_ROOT}` dependency inside the kernel;
- no plugin version inside the kernel;
- every CLI accepts an explicit `--root` project path;
- adapters depend on the kernel, never the reverse;
- projects pin framework version and digest;
- installation/sync is one-way from repository source to runtime targets.

Extract to `intellix-engineering-framework` only after a real client project uses
the kernel independently or independent release cadence becomes necessary.

## Project profiles

| Profile | Contract requirement | Typical gates |
|---|---|---|
| `micro` | Lite Task Contract for non-trivial changes | schema, tests, fileset |
| `standard` | Full Task Contract | CI, independent review, risk gates |
| `regulated` | Full contract plus authenticated approvals and evidence retention | security, compliance, human gate, staged release |

## Non-goals for MVP

- autonomous agent organization;
- permanent agents per technical layer;
- a general-purpose workflow engine;
- authenticated approval implemented as editable local JSON;
- automatic merge, deploy or production mutation;
- rewriting historical `issues/`.
