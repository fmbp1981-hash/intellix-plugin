## Regras de Desenvolvimento

1. **TypeScript strict** em todos os projetos — zero `any`
2. **Mobile-first** obrigatório em frontend
3. **RLS ativo** em todas as tabelas Supabase
4. **Variáveis de ambiente** para credenciais — nunca hardcode
5. **Validação com Zod** em todas as entradas de usuário e APIs
6. **Commits semânticos** — feat:, fix:, docs:, refactor:, chore:
7. Antes de criar arquivo novo, verifique se já existe algo similar

## Formato de Documentação

- **Markdown** — todo artefato consumido por IA ou por desenvolvedor em IDE (SKILL.md, CLAUDE.md, specs, PRDs, planos, memory files). HTML aqui = desperdício de tokens.
- **HTML** — entregas visuais a clientes e stakeholders fora do ecossistema de dev: handoff docs, design system showcase, relatório de code audit para cliente, proposta técnica comercial. Templates em `intellix-plugin/intellix-templates/delivery-templates/`.

## Stack Padrão IntelliX.AI

| Camada | Tecnologia |
|--------|-----------|
| Framework | Next.js 16 (App Router) |
| Linguagem | TypeScript strict |
| Estilo | Tailwind CSS + Shadcn/UI |
| Animações | Framer Motion |
| Banco de dados | Supabase (PostgreSQL + Auth + RLS) |
| Validação | Zod + React Hook Form |
| WhatsApp | Evolution API |
| Automação | n8n |
| Agentes | GPT Maker |
| Deploy | Cloudflare (Workers/Pages) — trocado de Vercel em 2026-09-07, ver `WORKFLOW-SPINE-VS-ORBIT.md` |

## MCP Tools Disponíveis

- `perplexity_search` — busca web rápida
- `perplexity_ask` — perguntas com contexto web
- `perplexity_research` — pesquisa aprofundada
- `perplexity_reason` — raciocínio com dados externos
- `n8n_*` — criar/gerenciar workflows n8n
