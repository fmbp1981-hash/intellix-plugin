---
name: intellix-master-workflow
description: >
  Orquestrador do workflow completo IntelliX — da concepção ao deploy.
  Use esta skill SEMPRE que o usuário mencionar: criar um sistema, desenvolver uma aplicação,
  novo projeto, começar do zero, "quero construir", "tenho uma ideia", "vou criar um SaaS",
  "preciso de um sistema", "como estruturar meu projeto", ou qualquer início de desenvolvimento.
  Esta skill define a sequência OBRIGATÓRIA de fases e skills que garante arquitetura limpa,
  código profissional e desenvolvimento sem retrabalho — do brainstorm ao handoff.
user-invocable: true
---

# IntelliX Master Workflow — Da Ideia ao Deploy

Este é o workflow completo IntelliX. Define a sequência exata de fases e skills
desde a primeira ideia até o sistema em produção.

> **Referência de arquitetura:** Consulte `MASTER-ARCHITECTURE.md` no plugin para
> todas as regras técnicas, estrutura de pastas, patterns e padrões de código.

---

## Visão Geral do Fluxo

```
💡 IDEIA
   │
   ▼
[PRÉ-DEV] ─── superpowers:brainstorming ──→ ai-project-brainstorm
   │                                         (PRD completo + personas + roadmap)
   │
   ▼
[PLANO] ──── superpowers:writing-plans ──→ Plano aprovado pelo usuário
   │
   │  ← GATE: usuário aprova o plano antes de continuar
   │
   ▼
[EXECUÇÃO] ─ IntelliX Plugin ─────────────────────────────────────────
   │
   ├─ [00] project-kickoff      → scaffolding + estrutura canônica
   ├─ [00b] code-audit          → (apenas projetos existentes)
   ├─ [01] architecture         → schema DB + rotas + types + repository/service
   ├─ [02] frontend-design      → vibestack → ui-ux-pro-max → frontend-design-pro
   │                              → ckm-ui-styling → web-design-guidelines
   ├─ [03] agent-creation       → intellix-agent-creation (se houver agentes)
   ├─ [04] dev-standards        → TypeScript + naming + patterns
   ├─ [05] integration          → APIs externas + WhatsApp + n8n
   ├─ [06] security-observability → OWASP + rate limiting + logs
   ├─ [07] test-e2e             → SKILL_TestE2E (smoke → stress)
   ├─ [08] deploy               → Vercel + Cloudflare DNS
   └─ [09] handoff              → README + documentação final
        │
        ▼
     ✅ SISTEMA EM PRODUÇÃO
```

---

## ETAPA 1 — Pré-Desenvolvimento (Brainstorm + PRD)

### Quando a ideia chega

**Passo 1.1 — Brainstorm e validação:**

```
Skill("superpowers:brainstorming")
```

Valida a ideia, explora ângulos, identifica riscos e oportunidades antes de qualquer código.
**NÃO pule esta etapa.** Muitos problemas de arquitetura são evitados aqui.

**Passo 1.2 — PRD completo (se o projeto for significativo):**

```
Skill("ai-project-brainstorm")
```

Gera documento estruturado com:
- Visão do produto e problema que resolve
- Personas e casos de uso
- Features por prioridade (MVP vs V2)
- Stack recomendada e arquitetura de alto nível
- Banco de dados: tabelas e relacionamentos iniciais
- Roadmap de implementação em fases
- Prompt de geração para IA (para uso no `/spec`)

**Gate 1:** Apresente o PRD ao usuário. Aguarde aprovação antes de continuar.

**Passo 1.3 — Stress-test do PRD (opcional mas recomendado):**

```
Skill("grill-me")
```

Questiona implacavelmente cada decisão do PRD — features, arquitetura, personas, roadmap — até que não restem ambiguidades. Use antes de commitar o plano ao time.

- Percorre cada galho da árvore de decisão
- Para cada pergunta, oferece a resposta recomendada
- Resolve dependências entre decisões na sequência certa

> Use quando o projeto é alto risco, tem muitas incógnitas, ou quando o usuário quer "grill me on this plan".

