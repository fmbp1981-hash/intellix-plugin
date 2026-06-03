# IntelliX Master Architecture — Fonte Única de Verdade

> **Este é o documento central do ecossistema IntelliX.**
> Todo projeto, toda skill, todo agente deve referenciar e obedecer este documento.
> Em caso de conflito entre qualquer skill e este documento, **este documento vence**.

---

## 0. Por Que Este Workflow Existe — Os 5 Problemas que Resolve

| Problema | Causa | Solução | Comando |
|---|---|---|---|
| **IA "engasga"** | Contexto da janela lotado com projetos grandes | Quebrar em tarefas menores — cada issue cabe em uma sessão | `/spec` + `/break` |
| **Código bagunçado** | IA duplica código sem pesquisar o que já existe | Pesquisar imports e padrões existentes antes de implementar | `/plan` |
| **IA não obedece** | Claude modifica arquivos além do escopo | Listar exatamente quais arquivos criar/modificar — IA só mexe no que você pediu | `/execute` (com lista do `/plan`) |
| **Arruma uma coisa, quebra outra** | Behaviors acoplados na mesma pasta | Cada comportamento vive em sua própria pasta — editar um não afeta o outro | `architecture.md` + agents + testes |
| **Gafes de segurança** | Lógica e chaves no frontend | Thin Client, Fat Server — frontend só captura intenções e reage a resultados do backend. Jamais colocar chaves no frontend | `architecture.md` + agents + testes |

---

## 0b. Princípios Invioláveis

Estas regras se aplicam a 100% das decisões. Nunca negocie com elas.

| # | Princípio | Regra |
|---|-----------|-------|
| 1 | **Thin Client, Fat Server** | Frontend captura intenção e exibe resultado. Sem lógica de negócio, sem secrets, sem acesso direto ao banco |
| 2 | **Isolamento de Comportamentos** | Cada behavior vive em sua própria pasta. Comunicação entre behaviors via `lib/[domain]/contracts.ts` |
| 3 | **Não-Surpresa** | Claude nunca cria arquivos fora da lista aprovada no `/plan`. A IA só mexe nos arquivos que você pede |
| 4 | **TypeScript Strict Zero-Any** | `any` = nunca. `@ts-ignore` = nunca. `@ts-expect-error` = apenas incompatibilidade de lib de terceiro, com comentário obrigatório. `@ts-nocheck` = apenas em arquivo legado com `// @ts-nocheck — TODO: remover — issue #N`. Ver hierarquia completa em `skills/dev-standards/SKILL.md §TypeScript` |
| 5 | **RLS Sempre** | Toda tabela Supabase tem Row Level Security. Sem exceção |
| 6 | **Aprovação Explícita** | Nenhum step avança sem confirmação do usuário. Apresente, aguarde, só então execute |
| 7 | **Arquitetura > Velocidade** | Em conflito entre velocidade e arquitetura limpa, a arquitetura sempre vence |
| 8 | **Multi-tenant por Padrão** | Toda query que acessa dados de usuário DEVE ter `.eq("user_id", userId)` explícito — mesmo com RLS ativo. RLS é a segunda linha de defesa, não a única |
| 9 | **Zero Credencial no Código** | Emails de admin, IDs de tenant, secrets e URLs de ambiente nunca em código-fonte. Sempre `process.env.*`. Se está em `.ts`, está errado |
| 10 | **Singleton de DB Client** | Clientes de banco de dados são criados uma vez no módulo, nunca por chamada. `createClient()` dentro de uma função = vazamento de conexão em serverless |
| 11 | **IDs Nunca por COUNT** | Gerar IDs/refs com `COUNT(*) + 1` é race condition garantida. Usar UUID, sequências PostgreSQL ou timestamp+random |

---

## 0c. Gerenciamento de Context Window

**Regra:** Mantenha o context window entre **40% e 50%**. Acima de 70%, a qualidade da IA despenca — não por "cansaço", mas porque ela literalmente perde acesso ao contexto anterior.

