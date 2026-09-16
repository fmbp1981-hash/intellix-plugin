# Bootstrap técnico — projeto novo (Fase 00, modo "projeto novo")

> Carregado pelo `intellix:project-kickoff` quando o projeto é criado do zero
> (`/intellix:new-project`). Absorve o antigo `projeto-novo` (arquivado em
> 2026-09-16, decisão D7). Lista normativa do que o projeto precisa ter no fim:
> `artefatos_projeto` em `~/.claude/metodologia.yaml`.

## B1 — Dados do briefing

Além das 5 perguntas do diagnóstico (Passo 1 do kickoff), colete — uma pergunta por vez,
pulando o que o usuário já informou:

```
1. Nome do projeto (ex: "NossoCRM")
2. Problema que resolve, em 1–2 frases
3. Cliente (ou "IntelliX Interno")
4. Cor primária em hex (Enter = #6366F1) e secundária (Enter = #10B981)
5. Supabase project ID e Cloudflare account ID, se já existirem (Enter = placeholder)
```

**Nunca peça chaves de API, tokens ou senhas no chat.** Segredos são preenchidos pelo
usuário direto em `.env.local` (dev) e via `wrangler secret put` (staging/produção).

Valores derivados:

```
PROJECT_SLUG      = nome em minúsculas, sem espaços e sem acentos
CREATED_AT        = data de hoje (YYYY-MM-DD)
TEMPLATE_VERSION  = campo "version" de intellix-templates/version.json
HAS_PERSONAL_DATA = S/N (pergunta 4 do diagnóstico)
HAS_LLM           = S/N (pergunta 3 do diagnóstico)
HAS_UI            = S/N (tipo de sistema ≠ API/worker puro)
```

Mostre o resumo e peça confirmação antes de criar qualquer arquivo.

## B2 — Diretório de destino

1. Se `{{PROJECT_SLUG}}/` não existe → criar.
2. Se existe **sem** `.intellix-phase` → inicializar nele (sem apagar nada existente).
3. Se existe **com** `.intellix-phase` → oferecer só **[1] completar os artefatos
   ausentes** ou **[2] cancelar**. Nunca ofereça apagar/resetar o diretório.

Se um passo falhar, pare e reporte o erro exato. Não apague arquivos para "desfazer".

## B3 — `references/` e `DESIGN.md` (a partir dos templates, sem reescrever)

Copie os templates do plugin substituindo os placeholders (`{{PROJECT_NAME}}`,
`{{CLIENT_NAME}}`, `{{CREATED_AT}}`, `{{TEMPLATE_VERSION}}`, `{{STACK_PRESET}}`,
`{{SUPABASE_PROJECT_ID}}`, `{{PRIMARY_COLOR}}`, `{{SECONDARY_COLOR}}`):

| Origem (`${CLAUDE_PLUGIN_ROOT}/intellix-templates/`) | Destino no projeto |
|---|---|
| `references-template/architecture.md` | `references/architecture.md` |
| `references-template/security.md` | `references/security.md` |
| `references-template/stack.md` | `references/stack.md` |
| `references-template/workflow.md` | `references/workflow.md` |
| `root-template/DESIGN.md` (só se `HAS_UI = S`) | `DESIGN.md` (raiz) |

Os templates são a fonte única — **não** escreva versões próprias desses arquivos.
`references/architecture.md` sai com o marcador `intellix-rascunho-kickoff`; a Fase 01
(`intellix:architecture`) remove o marcador ao registrar as decisões do projeto, e o
phase gate de `/plan` e `/execute` bloqueia enquanto ele existir.

Crie também `issues/` (vazio, com `.gitkeep`).

## B4 — DevSecOps scaffold

| Arquivo | Quando | Fonte |
|---|---|---|
| `.github/workflows/security.yml` | sempre | bloco YAML (Gitleaks + Semgrep + Trivy) em `references/security.md` |
| `src/lib/lgpd/pii-redactor.ts` | `HAS_PERSONAL_DATA = S` | bloco de código em `references/security.md` |
| `src/lib/ai/guardrails.ts` | `HAS_LLM = S` | bloco de código (Camadas 1 e 4) em `references/security.md` |

Tabelas LGPD (consentimento, requisições de titular, log de tratamento) **não** são criadas
aqui: entram nas primeiras migrations da Fase 01, conforme `devsecops:lgpd-compliance`
(autoridade do domínio — prazos legais vêm de lá, não de memória).

## B5 — Ambiente

`.env.example` (versionado, sem valores):

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://{{SUPABASE_PROJECT_ID}}.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# IA (se HAS_LLM = S)
ANTHROPIC_API_KEY=

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Cloudflare (deploy — segredos de produção vão por `wrangler secret put`)
CLOUDFLARE_ACCOUNT_ID={{CLOUDFLARE_ACCOUNT_ID}}

# Opcional — Evolution API / WhatsApp
# EVOLUTION_API_URL=
# EVOLUTION_API_KEY=
```

`.env.local` (gitignored): mesma lista, com `PREENCHER` em todo valor secreto. Confirme
que `.env.local` está no `.gitignore` (Passo 4 do kickoff).

## B6 — `package.json` e dependências

> ⚠️ **Verifique as versões antes de gravar.** Use Context7 (`resolve-library-id` +
> `query-docs`) ou Perplexity para confirmar a major/minor atual de cada pacote — a
> tabela de `references/stack.md` é ponto de partida, não verdade. Se a major de um
> pacote divergir da stack declarada em `~/.claude/metodologia.yaml` (ex.: Next.js),
> **pare e pergunte** ao usuário qual vale; não escolha sozinho.

Scripts mínimos:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "vitest",
    "test:e2e": "playwright test"
  }
}
```

Os scripts de deploy (`preview`, `deploy`, `cf-typegen`) e as dependências
`@opennextjs/cloudflare`/`wrangler` são adicionados na Fase 08 (`intellix:deploy`).

Dependências de referência: `next`, `react`, `react-dom`, `@supabase/supabase-js`,
`@supabase/ssr`, `zod`, `react-hook-form`, `@hookform/resolvers`, `tailwind-merge`,
`clsx`, `class-variance-authority`, `lucide-react` (+ `@anthropic-ai/sdk` se `HAS_LLM = S`);
dev: `typescript`, `@types/node`, `@types/react`, `@types/react-dom`, `tailwindcss`,
`postcss`, `vitest`, `@playwright/test`, `eslint`, `eslint-config-next`.

**`npm install` baixa pacotes:** peça confirmação ao usuário antes de rodar. Se falhar por
versão incompatível, reporte o erro exato e deixe o usuário decidir.

## B7 — Verificação final (obrigatória)

```bash
python3 ~/.claude/scripts/scaffold-check.py {{PROJECT_SLUG}} --fase kickoff
```

Exit 0 = todos os artefatos da fase existem. Exit 1 = liste os faltantes e complete-os
antes do handover.