**Alternativa rápida — PRD direto do contexto:**

```
Skill("to-prd")
```

Quando já há contexto suficiente na conversa e no codebase, `to-prd` sintetiza um PRD completo sem entrevista. Use no lugar de `ai-project-brainstorm` quando o escopo já está claro.

| Skill | Quando usar |
|---|---|
| `superpowers:brainstorming` | Ideia bruta — explorar ângulos antes de qualquer estrutura |
| `ai-project-brainstorm` | PRD completo guiado por perguntas interativas |
| `to-prd` | PRD rápido quando o contexto já está claro na conversa |
| `grill-me` | Stress-test de PRD/plano aprovado antes de commitar |

---

## ETAPA 2 — Planejamento

### Transformar PRD em plano executável

```
Skill("superpowers:writing-plans")
```

Transforma o PRD aprovado em um plano de implementação estruturado com:
- Lista de tarefas ordenadas e dependências
- Estimativas de complexidade por feature
- Arquivos que serão criados/modificados
- Riscos técnicos identificados
- Critérios de sucesso por fase

**Gate 2:** Apresente o plano ao usuário. Aguarde aprovação explícita antes de executar.

---

## ETAPA 3 — Execução com IntelliX Plugin

A execução segue o fluxo de fases do plugin. **Cada fase tem um gate de aprovação.**

---

### FASE 00 — Project Kickoff

```
Skill("intellix:project-kickoff")
```

**Para projetos novos:**
- 3 perguntas diagnóstico (tipo de sistema, integrações, agentes)
- Definir stack e escopo
- Criar estrutura de pastas canônica (ver MASTER-ARCHITECTURE.md §3)
- Inicializar `AGENTS.md` (contexto neutro para qualquer agente), `CLAUDE.md` (Claude-específico), `.intellix-phase`, `.claude/settings.json`

> **`AGENTS.md`:** arquivo vendor-neutral lido por Claude Code, Cursor, Codex, Copilot, Aider e 20+ outros agentes. Contém comandos de setup/test, convenções de código e estrutura de pastas. Diferente do `CLAUDE.md` que contém regras IntelliX-específicas.

**Para projetos existentes (código já existe):**
```
Skill("intellix:code-audit")
```
Auditoria completa antes de qualquer refatoração.

---

### FASE 01 — Architecture

```
Skill("intellix:architecture")
```

Antes de qualquer código:
- Schema Supabase com RLS obrigatório
- Rotas Next.js App Router
- Tipos TypeScript centralizados em `src/types/`
- Repository + Service pattern (ver [`references/data-layer.md`](../references/data-layer.md))
- API Response padronizado RFC 7807
- RBAC (se SaaS multi-tenant)

**Skills complementares automáticas:**
- `supabase-postgres-best-practices` → ao escrever queries e schema
- `vercel-react-best-practices` → ao definir Server vs Client Components

---

### FASE 02 — Frontend Design

> **Executar apenas se o projeto tem interface de usuário.**

```
Skill("intellix:frontend-design")
```

Sequência de **9 steps** em ordem obrigatória (6 skills principais + auditoria 3 camadas):

```
1. vibestack-architect       → estrutura de componentes e roteamento visual
2. ui-ux-pro-max             → design system conceitual: cores, tipografia, estilo visual
2b. design-system-patterns   → tokens CSS/Tailwind em código: tailwind.config.ts + globals.css
3. frontend-design-pro       → implementação UI com qualidade $50k+ agency
3b. impeccable               → polish, animações avançadas e craft anti-AI-slop (23 comandos)
4. ckm-ui-styling            → Shadcn/UI, loading/error states, consistência
5a. web-design-guidelines    → guidelines HIG/Material, hierarquia, micro-interações
5b. accessibility            → WCAG 2.1 AA/AAA: contraste, aria, teclado, screen readers
5c. seo                      → meta tags, schema.org, Core Web Vitals, sitemap
```

Entregável obrigatório: `docs/design-system.md` + `PRODUCT.md` (para impeccable).

---

### FASE 03 — Agent Creation

> **Executar apenas se o sistema tem agentes, bots ou automação com IA.**

