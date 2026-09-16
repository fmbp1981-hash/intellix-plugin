# Stack Tecnológica — {{PROJECT_NAME}} (NÃO-NEGOCIÁVEL)

> Gerado em: {{CREATED_AT}} | Template versão: {{TEMPLATE_VERSION}}

## Stack Fixa

- **Framework:** Next.js 15 (App Router)
- **Linguagem:** TypeScript strict (`strict: true`, zero `any`)
- **Estilo:** Tailwind CSS + Shadcn/UI
- **Banco de dados:** Supabase (PostgreSQL + RLS + Auth)
- **Hospedagem:** Cloudflare Workers/Pages (`@opennextjs/cloudflare` + `wrangler`)
- **IA:** Anthropic SDK
- **Validação:** Zod
- **Forms:** react-hook-form
- **Preset:** {{STACK_PRESET}}

## Versões de referência

> ⚠️ **Verifique antes de fixar.** Confirme a major/minor atual de cada pacote via Context7
> (`resolve-library-id` + `query-docs`) ou Perplexity antes do primeiro `npm install`. A
> tabela é ponto de partida (referência de 2026-08-25), não verdade. Se a major de um pacote
> divergir da stack em `~/.claude/metodologia.yaml`, pergunte ao responsável qual vale.

| Pacote | Major/minor de referência |
|--------|---------------------------|
| next, eslint-config-next | major conforme `stack.framework` em `~/.claude/metodologia.yaml` |
| react / react-dom | 19.2.x |
| typescript | 5.x (checar minor atual) |
| tailwindcss | 4.3.x (prefixing já incluso — sem `autoprefixer`) |
| @supabase/supabase-js | 2.112.x |
| @supabase/ssr | checar versão atual |
| @anthropic-ai/sdk | 0.120.x |
| zod | 4.4.x |
| react-hook-form | 7.86.x |
| motion (ex-framer-motion) | 13.1.x — importar de `motion/react` |
| vitest | 4.1.x |
| @playwright/test | 1.62.x |
| eslint | 10.x (flat config) |

Depois de gerado e verificado, o `package.json` do projeto é a fonte da verdade para versões.
Não sugerir upgrades ou libs alternativas sem aprovação explícita do responsável.
