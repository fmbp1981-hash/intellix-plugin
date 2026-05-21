---
name: deploy
description: >
  Use esta skill sempre que o usuário mencionar: deploy, Vercel, DNS,
  domínio, Cloudflare, variáveis de ambiente, produção, release, publicar,
  "colocar no ar", configurar domínio, "está pronto para produção".
  Esta é a Fase 06 do fluxo IntelliX — só executar após test-e2e passar.
disable-model-invocation: true
---

# Fase 06 — Deploy Checklist

Checklist completo de deploy IntelliX. Esta skill é de invocação manual apenas
(`disable-model-invocation: true`) — você controla quando fazer o deploy.

## Passo 0 — Pipeline CI/CD `ci-cd-and-automation` (obrigatório, uma vez por projeto)

**Invoke:** `Skill("ci-cd-and-automation")`

Antes do primeiro deploy em produção, garantir que o pipeline está configurado:
- GitHub Actions com quality gates: lint → typecheck → testes → build → segurança
- Branch protection em `main` (PRs obrigatórios, status checks bloqueadores)
- Preview deploy automático por PR (Vercel)
- Dependabot/Renovate para atualizações de dependências

> Este passo é executado **uma vez** no início do projeto ou ao detectar que não existe `.github/workflows/`. Em deploys subsequentes, verificar apenas se o pipeline está passando.

---

## Pré-requisitos obrigatórios
- [ ] Fase 05 (test-e2e) concluída com 100% dos testes passando
- [ ] Pipeline CI/CD configurado (Passo 0)
- [ ] `.intellix-phase` = `deploy`
- [ ] Sem `console.log` ou código de debug em produção

## Checklist Vercel

### Variáveis de ambiente
```bash
# Mínimo obrigatório para todo projeto IntelliX
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=      # Nunca expor no cliente
NEXT_PUBLIC_APP_URL=            # URL de produção (para redirects)

# Se houver agentes
ANTHROPIC_API_KEY=
N8N_WEBHOOK_URL=                # Se integrado ao n8n
EVOLUTION_API_URL=              # Se integrado ao WhatsApp
EVOLUTION_API_KEY=
```

### Configurações Vercel
- [ ] Root directory: `./` (ou pasta do app se monorepo)
- [ ] Framework: Next.js (auto-detectado)
- [ ] Node version: 20.x
- [ ] Build command: `npm run build`
- [ ] Output: `.next`

## Checklist DNS (Cloudflare)

```
Tipo    Nome              Valor                   Proxy
A       @                 76.76.21.21             ✅ (Vercel IP)
CNAME   www               cname.vercel-dns.com    ✅
```

**Após adicionar DNS:**
1. Vercel → Project → Settings → Domains → Add domain
2. Aguardar propagação (5-30 min com Cloudflare)
3. Verificar SSL/TLS no Cloudflare: modo "Full (strict)"

## Health check pós-deploy

```bash
# Verificar se o site está no ar
curl -I https://seu-dominio.com.br

# Verificar variáveis de ambiente (via Vercel CLI)
vercel env ls

# Logs de produção
vercel logs --follow
```

## Checklist final
- [ ] Site abre em https (sem aviso de SSL)
- [ ] Login/auth funcionando em produção
- [ ] Supabase conectado (testar uma operação de leitura)
- [ ] Domínio customizado funcionando (www + raiz)
- [ ] Vercel Analytics habilitado (opcional mas recomendado)

## CI/CD com GitHub Actions

Automatize testes e deploy com este workflow padrão IntelliX:

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npx tsc --noEmit

      - name: Lint
        run: npm run lint

      - name: Unit tests
        run: npm run test
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}

  e2e:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run test:e2e
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}
          PLAYWRIGHT_BASE_URL: ${{ secrets.STAGING_URL }}