```
Skill("intellix:agent-creation")
→ delega para: Skill("intellix-agent-creation")
```

A skill unificada pergunta a plataforma e executa o módulo correto:

| Plataforma | Módulo | Resultado |
|---|---|---|
| GPT Maker | Módulo 1 | Agente configurado via MCP diretamente |
| n8n | Módulo 2 | Workflow completo de agente no n8n |
| IntelliX Blueprint | Módulo 3 | Blueprint v2 JSON + 20 seções |

---

### FASE 04 — Dev Standards

```
Skill("intellix:dev-standards")
```

**Passo 0 obrigatório antes de qualquer código:**
```
Skill("karpathy-guidelines")  → Think Before Coding | Simplicity First | Surgical Changes | Goal-Driven Execution
```

Referência contínua durante todo o desenvolvimento:
- TypeScript strict: zero `any`, zero `@ts-ignore`
- Naming conventions por tipo de artefato
- Estrutura obrigatória de componentes
- Server Actions vs Route Handlers
- Validação com Zod em todas as entradas

---

### FASE 04b — Implementação com Epic Workflow + Review em Dois Estágios

**Antes do `/spec` — spec de produto (opcional, features complexas):**

```
Skill("write-product-spec")  → PRODUCT.md: comportamento do usuário, invariantes, edge cases
```

Use quando a feature é substancial ou comportamentalmente ambígua. O PRODUCT.md descreve o que o usuário vê e faz, sem detalhes de implementação — contexto essencial para o agente implementar sem regressões.

Para cada feature/módulo, execute os 4 comandos:

```
/spec  → SPEC.md: pages + components + behaviors (aguarda aprovação)
/break → issues/ atômicas ordenadas (UI protótipos → behaviors → integrações)
/plan  → 7 seções por issue (aguarda aprovação)
/execute → ciclo de 3 estágios por arquivo (ver abaixo)
```

**Alternativa para `/break` — quebrar em issues via skill:**

```
Skill("to-issues")  → converte plano/PRD em issues independentes usando tracer bullets verticais
```

**Ciclo `/execute` por arquivo (3 estágios obrigatórios):**

```
Para cada arquivo da issue:
  1. Agente tipado implementa (component-writer, action-writer, etc.)
       ↓ implementa → testa → self-review → reporta
  2. Spec-reviewer subagent — verifica Happy Path + Edge + Error Cases
       ↓ ✅ aprovado ou ❌ gaps → agente corrige → repete
  3. Code-quality-reviewer subagent — verifica TypeScript strict, Zod, naming
       ↓ ✅ aprovado ou ❌ Critical/Important → agente corrige → repete
  ✅ Arquivo concluído → próximo arquivo
```

**Agentes por tipo de arquivo (Estágio 1):**
- `component-writer.md` → componentes React + modais (`.tsx`)
- `action-writer.md` → Server Actions (`actions.ts`)
- `hook-writer.md` → custom hooks (`use-*.ts`)
- `route-writer.md` → Route Handlers (`route.ts`)
- `integration-writer.md` → SDKs externos / webhooks
- `model-writer.md` → tipos TypeScript + SQL migrations
- `test-writer.md` → testes (`.test.ts`)

> **Prompts dos reviewers e ciclo completo:** `references/four-commands.md §/execute`

---

### FASE 05 — Integration

```
Skill("intellix:integration")
```

Receitas prontas para:
- Anthropic SDK / OpenAI SDK (nativo preferido)
- Evolution API / WhatsApp
- n8n (orquestração opcional para fluxos complexos)
- Supabase Realtime (websockets)
- Resend (email)

**Skills complementares por integração:**
- n8n: `n8n-workflow-patterns` + `n8n-node-configuration`
- Código n8n JS: `n8n-code-javascript`
- Código n8n Python: `n8n-code-python`
- Validação n8n: `n8n-validation-expert`

---

### FASE 06 — Security, LGPD & Observability

```
Skill("intellix:security-observability")   ← segurança técnica OWASP
Skill("lgpd-compliance")                   ← SEMPRE que houver dados pessoais
```

Executar **em paralelo**. São complementares:

**`security-observability`** — segurança técnica:
- Auth no servidor, rate limiting, RLS, headers CSP/HSTS
- Logs sem PII, sem stack traces expostos ao cliente

**`lgpd-compliance`** — proteção de dados pessoais (Lei 13.709/2018):
- Bases legais documentadas por tabela/operação
- Tabelas: `consent_records`, `titular_requests`, `data_audit_log`
- Consentimento granular por finalidade com rastreio
- 9 direitos dos titulares implementados (prazo: 15 dias)
- Criptografia AES-256-GCM para dados sensíveis (CPF, saúde)
- Pseudonimização em logs e analytics
- Cookie banner LGPD-compliant
- Política de retenção e descarte automático
- Plano de resposta a incidentes (notificação ANPD em 72h)
- Checklist ANPD 48 pontos executado
- Multa máxima evitada: 2% faturamento / R$ 50M por infração

---

### FASE 07 — Test E2E

```
Skill("intellix:test-e2e")
→ executa: Skill("vibecode-e2e-tester") [SKILL_TestE2E]
```

Bateria completa:
1. **Smoke tests** — funcionalidades críticas básicas
2. **Functional tests** — happy path, edge cases, error cases por feature
3. **Security tests** — auth bypass, SQL injection, XSS
4. **Performance tests** — Lighthouse, Core Web Vitals
5. **Stress tests** — Locust para carga

**Gate final:** 100% dos testes passando antes do deploy.

---

### FASE 08 — Deploy

```
Skill("intellix:deploy")
```

Checklist Vercel + Cloudflare:
- Variáveis de ambiente configuradas
- DNS apontado corretamente
- SSL "Full (strict)" no Cloudflare
- Health check pós-deploy
- Monitoramento ativo

---

### FASE 09 — Handoff

```
Skill("intellix:handoff")
```

Documentação final:
- `README.md` com setup local completo
- ADRs (Architecture Decision Records)
- Runbook de operações
- Acesso ao cliente configurado
- `.intellix-phase` = `done`

---

## Regras de Ouro do Workflow

1. **Nunca pule fases** — cada fase tem um entregável que a próxima fase depende
2. **Sempre espere aprovação** nos gates antes de avançar
3. **Arquitetura antes de código** — Fases 00→02 antes de escrever qualquer lógica
4. **Design system antes de UI** — Fase 02 completa antes de qualquer componente
5. **Testes antes de deploy** — Fase 07 com 100% passando é pré-requisito do Fase 08
6. **Um problema por vez** — `/break` garante que cada sessão tem foco único
7. **Referência sempre** — consultar `MASTER-ARCHITECTURE.md` antes de qualquer `/plan`

---

## Decisões Rápidas por Tipo de Projeto

```
Landing page simples?
  → Fases: 00 → 01(rotas apenas) → 02 → 08
  → Pular: 03, 04b behaviors, 05, 06 completo

SaaS completo com auth?
  → Fluxo completo: 00 → 01 → 02 → 04 → 04b → 05 → 06 → 07 → 08 → 09

CRM/Dashboard com agentes?
  → Fluxo completo + Fase 03 após Fase 01

API-only sem UI?
  → Fases: 00 → 01 → 04 → 04b → 05 → 06 → 07 → 08
  → Pular: 02 (sem frontend)

Projeto existente (refatorar)?
  → Começar com: 00b (code-audit) → plano de refatoração → fases conforme gaps
```

---

## Skills Externas Integradas ao Workflow