| Sintoma | Diagnóstico | Ação imediata |
|---------|-------------|---------------|
| IA esquece arquivo criado há 5 mensagens | Context >70% | `/clear` + retomar com plano aprovado |
| IA duplica componente existente | Não buscou codebase no `/plan` | Forçar Frente 1 (grep antes de planejar) |
| IA modifica arquivo fora do escopo | "Files to NOT Touch" ausente na issue | Preencher seção obrigatória no `/break` |
| IA contradiz decisão anterior | Decisão não persistida | Registrar em `references/architecture.md` do projeto |

**Ações obrigatórias entre fases:**
- Após `/plan` aprovado → `/clear` antes de `/execute`
- Após pesquisa de docs/repos → `/clear` antes de escrever código
- Context window > 60% → parar, resumir em `prd.md`, limpar, retomar

> **Referência completa:** [`references/context-window.md`](references/context-window.md)

---

## 1. Workflow Completo de Desenvolvimento

### Visão Macro — Fases do Projeto

```
[FASE 00] /projeto novo    →  zero-touch: references/ + agentes/ + estrutura SDD + npm install
[FASE 00] Kickoff manual   →  (projetos existentes) diagnóstico, tipo, stack
[FASE 00b] Code Audit      →  (projetos existentes) auditoria antes de refatorar
[FASE 01] Architecture     →  schema DB, rotas, tipos, repository/service pattern
[FASE 02] Frontend Design  →  design system, tokens, componentes base, UI kit
[FASE 03] Dev Standards    →  TypeScript, naming, estrutura de componentes
[FASE 04] Implementation   →  /spec → /break → /plan → /execute (ver seção 2)
[FASE 05] Integration      →  APIs externas, WhatsApp, n8n, SDKs de IA
[FASE 06] Security         →  auditoria OWASP, rate limiting, observabilidade
[FASE 07] Test E2E         →  Playwright/Pytest, smoke → stress
[FASE 08] Deploy           →  Vercel + Cloudflare DNS checklist
[FASE 09] Handoff          →  README técnico, documentação final
```

**Arquivo de controle:** `.intellix-phase` na raiz (valores: `init|arch|dev|test|deploy|done`)

> **Projetos novos:** use `/projeto novo` (`intellix:projeto-novo`) para automação zero-touch.
> Entrega estrutura pronta para `/spec` em ~2 minutos sem setup manual.
> **Skill:** [`skills/projeto-novo/SKILL.md`](skills/projeto-novo/SKILL.md)
> **Templates:** [`intellix-templates/`](intellix-templates/)

---

## 2. Workflow de Implementação — Os 4 Comandos

Para cada feature/módulo: `/spec` → `/break` → `/plan` → `/execute`. Nunca pule.

| Comando | Quando | O que faz |
|---------|--------|-----------|
| `/spec` | Início de feature | Cria/atualiza `SPEC.md` — O QUÊ, não o COMO |
| `/break` | Após SPEC aprovado | Cria `issues/` com behaviors atômicos ordenados |
| `/plan` | Antes de cada issue | Pesquisa codebase, preenche 7 seções, aguarda aprovação |
| `/execute` | Após plan aprovado | Implementa APENAS os arquivos do plano, roda checklist |

> **Referência completa (templates, exemplos, regras):** [`references/four-commands.md`](references/four-commands.md)

---

## 2b. Anti-patterns Críticos

Os 5 erros que destroem SaaS em produção: data leak multi-tenant, credencial hardcoded,
race condition em IDs, DB client por chamada, e sistemas coexistindo sem migração completa.

> **Referência completa com exemplos de código:** [`references/anti-patterns.md`](references/anti-patterns.md)

---

## 3. Estrutura de Pastas Canônica

Estrutura padrão para todo projeto IntelliX: App Router, behaviors isolados, camadas repository/service, referências em `references/`, supabase migrations, testes separados por camada.

> **Estrutura completa com comentários:** [`references/data-layer.md`](references/data-layer.md) — seção §7 para schema SQL e `src/repositories/` + `src/services/`

```
projeto/
├── src/app/           # Next.js 15 App Router — rotas, pages, layouts, api/
├── src/components/    # ui/ (Shadcn) | layout/ | shared/
├── src/lib/           # supabase/ | ai/ | [domain]/contracts.ts | api-response.ts
├── src/repositories/  # Data Access Layer — apenas Supabase
├── src/services/      # Business Logic — usa repositories
├── src/hooks/         # use-*.ts
├── src/types/         # index.ts — fonte única de verdade
├── src/validations/   # Zod schemas
├── supabase/migrations/   # SQL versionado
├── tests/unit/ integration/ e2e/
├── .intellix-phase    # init|arch|dev|test|deploy|done
├── SPEC.md            # Especificação viva
└── MASTER-ARCHITECTURE.md
```

