---
name: intellix-projeto-novo
description: >
  Automação zero-touch para inicialização de projetos IntelliX via comando /projeto novo.
  Ativa quando o usuário digita "/projeto novo" ou menciona "iniciar projeto do zero com template",
  "setup automático de projeto", "boilerplate IntelliX", "criar projeto com estrutura SDD".
  Elimina setup manual: coleta inputs interativos, substitui placeholders nos templates,
  compila agentes especializados, instala dependências e entrega estrutura pronta para /spec.
user-invocable: true
---

# /projeto novo — Setup Zero-Touch IntelliX

Automatiza 100% do setup inicial: `references/` customizadas, agentes compilados,
estrutura SDD, `.env.local` com secrets e `npm install` — tudo em ~2 minutos.

> **Referência:** Parte 8 do roteiro SDD IntelliX. Ver também `MASTER-ARCHITECTURE.md §FASE-00`.
> **Pré-requisito:** Brainstorm e plano aprovados (`superpowers:brainstorming` + `superpowers:writing-plans`).

---

## PASSO 1 — Coleta de Inputs (máx. 5 perguntas)

Faça estas perguntas **em sequência**, uma por vez. Aguarde a resposta antes de continuar.

```
Pergunta 1: Qual o nome do projeto? (ex: "NossoCRM", "LeadBot Pro")
Pergunta 2: Descreva o problema que resolve em 1-2 frases.
Pergunta 3: Nome do cliente ou "IntelliX Interno".
Pergunta 4: Cor primária em hex? (ex: #007AFF) — ou pressione Enter para usar #6366F1
Pergunta 5: Tem Supabase project ID ou Vercel project ID já criados?
           (opcional — pressione Enter para gerar placeholders)
Pergunta 6: O projeto processará dados pessoais de pessoas físicas?
           (nome, email, CPF, telefone, endereço, comportamento de uso, etc.)
           [S] Sim — scaffoldar LGPD: tabelas + pii-redactor + checklist
           [N] Não — pular scaffolding LGPD
Pergunta 7: O projeto terá chamadas a LLMs (OpenAI, Anthropic, etc.) ou agentes autônomos?
           [S] Sim — scaffoldar guardrails: prePromptFilter + postOutputValidator
           [N] Não — pular scaffolding LLM
```

**Inputs opcionais** (se não informados, geram placeholders em `.env.example`):
- `supabaseProjectId` — conecta a projeto Supabase existente
- `vercelProjectId` — conecta a Vercel existente
- `anthropicApiKey` — salvo em `.env.local`, nunca commitado

Ao receber todas as respostas, derive os valores calculados:

```
PROJECT_SLUG        = projectName em lowercase, sem espaços, sem acentos (ex: "nossocrm")
SECONDARY_COLOR     = se não informado, usar #10B981
CREATED_AT          = data atual no formato YYYY-MM-DD
HAS_PERSONAL_DATA   = S ou N (Pergunta 6)
HAS_LLM             = S ou N (Pergunta 7)
```

Confirme o resumo com o usuário antes de prosseguir:
```
📋 Resumo do projeto a inicializar:
   Nome: {{PROJECT_NAME}} (slug: {{PROJECT_SLUG}})
   Cliente: {{CLIENT_NAME}}
   Cores: {{PRIMARY_COLOR}} / {{SECONDARY_COLOR}}
   Supabase: {{SUPABASE_PROJECT_ID || "placeholder"}}

Confirmar? [S/n]
```

---

## PASSO 2 — Verificar Diretório e Estado

Antes de criar qualquer arquivo:

1. Verificar se o diretório `{{PROJECT_SLUG}}/` já existe
2. Se existe E já tem `.intellix-phase`:
   ```
   ⚠️  Projeto IntelliX detectado em {{PROJECT_SLUG}}/
   [1] Atualizar apenas references/
   [2] Resetar projeto (apaga tudo — irreversível)
   [3] Cancelar
   ```
