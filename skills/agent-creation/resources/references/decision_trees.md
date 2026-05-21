# Decision Trees Reference

Quick-reference decision trees for agent generation. Used by the Agent Creation Engine during blueprint generation.

---

## 1. Single vs Multi-Agent

```
User describes a process with:

  1-2 distinct responsibilities?
    → SINGLE AGENT
    (even if complex, use a detailed workflow with conditions)

  3+ distinct responsibilities with different expertise?
    → MULTI-AGENT SYSTEM
    (each responsibility becomes an agent role)

  User explicitly requests multi-agent?
    → MULTI-AGENT SYSTEM
    (regardless of complexity)
```

**Examples:**
- "Agent that answers questions about my dental clinic" → Single (one responsibility: answer questions)
- "Agent that qualifies leads and moves them in the pipeline" → Single (two related responsibilities, one domain)
- "System that handles reception, qualification, scheduling, follow-up and billing" → Multi (5 distinct responsibilities)

---

## 2. Operation Mode

| Scenario | Mode |
|---|---|
| Agent runs inside CRM/ERP/SaaS dashboard | embedded |
| Agent talks to customers via WhatsApp/Telegram/email | external |
| Agent does both (e.g. WhatsApp + admin dashboard panel) | hybrid |
| Agent processes data in background (cron/batch) | embedded |
| Agent exposes an API for other systems | embedded |

---

## 3. Reasoning Strategy

| Scenario | Strategy | Temperature |
|---|---|---|
| Fixed workflow, no decisions (send notification, execute steps) | deterministic | N/A |
| Pick which tool to use based on user input (80% of agents) | react | 0.3 |
| Need step-by-step analysis (lead scoring, diagnosis triage) | chain_of_thought | 0.2 |
| Evaluate multiple paths (complex negotiation, optimization) | tree_of_thought | 0.2 |
| Plan all steps before executing any (orchestrator) | plan_and_execute | 0.2 |

---

## 4. Memory Configuration

| Need | Type | Enable When |
|---|---|---|
| Remember current conversation | short_term | Always (default on) |
| Remember across sessions | long_term | Agent sees same user again |
| Search knowledge base / catalog | episodic (RAG) | Agent needs FAQ, products, docs |
| One-shot processing, no memory | short_term only | Batch/cron agents |

**Summarization:**
- Enable if conversations typically exceed 15 messages
- Strategy: key_points for customer-facing, rolling_summary for internal

---

## 5. Orchestration Type (Multi-Agent)

| Process Pattern | Type |
|---|---|
| Customer moves through stages in order | event_driven |
| Steps always execute in same order | sequential |
| Some steps can run simultaneously | parallel |
| Supervisor delegates to workers | hierarchical |
| Agents must agree before acting | consensus |

**Default: event_driven** — covers 90% of customer journey use cases.

---

## 6. Follow-Up Sequence Type

| Trigger Event | Sequence Type | Duration | Max Messages |
|---|---|---|---|
| New hot lead, no response in 1h | quick_follow_up | 24-48h | 2-3 |
| Lead qualified but not ready to buy | warm_nurturing | 2-3 weeks | 5-7 |
| Lead inactive 30+ days | cold_reactivation | 2 weeks | 3 |
| After appointment/service delivery | post_appointment | 1-3 days | 1-2 |
| After sale/contract | post_sale | 1-4 weeks | 3-5 |
| Before scheduled appointment | reminder | 24h + 1h before | 2 |

**Priority (higher cancels lower):**
quick > warm > pipeline > post_appointment > post_sale > cold_reactivation

---

## 7. Tool Type Selection

| Need | tool_type |
|---|---|
| Call external REST/GraphQL endpoint | api_call |
| Use MCP server tool | mcp_tool |
| Execute internal logic (scoring, routing) | function |
| Send data to external webhook (n8n, Zapier) | webhook |
| Read/write database directly | database_query |
| Read/write files | file_operation |
| Call another LLM for sub-tasks | llm_call |

---

## 8. Channel Provider Selection

| Channel | Common Providers |
|---|---|
| WhatsApp | evolution_api, cloud_api (Meta), z_api, wppconnect |
| Telegram | Telegram Bot API (native) |
| Instagram | Meta Graph API |
| Email | SendGrid, Resend, SES, SMTP |
| Voice | Twilio, Vapi, Bland AI |
| SMS | Twilio, Vonage |

**Note:** Provider is a pending_configuration — the user fills it during setup. The blueprint specifies the interface structure, not the specific provider.

---

## 9. Guardrail Selection by Niche

| Niche | Hard Block Guardrails |
|---|---|
| Healthcare | Never diagnose, never share patient data, escalate emergencies |
| Real Estate | Never invent features, never share exact address, escalate negotiations |
| Financial | Never give investment advice, never guarantee returns, escalate compliance |
| Legal | Never provide legal advice, always disclaim, escalate complex cases |
| E-commerce | Never guarantee delivery dates, escalate payment disputes |
| Education | Never guarantee certification, escalate payment issues |
| Generic | Never invent information, escalate when uncertain, respect privacy |

---

## 10. Compliance Framework by Region/Niche

| Region + Niche | Frameworks |
|---|---|
| Brazil (any) | LGPD |
| Brazil + Healthcare | LGPD, CFM/CRO resolutions |
| Brazil + Real Estate | LGPD, CRECI norms |
| Brazil + Financial | LGPD, BACEN regulations |
| Brazil + Legal | LGPD, OAB ethics code |
| Brazil + E-commerce | LGPD, CDC |
| EU (any) | GDPR |
| US + Healthcare | HIPAA |
| US + Financial | SOX, SOC2 |
