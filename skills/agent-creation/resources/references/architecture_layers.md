# IntelliX AgentOS — Architecture Layers Reference

This document describes the 10 architectural layers of the IntelliX AgentOS. Each layer maps to specific sections of the Agent Blueprint Schema v2.

Use this reference when generating blueprints to ensure all layers are properly configured.

---

## Layer Overview

```
┌─────────────────────────────────────────────────┐
│  1. INTERFACE LAYER                             │
│     How the agent communicates with the world    │
├─────────────────────────────────────────────────┤
│  2. AGENT LAYER                                 │
│     Identity, role, capabilities                 │
├─────────────────────────────────────────────────┤
│  3. ORCHESTRATION LAYER                         │
│     Routing, multi-agent coordination            │
├─────────────────────────────────────────────────┤
│  4. COGNITIVE LAYER                             │
│     Observe → Think → Plan → Act → Reflect → Learn │
├─────────────────────────────────────────────────┤
│  5. MEMORY LAYER                                │
│     Short-term, long-term, episodic (RAG)        │
├─────────────────────────────────────────────────┤
│  6. TOOL LAYER                                  │
│     APIs, MCP, functions, webhooks, DB queries   │
├─────────────────────────────────────────────────┤
│  7. EXECUTION LAYER                             │
│     Runtime, error handling, retry, rollback     │
├─────────────────────────────────────────────────┤
│  8. LEARNING LAYER                              │
│     Feedback, performance tracking, knowledge    │
├─────────────────────────────────────────────────┤
│  9. GOVERNANCE LAYER                            │
│     Permissions, audit, safety, compliance       │
├─────────────────────────────────────────────────┤
│ 10. INFRASTRUCTURE LAYER                        │
│     Runtime environment, providers, deployment   │
└─────────────────────────────────────────────────┘
```

---

## 1. Interface Layer

**Blueprint sections:** `interfaces`

The interface layer defines how the agent communicates with external users and systems. Each interface is a communication channel with its own protocol, authentication and delivery characteristics.

**Supported interfaces:**

| Interface | Use Case | Protocol | Latency |
|---|---|---|---|
| system_ui | Embedded chat/panel inside web app | WebSocket/REST | <100ms |
| api | Programmatic access from other systems | REST/GraphQL/MCP | <200ms |
| whatsapp | Customer messaging via WhatsApp | Webhook (inbound) + API (outbound) | 1-5s |
| telegram | Customer messaging via Telegram | Webhook + Bot API | 1-3s |
| instagram | Customer messaging via Instagram DM | Webhook + Graph API | 2-5s |
| email | Email-based interactions | Webhook (inbound) + SMTP/API (outbound) | 5-30s |
| voice | Phone/voice interactions | WebSocket/VOIP | Real-time |

**Design principles:**
- An agent can have multiple interfaces active simultaneously
- The same agent logic handles all channels — only the transport differs
- Channel-specific formatting (e.g. no markdown on WhatsApp) is handled at the interface layer
- Provider credentials are always in pending_configuration, never hardcoded

---

## 2. Agent Layer

**Blueprint sections:** `agent_metadata`, `objective`, `operation_mode`, `prompt_template`

The agent layer defines who the agent is, what it does and how it operates. This is the agent's identity and mission.

**Components:**

- **Identity** (agent_metadata): Name, type, domain, version, tags
- **Mission** (objective): Primary goal, secondary goals, success criteria, constraints
- **Operation** (operation_mode): Embedded vs external vs hybrid, runtime environment, concurrency
- **Personality** (prompt_template): System prompt, tone, guardrails, few-shot examples

**Design principles:**
- One agent = one clear responsibility. If responsibilities diverge, use multi-agent.
- The agent_name should reflect the role (ReceptionAgent, not Bot1)
- Constraints in objective are hard limits — they appear in both objective.constraints AND prompt_template.guardrails
- The system_prompt is the single most important artifact — it defines behavior more than any other field

---

## 3. Orchestration Layer

**Blueprint sections:** `multi_agent`, `workflow` (for single-agent routing)

The orchestration layer manages how work flows through the system — whether within a single agent's workflow or across multiple cooperating agents.

**Single-agent orchestration:**
- Handled by the `workflow` array
- Steps execute in sequence with conditions for branching
- The workflow IS the orchestration

**Multi-agent orchestration:**
- Handled by `multi_agent.orchestration`
- A dedicated orchestrator agent routes messages to the right specialist
- Routing rules map conditions to agent_refs
- Escalation chains define fallback paths

**Orchestration types:**

| Type | Pattern | Example |
|---|---|---|
| sequential | A → B → C → D | Simple pipeline processing |
| parallel | A + B + C simultaneously | Parallel data collection |
| event_driven | Route based on events | Customer journey (recommended) |
| hierarchical | Supervisor delegates to workers | Manager + specialists |
| consensus | Agents vote/agree | Multi-model ensemble (rare) |