3. Se existe mas SEM `.intellix-phase` → inicializar normalmente nele
4. Se não existe → criar a pasta e inicializar

**Regra de rollback (R1):** Se qualquer passo falhar a partir daqui,
deletar o diretório recém-criado e reportar o erro com instrução de correção.

---

## PASSO 3 — Criar Estrutura de Pastas SDD

Criar a seguinte estrutura de pastas (apenas diretórios — arquivos vêm nos passos seguintes):

```
{{PROJECT_SLUG}}/
├── .github/
│   └── workflows/
│       └── security.yml          ← DevSecOps CI/CD (sempre criado)
├── .claude/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   └── login/
│   │   ├── (dashboard)/
│   │   └── api/
│   ├── components/
│   │   ├── ui/
│   │   └── shared/
│   ├── lib/
│   │   ├── auth/
│   │   ├── db/
│   │   ├── ai/
│   │   │   └── guardrails.ts     ← se HAS_LLM=S
│   │   ├── lgpd/
│   │   │   └── pii-redactor.ts   ← se HAS_PERSONAL_DATA=S
│   │   └── utils/
│   └── types/
├── supabase/
│   └── migrations/
│       └── 00001_lgpd_tables.sql ← se HAS_PERSONAL_DATA=S
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── references/
├── agentes/
└── issues/
```

---

## PASSO 4 — Gerar `references/` com Placeholders Substituídos

Criar os 5 arquivos abaixo com os placeholders já substituídos pelos valores do Passo 1.

### `references/architecture.md`

```markdown
# Arquitetura — {{PROJECT_NAME}}

> Gerado em: {{CREATED_AT}} | Template: IntelliX SDD v2
> Regras inegociáveis do projeto. Consulte ANTES de qualquer /plan.

## 1. Compartimentação de Behaviors

- Cada comportamento tem sua própria pasta dentro da rota
- Comportamento NUNCA importa de outro comportamento irmão
- Compartilhamento apenas via `lib/` ou `components/shared/`
- Estrutura: `app/(grupo)/rota/nome-do-behavior/`

## 2. Thin Client / Fat Server

- Toda regra de negócio em server actions (`action.ts`)
- Client apenas captura input e renderiza output recebido
- Re-validar permissões no server SEMPRE (consultar DB, não confiar no client)
- NUNCA validar role/permissão via variável JS no client

## 3. Estrutura Obrigatória por Behavior

```
nome-do-behavior/
├── action.ts      # server action — valida sessão + Zod + lógica
├── schema.ts      # Zod schema do input
└── form.tsx       # client component — captura input, exibe feedback
```

## 4. Imports Proibidos

- Client → server libs (use 'use server' para server actions)
- Behavior A → Behavior B (compartilhar via lib/ apenas)
- Supabase queries diretas em componentes (usar via server action)

## 5. Informações do Projeto

- **Cliente:** {{CLIENT_NAME}}
- **Stack:** {{STACK_PRESET}}
- **Criado em:** {{CREATED_AT}}
- **Supabase project:** {{SUPABASE_PROJECT_ID}}
```

### `references/design_system.md`

```markdown
# Design System — {{PROJECT_NAME}}

> Gerado em: {{CREATED_AT}}

## Tokens de Cor

- **Primária:** `{{PRIMARY_COLOR}}` — ações principais, CTAs
- **Secundária:** `{{SECONDARY_COLOR}}` — destaques, badges
- **Fundo:** `#FFFFFF` (light) / `#0F0F0F` (dark)
- **Texto:** `#111827` (light) / `#F9FAFB` (dark)
- **Bordas:** `#E5E7EB`
- **Destrutivo:** `#EF4444`

Definir estes tokens em `tailwind.config.ts` — nunca hardcode hex nos componentes.

## Tipografia

- **Sans:** Inter (padrão Shadcn/UI)
- **Mono:** JetBrains Mono (código, badges técnicos)
- Escala: 12 / 14 / 16 / 18 / 20 / 24 / 30 / 36 / 48

