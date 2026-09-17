## Context7 — Documentação de Libs em Tempo Real (OBRIGATÓRIO)

Context7 é um MCP server ativo que injeta documentação **atual e versionada** de
bibliotecas diretamente no contexto. Resolve o problema de docs desatualizadas no
treinamento do modelo (Next.js 16, Tailwind v4, Supabase, etc. mudam rápido).

**REGRA:** Antes de escrever código que usa qualquer API de biblioteca externa,
use Context7 para obter a documentação atual. Nunca assuma que sabe a API correta
sem verificar — versões mudam silenciosamente.

### Quando usar Context7 (obrigatório)

- Qualquer chamada de API de biblioteca que pode ter mudado (Supabase, Next.js, Tailwind, shadcn/ui, Zod, TanStack Query, Framer Motion, etc.)
- Ao instalar ou atualizar um pacote — verificar breaking changes
- Quando houver dúvida sobre a assinatura de uma função ou hook
- Ao configurar uma nova integração (Evolution API, n8n, Anthropic SDK, OpenAI)
- Para confirmar comportamento de features recentes (Next.js App Router, Supabase RLS helpers, etc.)

### Como usar (ferramentas MCP disponíveis)

```
Passo 1 — Resolver o ID da biblioteca:
  Tool: resolve-library-id
  Input: { libraryName: "nextjs" }
  Output: "/vercel/next.js"

Passo 2 — Buscar documentação atual:
  Tool: query-docs
  Input: { context7CompatibleLibraryID: "/vercel/next.js", query: "app router server actions" }
  Output: Documentação atual, versionada
```

**Shortcut:** Se já conhece o ID, use direto: `use library /supabase/supabase`

### Stack IntelliX — IDs frequentes

| Biblioteca | ID Context7 |
|-----------|-------------|
| Next.js | `/vercel/next.js` |
| Supabase | `/supabase/supabase` |
| Tailwind CSS | `/tailwindlabs/tailwindcss` |
| shadcn/ui | `/shadcn-ui/ui` |
| Zod | `/colinhacks/zod` |
| TanStack Query | `/tanstack/query` |
| Framer Motion | `/framer/motion` |
| React Hook Form | `/react-hook-form/react-hook-form` |
| Anthropic SDK | `/anthropics/anthropic-sdk-typescript` |

### Divisão de responsabilidades: Context7 vs Perplexity

| Quando usar | Ferramenta |
|-------------|-----------|
| API de biblioteca, assinatura de função, configuração de pacote | **Context7** (`query-docs`) |
| Versão atual de um pacote no npm | **Perplexity** (`perplexity_search`) |
| Preços, planos, limites de serviços externos | **Perplexity** (`perplexity_search`) |
| Bugs, erros com solução da comunidade | **Perplexity** (`perplexity_ask`) |
| Análise de mercado, tendências | **Perplexity** (`perplexity_research`) |
| Documentação de breaking changes de uma versão | **Ambos** |
