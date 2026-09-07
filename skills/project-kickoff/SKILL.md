---
name: project-kickoff
description: >
  Use esta skill SEMPRE que o usuário mencionar: criar um novo projeto, iniciar
  um sistema, novo cliente, scaffolding, estrutura inicial, "quero criar um...",
  "preciso de um sistema...", ou qualquer início de desenvolvimento.
  Esta é a PRIMEIRA skill do fluxo IntelliX — nunca pule para implementação
  sem executá-la. Também ativa quando o usuário quer entender a fase atual
  de um projeto existente.
---

# Fase 00 — Project Kickoff

Ponto de entrada obrigatório para todo projeto IntelliX. Diagnostica o contexto,
define o tipo de sistema e inicializa a estrutura canônica antes de qualquer código.

> **ORDEM OBRIGATÓRIA:** Esta skill só deve ser executada APÓS:
> 1. `superpowers:brainstorming` — ideação e escopo
> 2. `superpowers:writing-plans` — plano de implementação
>
> Se ainda não executou esses passos, faça-os primeiro.

## Quando usar
- Início de qualquer projeto novo
- Onboarding de projeto existente sem estrutura IntelliX
- Quando não está claro em que fase o projeto está

## Quando NÃO usar
- Projeto já inicializado e com fase definida em `.intellix-phase`

## Caminho Automático vs Manual

| Situação | Usar |
|----------|------|
| Projeto 100% novo, do zero | **`/projeto novo`** (zero-touch) — gera references/, agentes/, estrutura SDD, .env, npm install em ~2min |
| Projeto existente sem estrutura IntelliX | Este workflow manual (Passos 1-5 abaixo) |
| Precisa apenas de diagnóstico de fase | Passo 1 abaixo |

> **Recomendado para projetos novos:** usar `/projeto novo` via `intellix:projeto-novo`.
> Ele executa tudo abaixo automaticamente + gera os agentes + instala dependências.

---

## Workflow

### Passo 1 — Diagnóstico (5 perguntas)

Colete as respostas antes de continuar:

1. **Tipo de sistema**: Landing page / CRM / SaaS / Agente WhatsApp / API / Outro?
2. **Integrações previstas**: WhatsApp (Evolution API)? n8n? Supabase? Pagamentos?
3. **Agentes de IA**: O sistema terá agentes ou automações com LLM?
4. **Dados pessoais**: O sistema processará dados de pessoas físicas? (nome, email, CPF, telefone, comportamento, etc.)
   → SE SIM: scaffold LGPD obrigatório na Fase 01 (Architecture) + invocar `devsecops:lgpd-compliance` na Fase 06
5. **Dados sensíveis**: Saúde, biometria, finanças, dados de crianças?
   → SE SIM: regime de proteção reforçado — criptografia AES-256 + consentimento específico

Se o usuário já forneceu essas informações na conversa, pule direto ao Passo 2.

### Passo 2 — Definir stack e escopo

Com base no diagnóstico, confirme:

```
Stack padrão IntelliX (imutável):
- Frontend: Next.js 15 App Router + TypeScript strict + Tailwind + Shadcn/UI
- Backend: Supabase (DB + Auth + Edge Functions) + Cloudflare (Workers/Pages)
- Agentes: SDK Anthropic / n8n + Evolution API (conforme necessidade)
- Testes: Vitest (unit) + Playwright (E2E)

Se o projeto NÃO precisar de agentes → omitir skill 02
Se o projeto for landing page → focar skills 01 + 06
Se for CRM/SaaS → fluxo completo 00 → 07
```

### Passo 3 — Criar estrutura canônica

Gere a estrutura de pastas inicial conforme o tipo de projeto:

**Para SaaS/CRM completo:**
```
projeto/
├── .claude/                    # Configuração e contexto DESTE projeto
│   ├── settings.json           # Plugin IntelliX + permissões (versionado)
│   ├── settings.local.json     # Overrides só seus (gitignored)
│   ├── rules/                  # Convenções específicas deste projeto
│   │   ├── code-style.md
│   │   ├── testing.md
│   │   └── api-conventions.md
│   └── hooks/                  # Guardrails deste repositório
│       └── validate-migration.sh
├── .mcp.json                   # MCP servers deste cliente (versionado, time inteiro usa)
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/
│   │   ├── (dashboard)/
│   │   └── api/
│   ├── components/
│   │   ├── ui/                 # Shadcn/UI components
│   │   └── [feature]/          # Componentes por feature
│   ├── lib/
│   │   ├── supabase/           # Client + Server + types
│   │   ├── utils/
│   │   └── validations/        # Zod schemas
│   ├── hooks/
│   ├── types/
│   └── agents/                 # Se houver agentes
├── supabase/
│   ├── migrations/
│   ├── functions/              # Edge Functions
│   └── seed.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                    # Playwright
├── .intellix-phase             # Fase atual: init|arch|dev|test|deploy|done
├── AGENTS.md                   # Contexto operacional para QUALQUER agente (Cursor, Codex, Copilot...)
├── CLAUDE.md                   # Contexto Claude-específico (versionado — aponta para a metodologia global)
├── CLAUDE.local.md             # Paths, branch ativa, DB local (gitignored)
├── .env.example
└── README.md
```

> **`AGENTS.md` vs `CLAUDE.md`:** `AGENTS.md` contém fatos operacionais neutros (comandos, testes, PR format) legíveis por qualquer agente de coding. `CLAUDE.md` contém regras Claude-específicas (IntelliX workflow, plugin hooks). Claude Code lê ambos; Cursor/Codex/Aider/Copilot só leem `AGENTS.md`.

> **`CLAUDE.md` vs `CLAUDE.local.md`:** o primeiro é versionado e vale para o time inteiro (stack, fase, convenções). O segundo é gitignored e vale só para a sua máquina (paths absolutos, branch em que você está, string de conexão do banco local). Nunca coloque segredo em nenhum dos dois.

---

#### ⛔ O que **NÃO** vai para dentro do projeto (decisão de 2026-09-07)

Não crie `.claude/skills/`, `.claude/agents/` nem `.claude/commands/` no projeto do cliente.

**Por quê:** tudo que é copiado para dentro de um repositório vira um *fork congelado* da
metodologia na data do scaffolding. Corrigir um bug na skill global não corrige as cópias
espalhadas em N repositórios de cliente. Esse é exatamente o modo de falha que a auditoria
de 2026-09-07 documentou em `WORKFLOW-SPINE-VS-ORBIT.md` — skills arquivadas continuaram
sendo invocadas por meses em arquivos que ninguém atualizou.

| Fica no projeto (config e contexto — não existe cópia canônica em outro lugar) | Fica global, invocado por referência |
|---|---|
| `.claude/rules/` — convenções deste cliente | `skills/` — Fases 00-09, todas as skills IntelliX |
| `.claude/hooks/` — guardrails deste repo | `agents/` — os 5 revisores devsecops (já genéricos) |
| `.claude/settings.json` + `.local.json` | `commands/` — `/spec`, `/break`, `/plan`, `/execute` (vêm do plugin) |
| `.mcp.json` — endpoints deste cliente | metodologia, gates, workflow |
| `CLAUDE.md` + `CLAUDE.local.md` + `AGENTS.md` | |

**Única exceção:** uma skill ou agent genuinamente exclusivo daquele projeto, que não faz
sentido em nenhum outro (raro). Nesse caso, documente no `CLAUDE.md` do projeto por que
ela não é global.

### Passo 4 — Inicializar arquivos base

Crie os seguintes arquivos:

**`.intellix-phase`**: conteúdo `arch` (próxima fase após kickoff)