```

### Configuração de Segredos no GitHub

```bash
# Adicionar via GitHub CLI
gh secret set NEXT_PUBLIC_SUPABASE_URL --body "https://xxx.supabase.co"
gh secret set NEXT_PUBLIC_SUPABASE_ANON_KEY --body "eyJ..."
gh secret set SUPABASE_SERVICE_ROLE_KEY --body "eyJ..."
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..."
```

### Branch Protection Rules (obrigatório para main)

```
Configurar em: GitHub → Settings → Branches → Add rule → main

☑ Require a pull request before merging
☑ Require status checks to pass (selecionar: test, build)
☑ Require branches to be up to date before merging
☑ Do not allow bypassing the above settings
```

### Estratégia de Ambientes

```
develop branch → preview deploy automático (Vercel Preview)
main branch    → produção (Vercel Production)
feature/*      → preview deploy por PR
```

```yaml
# vercel.json — configurar ambientes
{
  "github": {
    "enabled": true,
    "autoAlias": false
  },
  "env": {
    "NODE_ENV": "production"
  }
}
```

### `package.json` — Scripts obrigatórios

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "type-check": "tsc --noEmit"
  }
}
```

---

## DevOps — Operação em Produção

O deploy é apenas o começo. Um sistema de produção profissional requer:

### Estratégia de Ambientes

```
develop branch  → Vercel Preview (staging automático)
feature/*       → Vercel Preview por PR
main branch     → Vercel Production
```

```
.env.local          → desenvolvimento local (não commitar)
.env.staging        → staging (Vercel Preview env vars)
.env.production     → produção (Vercel Production env vars)
```

**Regra de ouro:** staging deve ser idêntico a produção em configuração.
Nunca teste em produção o que não testou em staging.

---

### Database Migrations em CI

```yaml
# Adicionar ao .github/workflows/ci.yml
  migrate:
    name: Database Migration
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
        with:
          version: latest
      - name: Apply migrations
        run: supabase db push --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

```bash
# Fluxo de migrations IntelliX
# 1. Criar migration local
supabase migration new add_contacts_index

# 2. Editar o arquivo gerado em supabase/migrations/
# 3. Testar localmente
supabase db reset

# 4. Commitar e fazer PR
# 5. CI aplica automaticamente ao fazer merge em main
```

---

### Rollback Procedure

**Rollback de código (Vercel):**
```bash
# Via Vercel CLI — voltar para deployment anterior
vercel rollback [deployment-url]

# Via Dashboard: Vercel → Project → Deployments → Promote previous deployment
```

**Rollback de migration (Supabase):**
```sql
-- Toda migration deve ter rollback documentado
-- supabase/migrations/[timestamp]_add_feature.sql

-- UP (aplicar)
ALTER TABLE contacts ADD COLUMN score INT DEFAULT 0;
CREATE INDEX idx_contacts_score ON contacts(score);

-- DOWN (reverter — documentar como comentário)
-- ALTER TABLE contacts DROP COLUMN score;
-- DROP INDEX idx_contacts_score;
```

```bash
# Aplicar rollback de migration manualmente
supabase db execute --file supabase/migrations/rollback_[timestamp].sql
```

---

### Monitoramento Contínuo

```typescript
// src/app/api/health/route.ts — Health check endpoint
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET() {
  const checks = {
    status: 'ok' as 'ok' | 'degraded' | 'down',
    timestamp: new Date().toISOString(),
    services: {
      database: 'unknown' as 'ok' | 'error',
      auth: 'unknown' as 'ok' | 'error',
    }
  }

  try {
    const supabase = createClient()
    await supabase.from('health_check').select('id').limit(1)
    checks.services.database = 'ok'
  } catch {
    checks.services.database = 'error'
    checks.status = 'degraded'
  }

  const status = checks.status === 'ok' ? 200 : 503
  return NextResponse.json(checks, { status })
}
```

```yaml
# Uptime monitoring — adicionar ao Vercel Cron Jobs ou serviço externo
# vercel.json
{
  "crons": [{
    "path": "/api/health",
    "schedule": "*/5 * * * *"
  }]
}
```

---

### Gestão de Secrets em Produção

```bash
# Rotação de secrets — nunca hardcode, sempre variáveis
# Verificar onde cada secret é usado antes de rotacionar
grep -r "ANTHROPIC_API_KEY\|SUPABASE_SERVICE_ROLE" src/ --include="*.ts"

