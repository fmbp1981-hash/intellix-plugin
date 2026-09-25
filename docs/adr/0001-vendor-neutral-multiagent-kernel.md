# ADR-0001: Vendor-neutral multi-agent engineering kernel

Status: Proposed — human approval not yet recorded

Date: 2026-09-16

Related: ADR-0002 (Accepted, 2026-09-18)

ADR-0001 remains a proposed kernel decision; no explicit human acceptance of
this ADR has been recorded. ADR-0002 separately accepts the operational dynamic
orchestrator and its trust boundaries. That acceptance does not change this
ADR's status or override `framework/framework.yaml` and its referenced policies.

## Context

The IntelliX method already had mature phases, skills, hooks, tests and reviews,
but normative behavior was duplicated and execution was coupled to Claude Code.
The proposed orchestrator diagram added useful specialist accountability while
risking more permanent agents, handoffs and sources of truth.

## Decision

Adopt one machine-readable kernel, project and Task Contracts, vendor adapters,
independent review and deterministic CI. Use Codex as the default executor and
Claude as default architect/reviewer. Model database/backend/frontend as roles
selected per task, not mandatory agents. Require worktree isolation by risk and
human approval for irreversible/production actions.

## Consequences

Work becomes portable and auditable, parallelism is bounded by fileset ownership,
and neither vendor is the source of truth. Existing Claude automation must be
adapted gradually. Contracts add up-front discipline but reduce rework and
ambiguous handoffs.