**`AGENTS.md`** (template — adaptar nome e integrações do projeto):
```markdown
# [Nome do Projeto]

> Contexto operacional para agentes de coding (Claude Code, Cursor, Copilot, Codex, Aider, etc.)
> Para regras Claude-específicas e workflow IntelliX, ver CLAUDE.md

## O que é este projeto
[1-2 linhas: o que o sistema faz e para quem]

## Setup
\`\`\`bash
npm install          # instalar dependências
npm run dev          # servidor de desenvolvimento (localhost:3000)
npm run build        # build de produção
npm run lint         # ESLint + TypeScript check
\`\`\`

## Testes
\`\`\`bash
npm run test         # Vitest (unit + integration)
npm run test:e2e     # Playwright E2E
npm run test:watch   # Vitest em watch mode
\`\`\`
Rodar testes antes de qualquer commit. PRs bloqueados se testes falharem.

## Stack
- **Framework:** Next.js 15 App Router + TypeScript strict
- **Estilo:** Tailwind CSS + Shadcn/UI
- **Banco:** Supabase (PostgreSQL + Auth + RLS)
- **Deploy:** Cloudflare Workers/Pages (`wrangler` + `@opennextjs/cloudflare`)
- [adicionar: Evolution API / n8n / etc. se aplicável]

## Estrutura de pastas
\`\`\`
src/app/             → rotas Next.js (App Router)
src/components/ui/   → componentes Shadcn/UI (primitivos)
src/components/[f]/  → componentes por feature
src/lib/             → utilities, validações Zod, clients Supabase
src/hooks/           → custom hooks React
src/types/           → tipos TypeScript centralizados
supabase/migrations/ → migrations de banco
tests/               → unit/ | integration/ | e2e/
\`\`\`

## Convenções de código
- TypeScript strict: **zero `any`**, zero `@ts-ignore`
- Componentes: `PascalCase` | Hooks: `camelCase` com prefixo `use` | Arquivos: `kebab-case`
- Sem `console.log` em produção — usar logger estruturado
- Todo input de usuário validado com Zod
- Toda tabela Supabase com Row Level Security (RLS)

## Commits
Conventional Commits obrigatório:
\`\`\`
feat(auth): adiciona login com Google
fix(dashboard): corrige carregamento de métricas
chore(deps): atualiza next.js para 15.x
\`\`\`

## Pull Requests
- Branch a partir de `main`, nome: `feat/nome-da-feature` ou `fix/descricao`
- PR title: `[feat|fix|chore]: descrição curta`
- Rodar `npm run lint && npm run test` antes de abrir PR
- Descrever o que mudou e por quê no body do PR

## Variáveis de ambiente
Ver `.env.example` para todas as variáveis necessárias.
Nunca commitar `.env.local` ou `.env`.
```

**`CLAUDE.md`** (template — **aponta** para a metodologia global, não a reescreve):
```markdown
# [Nome do Projeto]

## Contexto
[Descrição em 2-3 linhas do que o sistema faz e para quem]

## Stack
Next.js 15 | TypeScript strict | Tailwind | Shadcn/UI | Supabase | Cloudflare (Workers/Pages)

## Fase atual
[FASE] — ver .intellix-phase

## Metodologia
Este projeto segue o workflow IntelliX (Fases 00-09) definido no plugin `intellix`,
instalado na camada global. **Não replique as fases aqui** — elas evoluem no plugin e
esta cópia ficaria desatualizada. Ver `intellix:master-workflow` para o fluxo vigente.

Segurança e LGPD: `devsecops:security-baseline` / `security-gate` / `lgpd-compliance`.

## Convenções deste projeto
Ver `.claude/rules/` — convenções específicas daqui (as globais já valem por padrão).

## Integrações ativas
[listar: n8n / Evolution API / WhatsApp / etc]
```

**`CLAUDE.local.md`** (template — adicionar ao `.gitignore`):
```markdown
# Contexto local — NÃO versionar

## Ambiente local
- Path do projeto: [caminho absoluto nesta máquina]
- Banco local: [connection string do Supabase local, se usar]
- Branch ativa: [branch em que você está trabalhando]

## Notas de trabalho
[o que você está fazendo agora, contexto temporário desta máquina]

> Nunca coloque secrets aqui — use `.env.local` (também gitignored).
```

**`.claude/settings.json`** (habilitar plugin por projeto — versionado):
```json
{
  "enabledPlugins": {
    "intellix@intellix-plugin": true
  }
}
```