## Componentes

- **Primitivos:** SEMPRE de `@/components/ui` (Shadcn/UI)
- NUNCA criar Button, Input, Dialog, Card do zero — customizar via `variants` (cva)
- Componentes de negócio em `components/shared/`

## Spacing

- Múltiplos de 4 (Tailwind scale padrão)
- Padding padrão de cards: `p-6`
- Gap entre elementos relacionados: `gap-4`
- Gap entre seções: `gap-8`

## Acessibilidade

- Contraste mínimo: 4.5:1 (WCAG AA)
- Focus ring visível em todos os elementos interativos
- Todo ícone clicável sem texto visível: `aria-label` obrigatório
```

### `references/workflow.md`

```markdown
# Workflow para Agentes IA — {{PROJECT_NAME}}

> Regras operacionais para Claude Code e subagentes neste projeto.

## Antes de QUALQUER mudança

1. Ler `references/architecture.md` deste projeto
2. Ler a issue completa (caminho feliz + edge + erros + Files to NOT Touch)
3. Listar arquivos que vai tocar
4. Confirmar com o usuário ANTES de executar

## Durante a execução

- Nunca criar arquivo fora dos paths declarados na issue
- Nunca modificar arquivo listado em "Files to NOT Touch"
- Se precisar de novo arquivo não previsto → parar e perguntar ao usuário
- Context window > 60%? → parar, fazer /clear, retomar com plano

## Depois de cada issue

- Rodar testes: `npm run test` + verificar `tsc --noEmit`
- Confirmar que nenhum arquivo fora da lista foi tocado
- Reportar arquivos criados/modificados

## /clear entre fases

Execute /clear nos seguintes momentos:
- Após /plan aprovado → antes de /execute
- Após pesquisa de codebase → antes de escrever código
- Ao trocar de issue
```

### `references/stack.md`

```markdown
# Stack Tecnológica — {{PROJECT_NAME}} (NÃO-NEGOCIÁVEL)

> Gerado em: {{CREATED_AT}} | Template versão: {{TEMPLATE_VERSION}}

## Stack Fixa

- **Framework:** Next.js 15 (App Router)
- **Linguagem:** TypeScript strict (`strict: true`, zero `any`)
- **Estilo:** Tailwind CSS + Shadcn/UI
- **Banco de dados:** Supabase (PostgreSQL + RLS + Auth)
- **Hospedagem:** Vercel
- **IA:** Anthropic SDK
- **Validação:** Zod
- **Forms:** react-hook-form
- **Preset:** {{STACK_PRESET}}

## Versões Canônicas (IntelliX)

| Pacote | Versão |
|--------|--------|
| next | 15.0.0 |
| react | ^19.0.0 |
| typescript | ^5.3.3 |
| tailwindcss | ^3.3.5 |
| @supabase/supabase-js | ^2.38.0 |
| @anthropic-ai/sdk | ^0.9.0 |
| zod | ^3.22.0 |
| react-hook-form | ^7.48.0 |

`package.json` é a fonte da verdade. Não sugerir upgrades ou libs alternativas sem aprovação explícita.
```

### `references/security.md`

```markdown
# Checklist de Segurança — {{PROJECT_NAME}}

> Validar ANTES de cada PR/merge. Zero exceções.

## Checklist de Segurança (Defense in Depth — 4 camadas)

```
1. Middleware Next.js     → bloqueia rotas sem sessão válida
2. Server Action / Route  → valida input com Zod (schema obrigatório)
3. Server Action / Route  → re-valida permissões consultando DB
4. Supabase RLS Policy    → última linha de defesa no banco
```

## Pré-PR Checklist

