# ADR-0004: Typed decision layer as a governed IntelliX capability

Status: Proposed
Date: 2026-09-23
Related: ADR-0001 (Accepted), ADR-0002 (Accepted), ADR-0003 (Accepted); TASK-010
Authority: `framework/framework.yaml` and its referenced policies remain normative

## Context

IntelliX projects repeatedly contain small semantic decisions over text: message
intent, ticket routing, lead stage, review theme, "does this need an LLM", "does
this need a human". Today these are solved ad hoc, usually by prompting a
generative LLM and parsing its answer.

Two "System One" engines now answer these decisions directly with typed outputs
(`choice`, `score`, `noul`) and per-option probabilities, without generating text:

| | Laya (Convai Innovations) | Jev (TypeSafe AI) |
|---|---|---|
| Distribution | open weights, Apache 2.0, self-hosted | hosted API only |
| API | `laya-serve` exposes `POST /v1/systemone` | `POST /v1/systemone` |
| Data residency | stays in the operator's environment | leaves the country |
| Fine-tuning | supported | not available |
| Out-of-box Portuguese | weak and uncalibrated (published) | not guaranteed (published) |

Because the request/response shape is shared, the engine is configuration, not
code. The methodology to use them safely already exists, but only as a Claude
skill in the user's global configuration (`intellix-decision-layer`). It is not
vendor-neutral, not visible to the Codex adapter, and not enforced by the kernel.

Four risks make this an architectural concern rather than a library choice:

1. both engines are documented as manipulable by instructions injected in the
   input text;
2. a probability is not a correctness guarantee; Laya ships over-confident and
   Jev's `confidence` field is a concentration statistic;
3. an automated decision can trigger an irreversible action (refund, deletion,
   external message) if nothing prevents it;
4. sending customer text to an external engine is an international transfer of
   personal data under LGPD.

A further concern is placement. The engine runtime and its credentials belong to
the operator's machine or infrastructure, not to any single project repository,
and must never be committed.

## Decision

### 1. Vendor-neutral methodology

The normative methodology moves to `references/decision-layer.md` in this plugin:
the L0 code → L1 engine → L2 LLM → L3 human cascade, risk classes A/B/C/D/S,
threshold policy on the calibrated probability of the chosen option (`pMax`),
mandatory abstention option, shadow pilot and calibration procedure, engine
selection rules, and LGPD constraints. The Claude skill becomes an adapter
convenience that points to this reference. The Codex adapter reads the same file.
The reference cannot override `framework/framework.yaml`, a project contract, an
ADR, a Task Contract or CI.

### 2. Optional project declaration

A project that uses the capability declares it in `intellix.yaml`:

```yaml
decision_layer:
  enabled: true
  engines_permitted: [laya, jev]       # subset; empty means none
  data_residency: local_only           # local_only | external_allowed
  registry: docs/decisions/DECISIONS.yaml
```

`data_residency: local_only` forbids external engines for that project. Absence
of the block means the capability is not used; existing projects stay valid.

### 3. Decision registry

Each automated semantic decision is one registry entry: identifier, risk class,
question and options (including abstention), engine and pinned model version,
thresholds, calibration parameters, and a reference to pilot evidence. Rules the
validator will enforce once implemented:

- class `D` entries can never have an automatic action;
- an entry without accepted pilot evidence can run only in `shadow` mode;
- an entry using an engine outside `engines_permitted`, or an external engine
  under `local_only`, is invalid;
- every `choice` question declares an abstention option.

### 4. Task Contract rules

- A task that enables automatic action for a class `C` decision has risk level
  `high` or above.
- Actions downstream of a class `D` decision are listed in
  `risk.irreversible_actions` and remain behind the human gate.
- A task that switches a decision from `shadow` to automatic mode lists the gate
  `decision_pilot`, satisfied only by pilot evidence meeting the class targets.

### 5. Machine-level runtime and credentials

The runtime is provisioned once per operator machine, outside any repository:

- Laya: an isolated environment under `~/.intellix/runtimes/laya/`, package
  version pinned, model weights pinned by Hugging Face revision with a recorded
  SHA-256 manifest, `laya-serve` bound to `127.0.0.1` only.
- Jev: the key lives in the operating system keychain as `TYPESAFE_API_KEY` and
  is exported to processes at launch. It is never written to a repository,
  `.env` template, log, report or runtime record.
- A read-only toolchain check reports presence, pinned versions and reachability
  without printing secrets.

Provisioning downloads external artifacts and involves credentials. It is a
human-authorized platform action, never an implicit executor step. Production
hosting for a given project is decided in that project's own ADR.