**`.claude/rules/`** — criar os 3 arquivos base, cada um só com o que é **específico
deste projeto** (as convenções globais já valem sem precisar repetir):

```markdown
<!-- .claude/rules/code-style.md -->
# Convenções de código — [Nome do Projeto]
[Só o que difere do padrão IntelliX global. Ex: este cliente usa `snake_case`
nas colunas legadas da tabela X; este projeto usa date-fns em vez de dayjs.]

<!-- .claude/rules/testing.md -->
# Testes — [Nome do Projeto]
[Ex: fluxo de checkout exige teste E2E obrigatório; mock do gateway de pagamento
fica em tests/mocks/gateway.ts]

<!-- .claude/rules/api-conventions.md -->
# Convenções de API — [Nome do Projeto]
[Ex: webhooks deste cliente usam assinatura HMAC no header X-Client-Signature]
```

**`.mcp.json`** (MCP servers deste cliente — versionado, todo o time usa):
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": ["-y", "@supabase/mcp-server-supabase@latest", "--project-ref", "<REF_DO_CLIENTE>"]
    }
  }
}
```
> Só inclua servers que o time inteiro precisa para trabalhar neste repositório.
> Credenciais vão por variável de ambiente, nunca inline neste arquivo.

**`.claude/hooks/`** — criar apenas se o projeto tiver um guardrail real
(ex: bloquear escrita em `supabase/migrations/` sem review, rodar `tsc` após edit).
Projeto sem necessidade concreta não precisa da pasta.

**`.gitignore`** — obrigatório adicionar as entradas locais, senão contexto de máquina
vaza para o repositório do cliente:
```gitignore
# Claude Code — contexto local (não versionar)
CLAUDE.local.md
.claude/settings.local.json

# Ambiente
.env
.env.local
```
> `.claude/settings.json`, `.claude/rules/`, `.claude/hooks/` e `.mcp.json` **são**
> versionados — é o contrato do time. Só os `*.local.*` ficam de fora.

### Passo 4b — Qualidade do Contexto `context-engineering` (projetos novos)

**Invoke:** `Skill("context-engineering")`

Após criar `CLAUDE.md` e `AGENTS.md`, valide a qualidade do contexto entregue aos agentes:

- Verificar se `CLAUDE.md` tem as 5 camadas de informação: stack, fase atual, convenções, integrações, anti-patterns
- Confirmar que `AGENTS.md` tem comandos operacionais verificáveis (não documentação genérica)
- Garantir ausência de "context flooding" (informação demais) e "context starvation" (informação de menos)
- Estruturar regras em ordem de prioridade — agentes lêem o início com mais atenção

**Gatilho:** obrigatório em projetos novos. Opcional em projetos existentes (só se CLAUDE.md estiver desatualizado).

---

### Passo 5 — Handover para Fase 01

Ao concluir, informe:
> "Kickoff concluído. Estrutura inicializada. Próxima fase: **intellix:architecture** para definir o schema de banco, rotas e componentes principais."

Se `HAS_PERSONAL_DATA = S`, adicionar ao handover:
> "⚠️ Projeto com dados pessoais detectado. Na Fase 01 (Architecture): incluir tabelas LGPD no schema (`consent_records`, `titular_requests`, `data_processing_log`). Na Fase 06: executar `devsecops:lgpd-compliance` em paralelo com `security-observability`."

Atualize `.intellix-phase` para `arch`.

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Brainstorm de produto antes de definir escopo | `superpowers:brainstorming` |
| PRD completo com features, personas e arquitetura | `ai-project-brainstorm` |
| Projeto é landing page ou site simples | `impeccable` (`init`/`shape`) |
| Planejar implementação em etapas antes de codar | `superpowers:writing-plans` |

---

## Armadilhas comuns
- ❌ Criar arquivos de código antes do kickoff → sempre executar esta skill primeiro
- ❌ Pular o diagnóstico → resulta em estrutura errada para o tipo de projeto
- ❌ Usar `pages/` router em vez de `app/` → IntelliX usa exclusivamente App Router