**Design principles:**
- Prefer event_driven for customer-facing systems
- Always have a human fallback in the escalation chain
- Limit max_handoffs_per_session (default 5) to prevent infinite loops
- The customer should never perceive agent changes — seamless experience

---

## 4. Cognitive Layer

**Blueprint sections:** `cognitive_loop`, `reasoning`

The cognitive layer implements how the agent thinks. It follows the Observe → Think → Plan → Act → Reflect → Learn cycle.

**Phases:**

| Phase | What Happens | Blueprint Config |
|---|---|---|
| Observe | Collect data from environment | cognitive_loop.observe: data_sources, event_listeners |
| Think | Analyze context, classify intent | cognitive_loop.think: analysis_strategy, context_window |
| Plan | Decide what to do next | cognitive_loop.plan: planning_method, max_steps, constraints |
| Act | Execute tools, send responses | cognitive_loop.act: execution_mode, timeout, rollback |
| Reflect | Evaluate outcome quality | cognitive_loop.reflect: criteria, threshold, logging |
| Learn | Update knowledge if needed | cognitive_loop.learn: type, frequency, review |

**Reasoning strategies:**

| Strategy | When to Use | Cognitive Loop |
|---|---|---|
| deterministic | Fixed script, no decisions | Disabled |
| react | Most agents — decide tool + act | Enabled, simple config |
| chain_of_thought | Complex analysis before action | Enabled, detailed think phase |
| tree_of_thought | Multiple paths to evaluate | Enabled, advanced plan phase |
| plan_and_execute | Plan all steps upfront | Enabled, full plan phase |

**Design principles:**
- 80% of agents use `react` strategy — start there unless you have a reason not to
- Enable cognitive_loop only for non-deterministic agents
- Keep max_reasoning_steps low (5-8) to prevent runaway reasoning
- Reflection is valuable but optional — enable for customer-facing agents

---

## 5. Memory Layer

**Blueprint section:** `memory`

The memory layer manages what the agent remembers and for how long.

**Three memory types:**

| Type | Scope | Storage | Use Case |
|---|---|---|---|
| short_term | Current session | Context window | Conversation history (always on) |
| long_term | Across sessions | Database table | Customer records, interaction logs |
| episodic | Knowledge retrieval | Vector store (RAG) | FAQ, catalogs, documents, past interactions |

**Short-term memory design:**
- Always enabled
- max_messages: 20 for simple agents, 40-50 for complex conversations
- Enable summarization if conversations routinely exceed 15 messages
- Summarization strategies: key_points (extract important facts), rolling_summary (maintain running summary)

**Long-term memory design:**
- Define table schema with columns, types, indexes
- Always include organization_id for multi-tenancy
- Include timestamps (created_at, updated_at) for analytics
- Set TTL (ttl_days) to comply with data retention policies
- Index the most queried columns

**Episodic memory (RAG) design:**
- Choose embedding model based on language (multilingual models for pt-BR)
- Set similarity_threshold: 0.65-0.75 (lower for broader recall, higher for precision)
- Chunk strategy: semantic for documents, paragraph for structured content
- max_results: 3-5 for focused answers, 8-10 for comprehensive research

---

## 6. Tool Layer

**Blueprint section:** `tools`

The tool layer defines everything the agent can DO in the world. Every action maps to a tool.

**Tool types:**

| Type | Description | Example |
|---|---|---|
| api_call | Call external REST/GraphQL endpoint | WhatsApp API, scheduling API |
| mcp_tool | Use MCP server tool | Supabase MCP, Google MCP |
| function | Execute internal logic | Lead scoring, routing decisions |
| webhook | Send data to external webhook | n8n trigger, Slack notification |
| database_query | Read/write database directly | Supabase queries |
| file_operation | Read/write files | Upload/download documents |
| llm_call | Call another LLM for sub-task | Summarization, translation |

**Tool design principles:**
- Every tool MUST have a clear `description` — this is what the LLM reads to decide when to use it
- Parameters MUST be defined as JSON Schema — this enables both LLM tool-calling (Path B) and runtime execution (Path C)
- Always define error_handling with retry strategy and fallback
- Set rate_limits to prevent abuse and stay within provider limits
- Use config_ref in auth to reference pending_configuration — never hardcode credentials

**Tool naming convention:**
- tool_id: snake_case with verb prefix (tool_search_patient, tool_book_appointment)
- tool_name: human-readable in the business language (buscar_paciente, agendar_consulta)

---

## 7. Execution Layer

**Blueprint sections:** `workflow` (steps with on_error), `tools` (error_handling), `cognitive_loop.act`

