# Operations — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§13–17](../MASTER-ARCHITECTURE.md).
> Consulte ao definir estratégia de testes, variáveis de ambiente, inicialização de projeto ou checklist de deploy.

## 14. Testes — Estratégia por Camada

| Camada | Framework | O que testar |
|--------|-----------|--------------|
| Funções puras / utils | Vitest | Formatadores, validações, cálculos |
| Services | Vitest | Lógica de negócio com DB real (não mock) |
| Route Handlers | Vitest | Autenticação, validação, respostas HTTP |
| Behaviors completos | Playwright | Happy path + edge cases + error cases |
| Fluxos E2E | Playwright | Jornadas completas do usuário |

**Cobertura mínima por behavior:**
- [ ] Happy path completo
- [ ] Edge case (dados limítrofes, valores nulos)
- [ ] Error case (não autenticado, não autorizado, DB error)

---

## 15. Variáveis de Ambiente

```bash
# .env.example — template obrigatório no repo

# Supabase (todo projeto)
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=      # NUNCA expor no cliente

# App
NEXT_PUBLIC_APP_URL=            # URL de produção

# IA (se usar agentes)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# WhatsApp (se integrar)
EVOLUTION_API_URL=
EVOLUTION_API_KEY=

# Automação (se usar n8n)
N8N_WEBHOOK_URL=
N8N_API_KEY=

# Email
RESEND_API_KEY=

# Cron
CRON_SECRET=
```

---

## 16. Inicialização de Projeto

### CLAUDE.md padrão por projeto

```markdown
# [Nome do Projeto]

## Contexto
[Descrição em 2-3 linhas do que o sistema faz]

## Stack
Next.js 15 App Router | TypeScript strict | Tailwind | Shadcn/UI | Supabase | Vercel

## Fase atual
[FASE] — ver .intellix-phase

## Arquitetura
Ler MASTER-ARCHITECTURE.md para todas as regras de arquitetura, padrões e workflow.

## Padrões obrigatórios
- TypeScript strict: NUNCA usar `any`
- Repository pattern: nunca acessar Supabase diretamente de componentes
- Commits: Conventional Commits (feat:, fix:, docs:, refactor:, chore:)
- Testes: toda feature nova precisa de testes cobrindo happy path + edge + error
- RLS: toda tabela Supabase com Row Level Security

## Integrações ativas
[listar: n8n / Evolution API / WhatsApp / Anthropic / etc]
```

### `.claude/settings.json` por projeto

```json
{
  "enabledPlugins": {
    "intellix@intellix-marketplace": true
  }
}
```

---

## 17. Deploy Checklist

### Pré-requisitos
- [ ] Testes E2E passando (100%)
- [ ] `tsc --noEmit` limpo
- [ ] Sem `console.log` em produção
- [ ] `.env.example` atualizado
- [ ] `.intellix-phase` = `deploy`

### Variáveis Vercel (mínimo obrigatório)
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
NEXT_PUBLIC_APP_URL
```

### DNS Cloudflare
```
Tipo   Nome   Valor                    Proxy
A      @      76.76.21.21              ON
CNAME  www    cname.vercel-dns.com     ON
```

**Configuração Cloudflare SSL:** modo "Full (strict)"

### Health check pós-deploy
```bash
curl -f https://[dominio]/api/health && echo "OK"
```