---

## 4. Agentes Especializados por Tipo de Arquivo

Durante o `/execute`, cada arquivo passa por **3 estágios**: agente tipado → spec review → quality review.
Os agentes vivem em `.claude/agents/`. Os reviewers são subagentes despachados inline.

> **Referência completa do ciclo de execução:** [`references/four-commands.md §/execute`](references/four-commands.md)

### Tabela Agente → Tipo de Arquivo (Estágio 1)

| Tipo de arquivo | Agente em `.claude/agents/` | Contexto obrigatório |
|---|---|---|
| Componente de UI (`.tsx`) | `component-writer.md` | architecture.md + DESIGN.md |
| Server Action (`actions.ts`) | `action-writer.md` | architecture.md |
| Hook customizado (`use-*.ts`) | `hook-writer.md` | architecture.md |
| Route Handler (`route.ts`) | `route-writer.md` | architecture.md + api-standards.md |
| Modal / Dialog (`.tsx`) | `modal-writer.md` | architecture.md + DESIGN.md |
| Integração externa (SDK, webhook) | `integration-writer.md` | architecture.md |
| Schema / Tipos (`.sql`, `types.ts`) | `model-writer.md` | architecture.md + data-layer.md |
| Testes de behavior (`.test.ts`) | `test-writer.md` | architecture.md + spec da issue |

### Estágio 2 — Spec Review (subagente)

Após o agente implementar: despachar subagente spec-reviewer com a spec da issue + diff.
Verifica conformidade com Happy Path, Edge Cases e Error Cases.
Bloqueia o Estágio 3 até ✅. Loop: agente corrige → revisor re-revisa.

### Estágio 3 — Quality Review (subagente)

Após spec aprovada: despachar subagente code-quality-reviewer com o diff.
Verifica: TypeScript strict, zero `any`, Zod em inputs, forbidden_paths, naming IntelliX.
Critical/Important bloqueiam → agente corrige → revisor re-revisa. Minor → nota, não bloqueia.

> **Prompts padrão dos reviewers:** [`references/four-commands.md §Prompt padrão`](references/four-commands.md)

### Skills que os Agentes Usam

| Skill | O que faz |
|---|---|
| `write-component` | Gera componentes React seguindo estrutura obrigatória |
| `write-action` | Gera Server Actions com validação Zod + auth check |
| `write-hook` | Gera custom hooks com TanStack Query ou estado local |
| `write-route` | Gera Route Handlers com apiResponse padronizado |
| `write-model` | Gera tipos TypeScript + Zod schemas + SQL migration |
| `write-integration` | Gera integrações com SDKs externos (Anthropic, Evolution, etc.) |
| `write-behavior-test` | Gera testes de behavior (happy path + edge + error) |
| `write-unit-test` | Gera testes unitários para funções puras e utils |
| `write-issue` | Gera template de issue com as 7 seções obrigatórias |
| `frontend-design` | Aplica design system, tokens e padrões visuais |
| `epic-cli` | Comandos do workflow (/spec, /break, /plan, /execute) |

### Estrutura `.claude/` por Projeto

```
.claude/
├── CLAUDE.md                 # Contexto do projeto
├── settings.json             # Plugin IntelliX habilitado
└── agents/
    ├── action-writer.md      # Server Actions
    ├── component-writer.md   # Componentes React
    ├── hook-writer.md        # Custom hooks
    ├── integration-writer.md # SDKs externos
    ├── modal-writer.md       # Modais e dialogs
    ├── route-writer.md       # Route Handlers
    └── test-writer.md        # Testes
```

---

## 5–12. Referências Técnicas

| Tópico | Quando consultar | Arquivo |
|--------|-----------------|---------|
| Repository pattern, Service layer, Schema SQL, Behavior isolation | Ao criar acesso a dados | [`references/data-layer.md`](references/data-layer.md) |
| API Response RFC 7807, Route Handler padrão, Paginação cursor-based | Ao criar Route Handlers | [`references/api-standards.md`](references/api-standards.md) |
| TypeScript strict, Naming conventions, Estrutura de componentes | Ao criar `.tsx` ou hooks | [`references/frontend-patterns.md`](references/frontend-patterns.md) |

