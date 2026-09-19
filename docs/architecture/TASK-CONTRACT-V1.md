# Task Contract v1

Status: Proposed for human approval

Date: 2026-09-17

## Purpose

The Task Contract is the smallest auditable unit of implementation, concurrency
and handoff. Chat history is never a substitute for it.

## Required contract

```yaml
id: TASK-001
title: Outcome-oriented title
status: DRAFT | READY | IN_PROGRESS | IN_REVIEW | BLOCKED | DONE
objective: One independently verifiable outcome
source:
  prd: docs/product/PRD.md
  architecture: docs/architecture/ARCHITECTURE.md
  spec: SPEC.md
  adrs: []
risk:
  level: low | medium | high | critical
  reasons: []
  irreversible_actions: []
assignment:
  primary_role: backend-engineer
  consult_roles: [security-reviewer]
  executor: codex
  reviewer: claude
scope:
  create: []
  modify: []
  forbidden: []
dependencies: []
acceptance_criteria: []
verification: []
gates: []
rollback: null
handoff:
  required_evidence: []
  open_questions: []
```

JSON-compatible YAML remains acceptable for the dependency-free MVP. The schema
is the authority; this example is explanatory.

## Definition of Ready

A task becomes `READY` only when:

- sources exist inside the declared project root;
- ID matches the filename;
- outcome and acceptance criteria are testable;
- primary/consult roles exist in the Role Registry;
- executor is installed or a permitted fallback is explicit;
- executor and reviewer are independent;
- filesets are repository-relative, bounded and collision-free;
- dependencies are acyclic and satisfied;
- gates meet or exceed the risk policy;
- high/critical risk has rollback and required human decision.

## Derived execution metadata

Branch and worktree paths should normally derive from project + task ID instead
of being manually entered. Runtime records bind:

- task digest;
- implementation commit SHA;
- selected adapter and roles;
- verification evidence;
- CI provider and exact revision;
- review provenance;
- human approval reference when required.

## Trust limits

Editable local fields such as `actor: human` cannot prove identity. Approval and
waiver records are audit indexes pointing to authenticated evidence, not authority
by themselves. A contract cannot waive mandatory failing CI or reviewer
independence.

## Profiles

The `micro` profile may use a generated lite form, but it must retain objective,
risk, fileset, acceptance, verification and ownership. Standard and regulated
profiles use the full schema.