- [ ] Nenhuma API key em código client ou commitado
- [ ] Toda server action valida sessão no início
- [ ] RLS habilitado em toda tabela Supabase nova
- [ ] Rate limiting em endpoints públicos
- [ ] Inputs sanitizados com Zod antes de qualquer operação
- [ ] Erros não expõem stack trace ao client
- [ ] CORS configurado restritivamente (não `*`)
- [ ] Secrets apenas em variáveis server-side (nunca `NEXT_PUBLIC_` para dados sensíveis)
- [ ] Nenhuma lógica de role/permissão no client

## Anti-pattern Crítico

❌ `if (user.isAdmin)` no client — hacker abre DevTools e muda em 30 segundos
✅ Sempre buscar role no banco no server action antes de qualquer operação privilegiada
```

---

## PASSO 4b — DevSecOps Scaffold (SEMPRE executar — não condicional)

### `.github/workflows/security.yml`

```yaml
name: DevSecOps Security Scan
on: [push, pull_request]

jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
        env: { GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN }}' }

  sast-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: "p/typescript p/owasp-top-ten p/nextjs"

  sca-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          format: "sarif"
          output: "trivy-results.sarif"
          severity: "CRITICAL,HIGH"
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with: { sarif_file: "trivy-results.sarif" }
```

> Custo zero. PRs com CRITICAL não fazem merge. HIGH exige dispensa documentada.

---

### `src/lib/lgpd/pii-redactor.ts` — criar SE `HAS_PERSONAL_DATA = S`

```typescript
// Redação de PII — executar ANTES de enviar qualquer dado ao LLM (LGPD Art. 46)
const PII_PATTERNS = [
  { regex: /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, token: '[CPF]' },
  { regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, token: '[EMAIL]' },
  { regex: /\b(\+55\s?)?(\(?\d{2}\)?\s?)?[\d\s\-]{8,}\b/g, token: '[TELEFONE]' },
  { regex: /\b\d{5}-?\d{3}\b/g, token: '[CEP]' },
]
export function redactPII(text: string): string {
  return PII_PATTERNS.reduce((acc, { regex, token }) => acc.replace(regex, token), text)
}
```

### `supabase/migrations/00001_lgpd_tables.sql` — criar SE `HAS_PERSONAL_DATA = S`

```sql
-- Tabelas LGPD obrigatórias — Lei 13.709/2018 | gerado por /projeto novo
CREATE TABLE consent_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  purpose TEXT NOT NULL, granted BOOLEAN NOT NULL,
  granted_at TIMESTAMPTZ, revoked_at TIMESTAMPTZ,
  version TEXT NOT NULL DEFAULT '1.0',
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE titular_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id), email TEXT NOT NULL,
  request_type TEXT NOT NULL CHECK (request_type IN (
    'access','correction','deletion','portability',
    'consent_revoke','anonymization','automated_review'
  )),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending','in_progress','completed','rejected'
  )),
  deadline TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '15 days'),
  response TEXT, created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE data_processing_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  operation TEXT NOT NULL, data_categories TEXT[] NOT NULL,
  purpose TEXT NOT NULL, legal_basis TEXT NOT NULL,
  automated BOOLEAN DEFAULT false, ai_model TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE titular_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_processing_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "titular_own_consents" ON consent_records FOR ALL USING (user_id = auth.uid());
CREATE POLICY "titular_own_requests" ON titular_requests FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "admin_manage_requests" ON titular_requests FOR ALL USING (
  EXISTS (SELECT 1 FROM user_roles WHERE user_id = auth.uid() AND role = 'admin'));
CREATE POLICY "admin_read_log" ON data_processing_log FOR SELECT USING (
  EXISTS (SELECT 1 FROM user_roles WHERE user_id = auth.uid() AND role = 'admin'));
```

### `src/lib/ai/guardrails.ts` — criar SE `HAS_LLM = S`

```typescript
// Pipeline de guardrails — Camadas 1 e 4 obrigatórias (OWASP LLM Top 10 2025)
import { redactPII } from '@/lib/lgpd/pii-redactor'