# Rotacionar via Vercel CLI
vercel env rm ANTHROPIC_API_KEY production
vercel env add ANTHROPIC_API_KEY production

# Verificar secrets expostos acidentalmente
git log --all --full-history -- "*.env*"
git log --all -p | grep -E "sk-ant|eyJ[a-zA-Z0-9]"
```

---

### Feature Flags (Para Releases Graduais)

```typescript
// src/lib/feature-flags.ts
// Solução simples via env vars (sem dependência externa)
export const featureFlags = {
  newDashboard: process.env.NEXT_PUBLIC_FF_NEW_DASHBOARD === 'true',
  aiSuggestions: process.env.NEXT_PUBLIC_FF_AI_SUGGESTIONS === 'true',
  betaAnalytics: process.env.NEXT_PUBLIC_FF_BETA_ANALYTICS === 'true',
} as const

// Uso:
// if (featureFlags.newDashboard) { return <NewDashboard /> }
// return <OldDashboard />

// Para habilitar gradualmente:
// Vercel → Environment Variables → NEXT_PUBLIC_FF_NEW_DASHBOARD = true
// Deploy apenas para Preview primeiro, depois Produção
```

---

### Runbook de Incidentes

Documente em `docs/runbook.md`:

```markdown
# Runbook de Incidentes — [Nome do Projeto]

## Sistema fora do ar (503)
1. Verificar Vercel Status: status.vercel.com
2. Verificar Supabase Status: status.supabase.com
3. Verificar último deployment: `vercel ls`
4. Rollback se último deploy causou: `vercel rollback`
5. Verificar logs: `vercel logs --follow`

## Erro de autenticação em massa
1. Verificar Supabase Auth logs no dashboard
2. Verificar se ANON_KEY expirou ou foi rotacionada
3. Verificar middleware.ts — possível mudança recente

## Query lenta / timeout de banco
1. Supabase Dashboard → Database → Query Performance
2. Identificar query com alto execution time
3. Verificar se índice está faltando
4. Aplicar EXPLAIN ANALYZE na query suspeita

## Alerta Sentry — erro novo em produção
1. Verificar stack trace no Sentry
2. Identificar commit que introduziu o erro: `git log --oneline -10`
3. Hotfix em branch separado + PR urgente
4. Se crítico: rollback imediato + fix depois
```

---

## Passo Final — Launch `shipping-and-launch` (deploy em produção)

**Quando invocar:** deploy para produção real (não preview). **Não invocar** em deploys de preview/staging.

**Invoke:** `Skill("shipping-and-launch")`

Garante que o go-live é reversível, observável e incremental:
- Pre-launch checklist: code quality, security, performance, acessibilidade, infra, docs
- Feature flags: código chega antes da feature ser visível (`NEXT_PUBLIC_FF_*`)
- Staged rollout: 5% → 25% → 50% → 100% com métricas em cada etapa
- Monitoramento da 1ª hora: error rate, latência, business metrics
- Rollback plan documentado: triggers + passos exatos

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Configurar pipeline CI/CD (uma vez por projeto) | `ci-cd-and-automation` |
| Go-live em produção com staged rollout | `shipping-and-launch` |
| Boas práticas de performance e otimização Vercel + Next.js | `vercel-react-best-practices` |
| Verificação sistemática antes de declarar deploy pronto | `superpowers:verification-before-completion` |
| Finalizar branch e criar PR para main | `superpowers:finishing-a-development-branch` |
| Diagnosticar incidentes em produção | `superpowers:systematic-debugging` |

---

## Handover para Fase 07
> "Deploy concluído. Sistema em produção. Próxima fase: **intellix:handoff** para documentação final."

Atualize `.intellix-phase` para `done`.
