# IntelliX Engineering Plugin v3.0

> **Orquestrador principal:** [`skills/master-workflow/SKILL.md`](./skills/master-workflow/SKILL.md)
> Define o fluxo completo da ideia ao deploy — brainstorm → PRD → plano → 10 fases de execução.
>
> **Fonte única de verdade de arquitetura:** [`MASTER-ARCHITECTURE.md`](./MASTER-ARCHITECTURE.md)
> Estrutura de pastas, behavior isolation, repository/service, API standards, naming, segurança.
> **Leia antes de qualquer implementação.**

---

Plugin oficial da IntelliX.AI para Claude Code — opera como um **Senior Developer
de 15+ anos** especializado em SaaS e sistemas de grande escala. Integra skills
especializadas externas em cada fase para máxima qualidade e eficiência.

---

## Workflow Completo — Da Ideia ao Deploy

```
💡 IDEIA
 │
 ├─ superpowers:brainstorming     → valida ideia, explora ângulos
 ├─ ai-project-brainstorm         → PRD completo: personas, roadmap, stack
 ├─ superpowers:writing-plans     → plano executável com tasks e dependências
 │
 │  ← GATE: aprovação do plano
 │
 ├─ project-kickoff          → scaffolding + .intellix-phase
 ├─ code-audit               → (projetos existentes)
 ├─ architecture             → schema + routes + repository/service
 ├─ frontend-design          → vibestack → ui-ux-pro-max → frontend-design-pro
 │                              → ckm-ui-styling → web-design-guidelines
 ├─ agent-creation           → intellix-agent-creation (GPT Maker/n8n/Blueprint)
 ├─ dev-standards            → TypeScript + naming + patterns
 ├─ epic-workflow            → /spec → /break → /plan → /execute
 ├─ integration              → APIs + WhatsApp + n8n
 ├─ security-observability   → OWASP + rate limit + logs
 ├─ test-e2e                 → SKILL_TestE2E (smoke → stress)
 ├─ deploy                   → Vercel + Cloudflare
 └─ project-handoff          → README + ADRs + docs
```

---

## Dois modos de operação

### Modo 1 — Criação (sistema novo)
```
1. superpowers:brainstorming        → ideação e validação
2. ai-project-brainstorm            → PRD completo
3. superpowers:writing-plans        → plano aprovado
4. intellix:project-kickoff         → scaffolding
5. fases 01 → 09 sequencialmente
```

### Modo 2 — Auditoria/Refatoração (sistema existente)
```
1. /intellix:audit                  → gap analysis + score + roadmap
2. superpowers:writing-plans        → plano de refatoração
3. fases IntelliX conforme gaps
```

---

## Fluxo completo — 11 fases

| Fase | Skill | O que faz |
|------|-------|-----------|
| 00b | `code-audit` | **Auditoria de sistemas existentes** — 10 dimensões, score, roadmap |
| 00 | `project-kickoff` | Diagnóstico, scaffolding, estrutura canônica |
| 01 | `architecture` | Schema Supabase, data layer, repository/service, API design, RBAC |
| 02 | `frontend-design-workflow` | Design system, UI/UX, implementação visual (vibestack→ux→design-pro) |
| 03 | `agent-creation` | Blueprints de agentes: GPT Maker / n8n / nativo *(opcional)* |
| 04 | `dev-standards` | TypeScript strict, Server Actions, TanStack Query, caching, formulários |
| 05 | `integration` | SDKs nativos (Anthropic/OpenAI), WhatsApp, Supabase Realtime, n8n opcional |
| 06 | `security-observability` | OWASP, rate limiting, Sentry, logging estruturado *(auto-nível)* |
| 07 | `test-e2e` | TDD, Vitest, Playwright, testes de integração |
| 08 | `deploy` | Vercel, CI/CD GitHub Actions, DevOps, runbook, feature flags |
| 09 | `handoff` | README técnico, ADRs, acesso ao cliente |
| 10 | `live-chat` | Chat omnichannel IA + humano *(opcional)* |

---

## Padrões arquiteturais aplicados

**Clean Architecture:**
```
UI Components → Services → Repositories → Supabase
                ↑               ↑
           Lógica de       Acesso a dados
           negócio         (isolado)
```

**API Design (RFC 7807 adaptado):**
```typescript
// Sucesso: { data: T, meta?: { total, cursor } }
// Erro:    { error: { code, message, details? } }
```

**Camadas obrigatórias:**
```
src/
├── app/              # Next.js routes + Server Actions
├── components/       # UI components (sem lógica de negócio)
├── services/         # Lógica de negócio
├── repositories/     # Acesso a dados (Supabase)
├── lib/              # Utilitários, validações, API response
├── hooks/            # Custom hooks (TanStack Query)
└── types/            # Tipos TypeScript centralizados
```

---

## Stack padrão (imutável)

| Camada | Tecnologia |
|--------|-----------|
| Framework | Next.js 15 App Router |
| Linguagem | TypeScript strict |
| Estilo | Tailwind CSS + Shadcn/UI |
| Banco | Supabase (PostgreSQL + Auth + RLS + Edge Functions) |
| Deploy | Vercel |
| CI/CD | GitHub Actions |
| Testes | Vitest (unit) + Playwright (E2E) |
| Monitoring | Sentry + structured logging |
| State | TanStack Query + Zustand + Server Actions |
| Validação | Zod + React Hook Form |

---

## Comandos disponíveis

```
/intellix:new-project   → Inicia novo projeto (Fase 00)
/intellix:audit         → Audita sistema existente (Fase 00b)
/intellix:deploy        → Checklist de deploy + DevOps (Fase 08, manual)
```

---

## Instalação

### Por projeto (persistente)
Adicione ao `.claude/settings.json` do projeto:
```json
{
  "plugins": [
    { "type": "local", "path": "/caminho/para/intellix-plugin" }
  ]
}
```

### Global (todos os projetos)
```bash
/plugin marketplace add intellixai/marketplace
/plugin install intellix@intellixai-marketplace
```

---

## Estrutura do plugin

```
intellix-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── master-workflow/          # Orquestrador principal do fluxo IntelliX
│   ├── project-kickoff/          # Scaffolding inicial
│   ├── code-audit/               # ★ Auditoria de sistemas existentes
│   ├── architecture/             # Data layer, API design, RBAC
│   ├── frontend-design/          # ★ Design system + UI/UX
│   ├── agent-creation/           # Blueprints de agentes
│   ├── dev-standards/            # TS, Server Actions, TanStack Query
│   ├── integration/              # Native-first, n8n opcional
│   ├── security-observability/   # ★ OWASP + Sentry + rate limit
│   ├── test-e2e/                 # Playwright + Vitest
│   ├── deploy/                   # Vercel + CI/CD + DevOps
│   ├── project-handoff/          # Documentação + entrega
│   └── live-chat/                # Omnichannel (opcional)
├── commands/
│   ├── new-project.md
│   ├── audit.md                  # ★ NOVO
│   └── deploy.md
└── hooks/
    ├── hooks.json
    └── scripts/
        ├── session-start.sh      # Injeta contexto Senior Dev
        └── skill-router.sh       # Sugere skills por palavras-chave
```

★ = Novo na v2.0

---

## Desenvolvido por
IntelliX.AI — https://intellixai.com.br