const INJECTION_PATTERNS = [
  /ignore\s+(previous|all|above)\s+instructions/i,
  /you\s+are\s+now\s+(a|an)\s+/i,
  /system\s*:\s*you/i,
]

export function prePromptFilter(input: string): { safe: boolean; sanitized: string } {
  if (INJECTION_PATTERNS.some(p => p.test(input))) return { safe: false, sanitized: '' }
  return { safe: true, sanitized: redactPII(input) }
}

export function postOutputValidator(output: string): { valid: boolean; sanitized: string } {
  const LEAKS = [/you are (a|an) .+ assistant/i, /system prompt/i]
  if (LEAKS.some(p => p.test(output)))
    return { valid: false, sanitized: '[Resposta bloqueada por política de segurança]' }
  return { valid: true, sanitized: redactPII(output) }
}
```

---

## PASSO 5 — Compilar Agentes Especializados

Criar os 4 arquivos JSON em `agentes/` com `{{PROJECT_NAME}}` substituído:

### `agentes/model_writer.json`

```json
{
  "name": "model_writer",
  "project": "{{PROJECT_NAME}}",
  "scope": "database-only",
  "reads_before_start": [
    "references/architecture.md",
    "references/stack.md"
  ],
  "forbidden_paths": [
    "app/",
    "components/",
    "lib/auth/",
    "lib/ai/"
  ],
  "allowed_paths": [
    "lib/db/",
    "supabase/migrations/",
    "supabase/seed.sql",
    "src/types/index.ts"
  ],
  "max_context_percent": 45,
  "skill": "write_db_models",
  "system_prompt_prefix": "Você é o model_writer do projeto {{PROJECT_NAME}}. Sua única responsabilidade é schema de banco de dados e RLS policies. Antes de qualquer ação, leia references/architecture.md. Nunca toque em arquivos fora de lib/db/ ou supabase/. Toda tabela precisa de RLS ativo."
}
```

### `agentes/action_writer.json`

```json
{
  "name": "action_writer",
  "project": "{{PROJECT_NAME}}",
  "scope": "server-actions-only",
  "reads_before_start": [
    "references/architecture.md",
    "references/security.md"
  ],
  "forbidden_paths": [
    "components/",
    "lib/db/",
    "supabase/"
  ],
  "allowed_paths": [
    "app/**/action.ts",
    "app/**/schema.ts",
    "lib/auth/",
    "src/validations/"
  ],
  "max_context_percent": 45,
  "skill": "write_server_actions",
  "system_prompt_prefix": "Você é o action_writer do projeto {{PROJECT_NAME}}. Sua única responsabilidade são server actions e seus schemas Zod. Toda action DEVE: (1) validar sessão no início, (2) validar input com Zod, (3) re-validar permissões consultando DB. Nunca coloque lógica de negócio em componentes client."
}
```

### `agentes/component_writer.json`

```json
{
  "name": "component_writer",
  "project": "{{PROJECT_NAME}}",
  "scope": "ui-only",
  "reads_before_start": [
    "references/architecture.md",
    "references/design_system.md"
  ],
  "forbidden_paths": [
    "lib/db/",
    "supabase/",
    "app/**/action.ts",
    "app/**/schema.ts"
  ],
  "allowed_paths": [
    "app/**/form.tsx",
    "app/**/page.tsx",
    "app/**/layout.tsx",
    "components/shared/"
  ],
  "max_context_percent": 45,
  "skill": "write_components",
  "system_prompt_prefix": "Você é o component_writer do projeto {{PROJECT_NAME}}. Sua única responsabilidade são componentes React client. Use apenas Shadcn/UI de @/components/ui — nunca crie Button, Input ou Dialog do zero. Nunca escreva lógica de negócio: apenas capture inputs e renderize outputs recebidos de server actions. Cor primária do projeto: {{PRIMARY_COLOR}}."
}
```

### `agentes/test_writer.json`

```json
{
  "name": "test_writer",
  "project": "{{PROJECT_NAME}}",
  "scope": "tests-only",
  "reads_before_start": [
    "references/architecture.md"
  ],
  "forbidden_paths": [
    "lib/",
    "components/ui/",
    "supabase/"
  ],
  "allowed_paths": [
    "app/**/*.test.tsx",
    "tests/unit/",
    "tests/integration/",
    "tests/e2e/"
  ],
  "max_context_percent": 40,
  "skill": "write_e2e_tests",
  "system_prompt_prefix": "Você é o test_writer do projeto {{PROJECT_NAME}}. Sua única responsabilidade são testes. Para cada behavior, valide: (1) caminho feliz, (2) ao menos 1 edge case, (3) o erro mais provável. Nunca modifique arquivos de produção."
}
```

---

## PASSO 6 — Gerar Arquivos de Configuração

### `.env.example` (commitável — sem valores reais)

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://{{SUPABASE_PROJECT_ID}}.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Anthropic
ANTHROPIC_API_KEY=

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXTAUTH_SECRET=

# Opcional — Evolution API / WhatsApp
# EVOLUTION_API_URL=
# EVOLUTION_API_KEY=
```

