# ADR-0004: Typed decision layer as a governed, per-project IntelliX capability

Status: Proposed
Date: 2026-09-23 (revision 2, after Codex independent review of the same date)
Related: ADR-0001, ADR-0002, ADR-0003 (Accepted); TASK-010; follow-up TASK-011
Authority: `framework/framework.yaml` and its referenced policies remain normative

## Context

IntelliX client systems repeatedly contain small semantic decisions over text:
message intent, ticket routing, lead stage, review theme, "does this need an
LLM", "does this need a human". They are usually solved by prompting a
generative LLM and parsing its answer.

A class of "System One" engines answers such decisions directly: it receives a
text state and typed questions (`choice`, `score`, `noul`) and returns typed
answers with per-option probabilities, without generating text. Two exist today:
Laya (open weights, self-hosted) and Jev (hosted API). Both are weeks old at the
time of writing, their published benchmarks are produced by their own authors,
and neither guarantees Portuguese.

The methodology to evaluate and use them safely exists as the skill
`intellix-decision-layer`, but only in the operator's global configuration and
documentation folder. It is not versioned in this repository, no phase invokes
it, and the Codex adapter cannot read it. An evaluation that no phase requires
can be skipped silently.

The architectural concerns are: engines are documented as manipulable by
injected instructions; a probability is not a correctness guarantee;
an automated decision can precede an irreversible action; customer text sent to
an external engine or LLM is an international transfer under LGPD; and engine
facts change faster than any normative document.

## Decision

### 1. Scope: client systems only

The capability is evaluated **per client project**. It is **not adopted inside
the IntelliX development workflow** (skill routing, research triggers, review or
CI triage, task risk): the volume is low, an LLM already reads the same context,
and the decisions that matter there (risk, gates, approval, completion) must not
depend on a probabilistic classifier. Any future proposal to use an engine in
the workflow requires a new ADR and must satisfy the invariants below.

### 2. Invariants

1. The layer never participates in the IntelliX framework approval chain.
2. No failure of the layer can block the development process.
3. The layer never lowers a risk, gate, warning or approval requirement.
4. Adoption in a project requires the checklist, a project ADR and a human decision.
5. Irreversible, financial, permission or production actions are never executed
   by an engine.
6. Deterministic rules precede the typed engine (cascade L0 rule → L1 engine →
   L2 LLM → L3 human).
7. Untrusted text is data (`state`); instructions and options are versioned on
   the server side.
8. Every decision has an abstention option and an explicit, per-decision fallback.
9. Thresholds are calibrated on real domain data and bound to the model version.
10. Changing the model, weights, questions, options, temperature, preprocessing
    or policy invalidates the calibration.
11. No engine enters active mode before an approved shadow pilot.
12. Personal data follows minimization, legal basis, retention and a location
    compatible with the project's residency constraint.
13. Credentials are never stored in a repository or in the decision log.
14. The decision port does not presume compatibility between vendors; each
    adapter proves its contract with real fixtures.
15. Removing or disabling the engine preserves safe operation through L0/L2/L3.

### 3. Normative rule versus volatile facts

The methodology is split in two:

- **Normative** (`references/decision-layer.md`): cascade, risk classes,
  invariants, adoption checklist, proportional port rule, shadow pilot and
  calibration procedure, invalidation events, fallback and residency rules.
  It contains no vendor benchmark, price or latency.
- **Informative** (`references/engines-YYYY-MM.md`): dated engine facts
  (versions, limits, published benchmarks, prices), each marked as vendor claim
  and each to be re-verified at use. Vendor claims are never production
  evidence; only the project's own pilot is.

Numeric values in the normative reference (for example 300 labeled cases per
decision, precision targets 85/92/97 %, 50 % coverage) are **configurable
starting defaults**, not universal rules. Rare or imbalanced decisions need
per-class analysis and may need more data; a class C decision may be worth
automating at low coverage if precision is proven and the economics justify it.

### 4. Risk class by concrete consequence

