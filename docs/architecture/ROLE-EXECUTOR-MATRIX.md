# Role / Executor Matrix

Status: Proposed for human approval

Date: 2026-09-17

Roles describe capability and constraints. Adapters provide execution. No role
contains `preferred_adapter`.

| Canonical role | Purpose | Claude adapter | Codex adapter | Mandatory specialist gates |
|---|---|---|---|---|
| `architect` | Boundaries, ADRs, trade-offs | Primary | Supported | architecture approval |
| `product-spec-author` | Testable product behavior | Primary | Supported | product/spec approval |
| `database-engineer` | Schema, migrations, RLS | Supported | Primary | database + security |
| `backend-engineer` | Domain/application/API | Supported | Primary | tests + independent review |
| `frontend-engineer` | Accessible UI behavior | Supported | Primary | accessibility when applicable |
| `integration-engineer` | External contracts/resilience | Supported | Primary | contract + security |
| `platform-engineer` | CI, infrastructure, runtime | Supported | Primary | security + human for production |
| `test-engineer` | Independent test evidence | Supported | Primary | tests |
| `security-reviewer` | Threat/data/authorization review | Primary | Supported | security review |
| `accessibility-reviewer` | Accessibility assessment | Primary | Supported | accessibility review |
| `observability-reviewer` | Telemetry/runbook review | Primary | Supported | observability review |
| `release-manager` | Reversible release coordination | Supported | Supported | authenticated human gate |

“Primary” is a project default recommendation, not kernel policy. A Task Contract
may assign either adapter if capability, permissions and reviewer independence are
satisfied.

## Existing Claude agent mapping

| Existing agent | Canonical role |
|---|---|
| `model-writer` | `database-engineer` |
| `action-writer` | `backend-engineer` or `integration-engineer` |
| `component-writer` | `frontend-engineer` |
| `test-writer` | `test-engineer` |
| `spec-reviewer` | spec-review gate executed by an independent reviewer |
| `code-quality-reviewer` | quality-review gate executed by an independent reviewer |

These mappings are adapter configuration. They do not create a third role catalog.

## Selection rules

- select one primary role from the task outcome;
- add consult roles only for triggered risk/surface rules;
- never activate all roles by default;
- never let the same execution identity approve its own change;
- after three review cycles, escalate to a human/architecture decision.