### `.env.local` (gitignored — com valores reais)

Criar com os secrets informados no Passo 1. Para campos não informados, usar placeholder `PREENCHER`:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://{{SUPABASE_PROJECT_ID}}.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=PREENCHER
SUPABASE_SERVICE_ROLE_KEY=PREENCHER

# Anthropic
ANTHROPIC_API_KEY={{ANTHROPIC_API_KEY || "PREENCHER"}}

NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Verificar que `.env.local` está em `.gitignore` — se não estiver, adicioná-lo.

### `.intellix-phase`

```
init
```

### `.claude/settings.json`

```json
{
  "enabledPlugins": {
    "intellix@intellix-marketplace": true
  }
}
```

### `.claude/CLAUDE.md`

```markdown
# {{PROJECT_NAME}} — Contexto do Projeto

## Sistema
{{PROJECT_DESCRIPTION}}

## Cliente
{{CLIENT_NAME}}

## Stack
Next.js 15 | TypeScript strict | Tailwind | Shadcn/UI | Supabase | Vercel | Anthropic SDK

## Fase atual
init → ver .intellix-phase

## Padrões obrigatórios
- TypeScript strict: NUNCA usar `any`
- Commits: Conventional Commits (feat:, fix:, chore:, etc.)
- Testes: toda feature nova precisa de testes
- RLS: toda tabela Supabase com Row Level Security

## References do projeto (ler antes de qualquer /plan)
- `references/architecture.md` — regras de isolamento e estrutura
- `references/design_system.md` — cores {{PRIMARY_COLOR}} / {{SECONDARY_COLOR}}, tipografia, componentes
- `references/security.md` — checklist pré-PR
- `references/stack.md` — versões fixas, não sugerir alternativas
- `references/workflow.md` — regras operacionais para agentes

## Agentes disponíveis
- `agentes/model_writer.json` — schema DB + RLS (lib/db/ + supabase/)
- `agentes/action_writer.json` — server actions (app/**/action.ts)
- `agentes/component_writer.json` — componentes React (app/**/form.tsx)
- `agentes/test_writer.json` — testes (tests/ + *.test.tsx)
```

---

## PASSO 7 — Gerar `package.json`

```json
{
  "name": "{{PROJECT_SLUG}}",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@supabase/supabase-js": "^2.38.0",
    "@supabase/ssr": "^0.1.0",
    "@anthropic-ai/sdk": "^0.9.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.48.0",
    "@hookform/resolvers": "^3.3.2",
    "tailwind-merge": "^2.0.0",
    "clsx": "^2.0.0",
    "class-variance-authority": "^0.7.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/node": "^20.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "tailwindcss": "^3.3.5",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "vitest": "^1.0.0",
    "@playwright/test": "^1.40.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "15.0.0"
  }
}
```