---

## 13–17. Referências Operacionais

| Tópico | Quando consultar | Arquivo |
|--------|-----------------|---------|
| Segurança: checklist BÁSICO/COMPLETO, headers CSP, RBAC | Ao criar rotas, middleware, autenticação | [`references/security-rules.md`](references/security-rules.md) |
| Testes por camada, variáveis de ambiente, CLAUDE.md template, deploy Vercel+Cloudflare | Ao configurar projeto ou preparar deploy | [`references/operations.md`](references/operations.md) |

---

## 18. Índice de Referências

Dois conjuntos de referências disponíveis: arquivos do **plugin IntelliX** (disponíveis em qualquer projeto) e arquivos **por projeto** (criados durante o kickoff de cada projeto).

### Referências do Plugin IntelliX

| Arquivo | O que contém | Quando consultar |
|---------|-------------|-----------------|
| [`skills/lgpd-compliance/SKILL.md`](skills/lgpd-compliance/SKILL.md) | Compliance LGPD: bases legais, direitos dos titulares, schema de tabelas, Privacy by Design, incidentes | Ao implementar qualquer feature com dados pessoais de brasileiros |
| [`skills/projeto-novo/SKILL.md`](skills/projeto-novo/SKILL.md) | Automação zero-touch: /projeto novo — 9 passos de setup com templates e agentes | Ao iniciar projeto novo do zero |
| [`intellix-templates/`](intellix-templates/) | Boilerplate com references/, agents-template/, version.json | Consultado automaticamente pelo /projeto novo |
| [`references/four-commands.md`](references/four-commands.md) | Templates completos de /spec, /break, /plan, /execute + Checklist Fatal | Ao executar qualquer um dos 4 comandos |
| [`references/context-window.md`](references/context-window.md) | Gerenciamento de context window: sintomas, diagnóstico, práticas operacionais | Ao iniciar `/execute` ou ao notar comportamento estranho da IA |
| [`references/anti-patterns.md`](references/anti-patterns.md) | 5 anti-patterns críticos de SaaS + checklist de armadilhas | Antes de escrever qualquer acesso a dados ou auth |
| [`references/data-layer.md`](references/data-layer.md) | Repository + Service pattern, Behavior isolation, Schema SQL + RBAC | Ao criar repositories, services, schemas ou behaviors |
| [`references/api-standards.md`](references/api-standards.md) | apiResponse RFC 7807, Route Handler padrão, Paginação cursor | Ao criar Route Handlers ou APIs |
| [`references/frontend-patterns.md`](references/frontend-patterns.md) | TypeScript strict, Naming conventions, Estrutura de componentes | Ao criar componentes `.tsx` ou hooks |
| [`references/security-rules.md`](references/security-rules.md) | Checklist BÁSICO/COMPLETO, headers CSP/HSTS, Regras DevSecOps 4-9, 5 Regras de Ouro | Ao implementar rotas, middleware, autenticação ou qualquer LLM |
| [`references/operations.md`](references/operations.md) | Estratégia de testes, variáveis de ambiente, CLAUDE.md template, deploy | Ao configurar projeto ou preparar deploy |

### Referências por Projeto

Criadas durante o kickoff de cada projeto em `references/` na raiz do projeto:

| Arquivo | Conteúdo | Quando ler |
|---------|----------|-----------|
| `references/architecture.md` | Regras de isolamento, naming, estrutura específica do projeto | Sempre, antes de `/plan` |
| `references/DESIGN.md` | Design tokens, paletas, tipografia, componentes base | Antes de qualquer componente UI |
| `references/specification.md` | Template e exemplos de spec bem escritas | Ao escrever um `/spec` |
| `references/workflow.md` | Resumo compacto do workflow para o time | Onboarding de novos devs |

> **Regra:** Sempre consulte `references/architecture.md` e `references/DESIGN.md` do projeto antes de implementar qualquer issue — são a memória de longo prazo do projeto.

---

## 20. Referência Completa de Skills — Workflow IntelliX

