# Migration to the IntelliX multi-agent framework

## Phase 0 — Land the kernel (this release)

- Add canonical framework, policies, roles and schemas.
- Add project and agent adapters.
- Add Task Contract templates, validator, tests and CI.
- Make plugin, marketplace and canonical versions converge.

Exit: `framework/validate.py --all` and tests pass in a clean checkout.

## Phase 1 — New work uses Task Contracts

- Keep historical `issues/*.md` read-only.
- `/break` creates draft `tasks/TASK-NNN.yaml` contracts.
- `/plan` completes risk, fileset, verification and ownership.
- `/execute` validates the contract and routes to the assigned executor.

Exit: every new implementation PR references a validated Task Contract.

## Phase 2 — Enforce repository gates

- Protect `main`; require framework and project CI.
- Add language-specific lint/type/test/build and security jobs.
- Require CODEOWNERS/human approvals for production and high-risk surfaces.
- Store handoffs, approvals and waivers as CI artifacts or versioned records.

Exit: merge is impossible with a failed mandatory gate.

## Phase 3 — Migrate active legacy issues

- Convert only active issues; do not rewrite history.
- Map prose sections to source, scope, acceptance, verification and gates.
- Detect overlapping filesets before parallel execution.
- Deprecate issue execution after one stable release cycle.

Exit: no active work depends on legacy issue semantics.

## Phase 4 — Operational maturity

- Add repository-specific observability and release evidence.
- Measure lead time, change failure rate, escaped defects and waiver ageing.
- Review roles/policies quarterly; change normative behavior by ADR/version.

Exit: governance metrics drive changes instead of prompt proliferation.

## Rollback

Revert this release branch before adoption, or pin projects to framework 1.0.0.
Because existing commands and global configuration remain as compatibility
adapters, landing the kernel does not invalidate historical projects.