The execution layer manages how actions are carried out, including error handling, retries, timeouts and rollbacks.

**Error handling hierarchy:**
```
Step fails
  → Check on_error.strategy
    → retry: try again (up to retry_count times)
    → skip: continue to next_step
    → fallback: jump to fallback_step
    → escalate: transfer to human
    → abort: stop execution
```

**Design principles:**
- Every step MUST have on_error defined
- Customer-facing agents: fallback to human escalation as last resort
- Internal/batch agents: can abort on failure
- Set realistic timeouts: 5s for DB queries, 10-15s for LLM calls, 25-30s for complex reasoning
- Log all errors for debugging (governance.audit)

**Timeout guidelines:**

| Operation | Recommended Timeout |
|---|---|
| Database query | 3-5s |
| External API call | 5-10s |
| LLM reasoning | 10-20s |
| Complex multi-step | 25-30s |
| File upload/download | 30-60s |

---

## 8. Learning Layer

**Blueprint section:** `learning`

The learning layer defines how the agent improves over time.

**Components:**

| Component | Purpose | Configuration |
|---|---|---|
| feedback_loop | Collect signals about performance | Method (explicit/implicit/human/automated), storage, cadence |
| performance_tracking | Monitor KPIs and alert on degradation | Metrics, calculations, thresholds |
| knowledge_update | Keep agent knowledge current | Trigger (manual/scheduled/event), validation, rollback |

**Feedback collection methods:**
- explicit_rating: User rates the interaction (thumbs up/down, 1-5 stars)
- implicit_signals: Derive from behavior (did user re-engage? did they escalate? how fast?)
- human_review: Human reviews and scores interactions periodically
- automated_metrics: System calculates metrics automatically (recommended default)

**Design principles:**
- Always track at least 3 metrics aligned with objective.success_criteria
- Set alert_thresholds to catch degradation early
- Default to manual knowledge_update with validation — auto-update is risky
- Enable rollback for knowledge updates in case of regression

---

## 9. Governance Layer

**Blueprint section:** `governance`

The governance layer ensures the agent operates safely, legally and within defined boundaries.

**Components:**

| Component | Purpose |
|---|---|
| permissions | What the agent can and cannot do (allowed_actions, denied_actions, approval_required) |
| audit | What gets logged, where, for how long |
| rate_limits | Operational limits (messages/min, tokens/request, cost/day) |
| safety | Content filters, PII handling, escalation triggers |
| compliance | Regulatory frameworks, data residency, consent |

**Audit levels:**
- none: No logging (not recommended)
- actions_only: Log tool calls and state changes
- actions_and_reasoning: Log tool calls + LLM reasoning (recommended for customer-facing)
- full_trace: Log everything including raw prompts and responses (for debugging)

**PII handling:**
- mask: Replace PII with *** in logs (e.g. "João ***" instead of "João Silva")
- redact: Remove PII from logs entirely
- encrypt: Store PII encrypted in logs
- allow: No PII handling (only for non-regulated contexts)

**Design principles:**
- Always enable audit for customer-facing agents
- Set max_cost_per_day_usd to prevent runaway costs
- Define escalation_triggers for every niche-specific risk scenario
- Compliance frameworks are mandatory for Brazil (LGPD always) — add industry-specific
- consent_required = true for first contact in healthcare and financial

---

## 10. Infrastructure Layer

**Blueprint sections:** `operation_mode.runtime_environment`, `integration`, `pending_configuration`

The infrastructure layer defines where and how the agent runs in production.

**Runtime environments:**

| Environment | Best For | Characteristics |
|---|---|---|
| supabase_edge_function | Most agents | Serverless, auto-scale, direct DB access, low latency |
| vercel_serverless | API-heavy agents | Edge network, good for REST APIs |
| n8n_workflow | Integration-heavy agents | Visual workflow, easy webhook management |
| standalone_server | High-volume/custom agents | Full control, persistent connections |

**Integration configuration:**
- primary_protocol: Matches the main communication pattern
- retry_policy: Exponential backoff is the safe default
- rate_limit: Must match provider limits (don't exceed WhatsApp's ~60/min)
- health_check: Enable for external integrations to detect outages

**Pending configuration:**
- This is the bridge between blueprint and deployment
- Every credential, URL, and environment-specific value is a pending_configuration
- Sensitive values are marked with sensitive: true — must be stored as env vars
- Each config has example_value to help the implementer understand the format

**Design principles:**
- The blueprint is infrastructure-agnostic — it describes WHAT, not WHERE
- pending_configuration captures everything that changes between environments
- The implementing tool (Claude Code, Antigravity) reads pending_configuration to know what to ask the user
- Default runtime_environment to supabase_edge_function unless there's a reason not to