### Fluxo Principal (ordem obrigatória)

| # | Etapa | Skill | Tipo |
|---|-------|-------|------|
| 1 | Brainstorm e validação da ideia | `superpowers:brainstorming` | Externa |
| 2 | PRD completo (personas, roadmap, stack) | `ai-project-brainstorm` | Externa |
| 3 | Plano de implementação executável | `superpowers:writing-plans` | Externa |
| 4 | **GATE: aprovação do plano** | — | — |
| 5 | **Setup zero-touch (projetos novos)** | `intellix:projeto-novo` | Plugin |
| 5m | Kickoff manual (projetos existentes) | `intellix:project-kickoff` | Plugin |
| 5b | Auditoria (projetos existentes) | `intellix:code-audit` | Plugin |
| 6 | Schema DB + routes + repository/service | `intellix:architecture` | Plugin |
| 7 | UI: estrutura → design → implementação → audit | `intellix:frontend-design` | Plugin (5 skills) |
| 8 | Agentes IA (GPT Maker / n8n / Blueprint) | `intellix:agent-creation` | Plugin → Externa |
| 9 | Padrões TypeScript + naming + components | `intellix:dev-standards` | Plugin |
| 10 | /spec → /break → /plan → /execute | `skill-epic-workflow` | Externa |
| 11 | APIs externas + WhatsApp + n8n | `intellix:integration` | Plugin |
| 12 | OWASP + rate limit + observabilidade + LLM/Agentes | `intellix:security-observability` | Plugin |
| 12b | LGPD + Privacy by Design (dados pessoais) | `lgpd-compliance` | Plugin |
| 13 | Testes E2E smoke → stress | `intellix:test-e2e` | Plugin → Externa |
| 14 | Deploy Vercel + Cloudflare | `intellix:deploy` | Plugin |
| 15 | README + ADRs + documentação final | `intellix:handoff` | Plugin |

### Skills Externas por Fase (invocadas pelos módulos do plugin)

| Fase Plugin | Skills externas invocadas | Função |
|---|---|---|
| 02 Frontend (passo 1) | `vibestack-architect` | Arquitetura de componentes e roteamento visual |
| 02 Frontend (passo 2) | `ui-ux-pro-max` | Design system: 50+ estilos, 161 paletas, 57 fontes |
| 02 Frontend (passo 3) | `frontend-design-pro` | Implementação UI qualidade $50k+ |
| 02 Frontend (passo 4) | `ckm-ui-styling` | Shadcn/UI, acessibilidade, loading/error states |
| 02 Frontend (passo 5) | `web-design-guidelines` | Auditoria WCAG, UX, responsividade |
| 03 Agentes | `intellix-agent-creation` | GPT Maker + n8n + IntelliX Blueprint unificado |
| 05 Integrações n8n | `n8n-workflow-patterns` | Padrões de workflow comprovados |
| 05 Integrações n8n | `n8n-node-configuration` | Configuração de nodes por operação |
| 05 Integrações n8n | `n8n-code-javascript` | JavaScript em Code nodes |
| 05 Integrações n8n | `n8n-validation-expert` | Diagnóstico de erros de validação |
| 07 Testes | `SKILL_TestE2E` (vibecode-e2e-tester) | Bateria completa smoke → stress |
| Qualquer | `supabase-postgres-best-practices` | Queries, índices, RLS, performance |
| Qualquer | `vercel-react-best-practices` | Server/Client components, caching, bundle |
| Dados pessoais BR | `lgpd-compliance` | LGPD completa: bases legais, direitos do titular, Privacy by Design, ANPD 48pts |

### Skills de Suporte (quando necessário)

| Situação | Skill |
|---|---|
| Encontrou um bug | `superpowers:systematic-debugging` |
| Feature concluída, revisar | `superpowers:requesting-code-review` |
| Recebeu feedback de review | `superpowers:receiving-code-review` |
| Execução paralela de tasks | `superpowers:dispatching-parallel-agents` |
| Chat omnichannel com IA + humano | `intellix:live-chat` |
| Criar/melhorar uma skill | `skill-creator` ou `skill-architect` |
| Design de banners/social | `ckm-banner-design` |
| Apresentações/slides | `ckm-slides` |
| Design system de tokens | `ckm-design-system` |