| Momento | Skill / Ferramenta | Por quê |
|---|---|---|
| Concepção | `superpowers:brainstorming` | Valida ideia antes de investir tempo |
| PRD | `ai-project-brainstorm` | Documento completo com personas e roadmap |
| Planejamento | `superpowers:writing-plans` | Plano executável com tasks e dependências |
| **Antes de qualquer código** | **`karpathy-guidelines`** | **Think Before Coding — evita over-engineering e mudanças cirúrgicas** |
| **API de qualquer lib** | **Context7 MCP** (`resolve-library-id` + `query-docs`) | **Docs atuais de Next.js/Supabase/Tailwind — nunca assuma a API** |
| Schema DB | `supabase-postgres-best-practices` | Índices, RLS, performance desde o início |
| LGPD + dados pessoais | `lgpd-compliance` | 10 bases legais, 9 direitos, Privacy by Design, ANPD |
| UI estrutura | `vibestack-architect` | Arquitetura de componentes antes de pixel |
| Design system conceitual | `ui-ux-pro-max` | 50+ estilos, 161 paletas, 57 font pairings |
| **Design system em código** | **`design-system-patterns`** | **Tokens CSS + Tailwind theme + dark mode infra** |
| Implementação UI | `frontend-design-pro` | Qualidade $50k agency, fotos reais, signature details |
| **Polish + animações** | **`impeccable`** | **Anti-AI-slop: 23 comandos craft, motion design, colorização** |
| Componentes | `ckm-ui-styling` | Shadcn/UI, loading/error states, consistência |
| Revisão UI | `web-design-guidelines` | Guidelines HIG/Material, hierarquia, micro-interações |
| **Acessibilidade** | **`accessibility`** | **WCAG 2.1 AA/AAA, aria, contraste, teclado, screen readers** |
| **SEO técnico** | **`seo`** | **Meta tags, schema.org, Core Web Vitals, sitemap** |
| Performance React | `vercel-react-best-practices` | Server/Client components, bundle, caching |
| Agentes | `intellix-agent-creation` | GPT Maker + n8n + Blueprint unificado |
| n8n patterns | `n8n-workflow-patterns` | Padrões comprovados de automação |
| Testes | `SKILL_TestE2E` | Smoke → stress → security, cobertura total |
| **Debug de testes no browser** | **`browser-testing-with-devtools`** | **DevTools: breakpoints, network panel, console — diagnóstico visual de falhas E2E** |
| Debug | `superpowers:systematic-debugging` | Metodologia antes de tentar correções |
| Code review | `superpowers:requesting-code-review` | Antes de merge ou feature completa |
| **Contexto CLAUDE.md + AGENTS.md** | **`context-engineering`** | **Validar qualidade do contexto entregue aos agentes — evita context starvation e flooding** |
| **API pública / webhooks / contratos** | **`api-and-interface-design`** | **Contract-first, versionamento, branded IDs — apenas quando há API consumida externamente** |
| **Git workflow + commits atômicos** | **`git-workflow-and-versioning`** | **Trunk-based dev, save-point pattern, worktrees para agentes paralelos, pre-commit gates** |
| **Decisões incertas em /plan** | **`doubt-driven-development`** | **Mapeia dúvidas técnicas antes de implementar — evita retrabalho por assunções erradas** |
| **Pipeline CI/CD (uma vez por projeto)** | **`ci-cd-and-automation`** | **GitHub Actions, branch protection, Dependabot, preview deploys automáticos por PR** |
| **Go-live com staged rollout** | **`shipping-and-launch`** | **5%→25%→50%→100%, feature flags, monitoramento 1ª hora, rollback plan documentado** |
| **Tech debt / migração de legado** | **`deprecation-and-migration`** | **Strangler pattern, zombie code, atualização de deps com breaking changes — projetos existentes** |

---

## Troubleshooting — Claude repetindo o mesmo erro em loop

**Sintoma:** O Claude continua cometendo o mesmo erro ou tomando a mesma decisão errada mesmo após correção.

**Causa:** A memória persistente do projeto (`MEMORY.md` + arquivos em `memory/`) contém uma entrada incorreta ou desatualizada que é reinjetada no contexto a cada sessão.

**Solução:**

```
1. Digite /memory no terminal do Claude Code
2. O painel de memórias do projeto abre
3. Localize a entrada incorreta (busque pelo erro ou comportamento problemático)
4. Edite ou delete a entrada manualmente
5. Continue — o Claude não repetirá mais o comportamento errado
```

**Alternativa via arquivo:** edite diretamente `~/.claude/projects/<projeto>/memory/MEMORY.md` e o arquivo de memória referenciado.

> Esta é a causa mais comum de "o Claude não aprende" — não é o modelo, é uma memória errada sendo injetada silenciosamente.