A decision's class is derived from the effect of acting on it in that project,
not from its name. The same field can be class A (informative tag), B (routing)
or C (a CRM stage change that notifies a customer). Class D (irreversible) never
executes automatically.

### 5. Decision port: neutral and proportional

The port is a neutral contract, not a System One contract:

```text
decide(decision_id, input) -> { option | abstain, probability | null,
                                source: rule | engine | llm | human,
                                reason, contract_version }
```

A System One engine is one adapter. Adapters normalize vendor differences
(model identifier location, meaning of confidence fields, usage, error kinds,
authentication) and must validate: maximum response size, expected model,
allowed options only, probability range and sum, and distinct failure kinds
(timeout, network, HTTP, invalid payload) for observability. Switching engines is
allowed only after contract tests with real fixtures from both providers.

A project creates the port only when at least one decision passes the adoption
checklist, or when its architecture ADR explicitly decides to stabilize an
L0/L2 interface for foreseeable evolution. Otherwise it records "not applicable"
or "not adopted" and creates no code.

### 6. Fallback respects residency

Each decision declares its fallback chain. When text may not leave the
environment, the chain may contain only L0 rules, a local engine and humans; an
external LLM is as forbidden as an external engine.

### 7. Calibration invalidation and automatic return to shadow

Any event in invariant 10, or a monitored drift beyond configured bounds
(abstention rate, human override rate, class distribution), returns the decision
to shadow mode automatically until a new calibration is approved.

### 8. Decision log

The log stores decision metadata, never raw customer text. Indirect references
(record identifiers) can still be personal data: the log follows the project's
RLS, retention and erasure procedures, including cascade deletion with the
referenced records.

### 9. Canonical location of the methodology

One skill identifier, `intellix-decision-layer`, versioned as a global skill in
`global-config/skills/intellix-decision-layer/` with `SKILL.md` and the two
references above. Phase skills reference it by that identifier. No
plugin-namespaced copy is created, to avoid two competing identifiers. Copying
the global configuration to `~/.claude` stays an explicit human action; the
Codex adapter reads the reference files by path.

### 10. Phase integration (TASK-011, after acceptance)

Only after this ADR is accepted, a single Task Contract (TASK-011) versions the
skill and its references and changes the three phases together, so a clean
checkout never references a missing capability:

- PRD (`ai-project-brainstorm`): when requirements include automated decisions
  over text at volume, in real time or on data that must stay local, record
  "evaluate decision layer" as an open decision;
- Architecture (`skills/architecture`): apply the checklist, record the outcome
  in the project's architecture ADR, including "not applicable", and create the
  port only under section 5;
- Agent creation (`intellix-agent-creation`): apply the decision already taken
  in the architecture phase to classifications the blueprint would otherwise
  take from the LLM's structured output.

### 11. Deferred to a first adopting project

Project schema declaration, decision registry and validator rules, pilot
harness, adapters and action policy, engine hosting, and any credential are
decided and implemented only inside a real project that passed the checklist,
each under its own Task Contract and that project's fileset. This ADR does not
authorize any of them, nor any kernel change.

## Consequences

- The evaluation stops being skippable and stops depending on one machine.
- Client projects gain a consistent, auditable way to adopt or reject the layer.
- Vendor volatility stays in dated informative references, not in the method.
- Projects that do not need the layer pay one line in their architecture ADR.
- Kernel and schema stay unchanged until real usage justifies them.

## Alternatives considered

- **Keep the skill only in the operator's configuration.** Rejected: not
  portable, invisible to Codex, silently skippable.
- **Adopt engines inside the development workflow.** Rejected for now: small
  benefit, maintenance cost dominant, decisions that matter must stay outside.
- **Add kernel schema and validator rules now.** Rejected: no adopting project
  yet; premature surface.
- **Standardize on one engine.** Rejected: data residency and fine-tuning favor
  a self-hosted engine; high cardinality and long inputs may favor a hosted one.
  The neutral port keeps the choice open.

## Open questions

- Whether a future `decision_pilot` gate belongs in `framework/policies/` or in a
  project-level registry rule; to be decided with the first adopting project.