---

## PASSO 8 — Executar `npm install`

```bash
cd {{PROJECT_SLUG}} && npm install
```

Aguardar a conclusão. Se falhar por versão incompatível, reportar exatamente o erro sem tentar corrigir automaticamente — apresentar ao usuário para decisão.

---

## PASSO 9 — Relatório de Confirmação e Handover

Exibir relatório:

```
✅ Projeto "{{PROJECT_NAME}}" inicializado com sucesso

📁 Estrutura criada:
   {{PROJECT_SLUG}}/
   ├── .github/workflows/security.yml  ← DevSecOps CI/CD (Gitleaks + Semgrep + Trivy)
   ├── references/    ← 5 arquivos customizados (architecture, design_system, workflow, stack, security)
   ├── agentes/       ← 4 agentes compilados (model_writer, action_writer, component_writer, test_writer)
   ├── src/           ← estrutura SDD pronta
   ├── .env.local     ← secrets configurados
   ├── .env.example   ← template commitável
   └── package.json   ← stack IntelliX v{{TEMPLATE_VERSION}} fixada

🔒 Secrets (.env.local — gitignored):
   [listar status de cada secret: ✓ configurado | ⚠ PREENCHER]

📦 Dependências: npm install ✓ (ou ⚠ com erro específico)

🛡️ DevSecOps:
   ✓ .github/workflows/security.yml — CI/CD rodará em todo PR automaticamente
   [se HAS_PERSONAL_DATA=S] ✓ src/lib/lgpd/pii-redactor.ts — redação de PII antes de LLMs
   [se HAS_PERSONAL_DATA=S] ✓ supabase/migrations/00001_lgpd_tables.sql — consent_records + titular_requests + data_processing_log
   [se HAS_LLM=S] ✓ src/lib/ai/guardrails.ts — prePromptFilter + postOutputValidator

🤖 Agentes prontos:
   ✓ model_writer    → lib/db/ + supabase/migrations/
   ✓ action_writer   → app/**/action.ts + schema.ts
   ✓ component_writer → app/**/form.tsx + components/shared/
   ✓ test_writer     → tests/ + *.test.tsx

📋 Próximos passos:
   1. /spec — mapear páginas e comportamentos
   2. /break — quebrar em issues atômicas
   3. /plan [issue] — pesquisa 3 frentes + plano com 7 seções
   4. /execute [issue] — agente correto por tipo de arquivo
```

Atualizar `.intellix-phase` para `arch`.

Handover para `intellix:architecture` para definir schema de banco, rotas e tipos.

---

## Regras de Implementação (Obrigatórias)

| # | Regra | O que fazer |
|---|-------|-------------|
| R1 | **Atomicidade** | Se qualquer passo falhar → rollback completo da pasta criada + reportar erro com instrução |
| R2 | **Idempotência** | Projeto existente detectado → menu [Atualizar references / Resetar / Cancelar] |
| R3 | **Secrets isolados** | Variáveis com `_KEY`, `_SECRET`, `_TOKEN` → apenas em `.env.local` (gitignored), nunca em template commitável |
| R4 | **Contexto isolado** | Cada agente JSON é invocado em instância separada — output de um vira arquivo, o próximo lê o arquivo |
| R5 | **References primeiro** | `reads_before_start` em todo agente é a primeira ação antes de qualquer escrita |
| R6 | **Versionamento** | Registrar versão do template em `references/stack.md` do projeto |

---

## Ordem de Execução dos Agentes (no /execute)

Dentro de cada issue, os agentes são invocados nesta ordem:

```
1. model_writer    → cria/atualiza tabelas + RLS migrations
2. action_writer   → cria server actions + schemas Zod
3. component_writer → cria UI consumindo as actions
4. test_writer     → valida o fluxo completo
```

Cada agente recebe contexto isolado. O output de cada um vira arquivo em disco —
o próximo agente lê o arquivo, não a memória do anterior.