### 6. Reusable pilot harness

The plugin ships a harness that runs one or both engines over a labeled JSONL set
through the same adapter contract, fits temperature where required, reports
precision by probability band, coverage and abstention, and emits pilot evidence
in a documented schema. Customer text is minimized before use, is never
committed, and pilot outputs are written to the gitignored runtime path.

### 7. Phase placement

| Phase | Obligation |
|---|---|
| PRD | Record "evaluate decision layer" as an open decision when requirements mention high-volume, real-time or data-sensitive text decisions |
| Architecture | Project ADR applying the adoption checklist and engine selection; create the decision port even when starting without an engine |
| `/plan` | Registry entry drafted; risk class drives Task Contract risk and gates |
| Integration | Single adapter, contract test against the chosen engine, timeout and fallback to L2/L3 |
| Security | Injection, data residency, runtime exposure, `devsecops` gate |
| Tests | Labeled set as a scheduled regression suite, not a per-PR check |

### 8. Use inside the IntelliX development workflow

The workflow itself makes repeated semantic decisions through keyword rules that
misfire (skill routing, external-research and library-documentation triggers).
The engine may be used there only under these invariants, each to be enforced by
a test or validator rule:

1. **Never in a blocking path.** No `PreToolUse` hook, gate or kernel step waits
   on the engine.
2. **Fail open to current behavior.** The existing rule always runs and is the
   default answer; engine absence, error, version mismatch or a 400 ms budget
   overrun returns that answer silently.
3. **Ratchet up only.** The engine may add a suggestion, a warning or a higher
   risk; it may never remove a warning, waive a gate or lower a risk.
4. **Outside the authority chain.** Engine output is never review, approval or
   completion evidence (ADR-0003).
5. **Local by default.** The development workflow uses the local Laya runtime;
   an external engine requires an explicit per-point exception with no customer
   content or secret.
6. **Pinned and reversible.** Package, weights and thresholds are pinned; a
   kill switch disables the engine without code changes.

Adoption is phased: measure the current rules with local decision logs and
implicit labels (no engine), then shadow, then advisory above a calibrated
threshold. Each phase has a stop criterion; failing it leaves the current
rules in place. Gates, approvals, security and secret or personal-data
detection are permanently excluded.

Risk assessment (architect estimate, probability x impact on 1-5 scales): without
these invariants, process blocking scores 20 and control downgrade 15; with them,
all residual risks are 6 or lower, the highest being maintenance cost exceeding
benefit. The full analysis and queue plan are in the accompanying handoff
document.

## Consequences

- Semantic decisions become declared, reviewable and testable artifacts instead
  of prompts buried in code.
- The kernel gains enforceable invariants for the most dangerous failure modes:
  automatic irreversible actions, unpiloted automation and prohibited data
  transfer.
- Both adapters share one methodology; the Claude-only skill stops being the
  source of truth.
- Operators must provision a runtime and a credential before piloting. Projects
  that do not declare the capability pay nothing.
- The validator, schemas and harness grow. This is new kernel surface and needs
  its own tests.

## Alternatives considered

- **Keep it as a Claude-only skill.** Rejected: invisible to Codex and
  unenforced.
- **Per-project installation and credentials.** Rejected: duplicates a machine
  concern across repositories and increases the chance of committed secrets.
- **Standardize on one engine.** Rejected: Laya is required when data must stay
  local or fine-tuning is needed; Jev covers high-cardinality and long inputs.
  The shared API makes supporting both cheap.
- **No kernel rules, methodology only.** Rejected: the irreversible-action and
  data-residency failures are exactly the ones methodology alone does not stop.

## Implementation boundaries

This ADR authorizes nothing by itself. After acceptance, implementation is split
into separate Task Contracts, each with its own review and CI:

1. development-workflow phase 0: decision port, local decision log and implicit
   labels for the existing rules, with no engine;
2. neutral reference and skill-to-reference pointer;
3. `intellix.yaml` schema extension, registry schema and validator rules with tests;
4. pilot harness and pilot-evidence schema with tests;
5. toolchain check (read-only);
6. runtime provisioning procedure, executed only with explicit human
   authorization for downloads and credentials.

## Open questions

- Minimum labeled sample and exact class targets remain the ones in the current
  methodology (300 per decision; 85/92/97%). Confirm or revise at acceptance.
- Whether `decision_pilot` becomes a policy-level gate in `framework/policies/`
  or a registry-level rule only.
- Production hosting pattern for Laya under the Cloudflare deployment default.
