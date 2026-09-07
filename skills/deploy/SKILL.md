---
name: deploy
description: >
  Use esta skill sempre que o usuário mencionar: deploy, Cloudflare Workers, DNS,
  domínio, wrangler, variáveis de ambiente, produção, release, publicar,
  "colocar no ar", configurar domínio, "está pronto para produção".
  Esta é a Fase 08 do fluxo IntelliX — só executar após test-e2e passar.
  Stack de deploy padrão IntelliX desde 2026-09-07: Cloudflare Workers/Pages (não Vercel).
disable-model-invocation: true
---

# Fase 08 — Deploy Checklist

Checklist completo de deploy IntelliX. Esta skill é de invocação manual apenas
(`disable-model-invocation: true`) — você controla quando fazer o deploy.

## Passo 0 — Pipeline CI/CD `ci-cd-and-automation` (obrigatório, uma vez por projeto)

**Invoke:** `Skill("ci-cd-and-automation")`

Antes do primeiro deploy em produção, garantir que o pipeline está configurado:
- GitHub Actions com quality gates: lint → typecheck → testes → build → segurança
- Branch protection em `main` (PRs obrigatórios, status checks bloqueadores)
- Preview deploy automático por PR (Cloudflare Workers Preview URLs)
- Dependabot/Renovate para atualizações de dependências

> Este passo é executado **uma vez** no início do projeto ou ao detectar que não existe `.github/workflows/`. Em deploys subsequentes, verificar apenas se o pipeline está passando.

---

## Pré-requisitos obrigatórios
- [ ] Fase 07 (test-e2e) concluída com 100% dos testes passando
- [ ] Pipeline CI/CD configurado (Passo 0)
- [ ] `.intellix-phase` = `deploy`
- [ ] Sem `console.log` ou código de debug em produção

## Passo 1 — Adapter Next.js → Cloudflare Workers

> **Verificado via WebSearch/docs oficiais em 2026-09-07** — este espaço muda rápido,
> reverifique antes de cada projeto novo (não confie neste texto por mais de alguns meses).

Next.js não roda nativamente em Workers — precisa de um adapter que traduza o build.
Duas opções, ambas oficiais da Cloudflare:

| Adapter | Status | Quando usar |
|---|---|---|
| **`@opennextjs/cloudflare`** (OpenNext) | Maduro, estável | **Padrão IntelliX** — recomendado pela própria Cloudflare para manter aplicações |
| **`vinext`** (`@vinext/cloudflare`) | Experimental — lançado 2026, ~94% de cobertura da API do Next.js, builds 4.4x mais rápidos, bundles 57% menores | Direção oficial para projetos **novos**, mas ainda jovem — avaliar caso a caso, não usar sem reconfirmar maturidade |

**Setup padrão (`@opennextjs/cloudflare`):**
```bash
npm i @opennextjs/cloudflare@latest
npm i -D wrangler@latest
```

```jsonc
// wrangler.jsonc
{
  "name": "nome-do-projeto",
  "main": ".open-next/worker.js",
  "compatibility_date": "2026-09-07",   // usar a data atual do deploy
  "compatibility_flags": ["nodejs_compat"],
  "assets": { "directory": ".open-next/assets", "binding": "ASSETS" },
  "observability": { "enabled": true },
  "routes": [{ "pattern": "seu-dominio.com.br", "custom_domain": true }]
}
```

```typescript
// open-next.config.ts — mínimo obrigatório
export default { default: { override: { wrapper: "cloudflare-node" } } }
```

**Remover antes de migrar:** qualquer `export const runtime = 'edge'` em route handlers —
o adapter OpenNext não suporta a diretiva de edge runtime do Next.js.

## Checklist Cloudflare Workers

### Variáveis de ambiente e secrets
```bash
# Variáveis não-sensíveis: em wrangler.jsonc → "vars"
# Secrets (nunca em wrangler.jsonc, nunca commitados):
wrangler secret put SUPABASE_SERVICE_ROLE_KEY
wrangler secret put ANTHROPIC_API_KEY
wrangler secret put EVOLUTION_API_KEY

# Mínimo obrigatório para todo projeto IntelliX
NEXT_PUBLIC_SUPABASE_URL=        # var pública, pode ir em wrangler.jsonc
NEXT_PUBLIC_SUPABASE_ANON_KEY=   # var pública
SUPABASE_SERVICE_ROLE_KEY=       # SECRET — nunca em NEXT_PUBLIC_, nunca no client
NEXT_PUBLIC_APP_URL=             # URL de produção (para redirects)

# Se houver agentes
ANTHROPIC_API_KEY=               # SECRET
N8N_WEBHOOK_URL=                 # Se integrado ao n8n
EVOLUTION_API_URL=
EVOLUTION_API_KEY=               # SECRET
```

### Build e deploy
```bash
npx opennextjs-cloudflare build
npx opennextjs-cloudflare preview   # roda localmente no runtime de Workers antes de subir
npx opennextjs-cloudflare deploy    # publica o Worker
```

## Checklist de Domínio (Cloudflare Custom Domains)

Diferente de apontar DNS manualmente para um IP: um **Custom Domain** de Workers gerencia
DNS e certificado SSL automaticamente — não crie registro A/CNAME manual para ele.

1. `wrangler.jsonc` → `routes: [{ pattern: "seu-dominio.com.br", custom_domain: true }]`
   (ou Dashboard → Worker → Settings → Domains & Routes → Add → Custom Domain)
2. Cloudflare cria o registro DNS e emite o certificado automaticamente
3. Aguardar propagação (geralmente minutos, já dentro da própria rede Cloudflare)

## Health check pós-deploy

```bash
# Verificar se o site está no ar
curl -I https://seu-dominio.com.br

# Logs em tempo real
wrangler tail

# Histórico de deployments/versões
wrangler deployments list
```

## Checklist final
- [ ] Site abre em https (certificado emitido automaticamente pelo Custom Domain)
- [ ] Login/auth funcionando em produção
- [ ] Supabase conectado (testar uma operação de leitura)
- [ ] Domínio customizado funcionando (www + raiz)
- [ ] `observability: { enabled: true }` ativo no `wrangler.jsonc` (Workers Analytics/Logs)

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

  deploy:
    name: Deploy (Cloudflare Workers)
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
      - name: Build + Deploy via OpenNext
        run: npx opennextjs-cloudflare build && npx opennextjs-cloudflare deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
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
gh secret set CLOUDFLARE_API_TOKEN --body "..."      # token com permissão Workers Scripts:Edit
gh secret set CLOUDFLARE_ACCOUNT_ID --body "..."
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
develop branch → preview via `wrangler versions upload` (Preview URL, não recebe tráfego de produção)
main branch    → produção via `wrangler deploy` (ou opennextjs-cloudflare deploy)
feature/*      → preview por PR, mesma mecânica de versions upload
```

Ambientes nomeados ficam declarados em `wrangler.jsonc` (`env.staging`, `env.production`)
— cada um com seu próprio binding de recursos (D1/KV/R2) e secrets, evitando que staging
escreva acidentalmente no banco de produção.

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
    "type-check": "tsc --noEmit",
    "preview": "opennextjs-cloudflare build && opennextjs-cloudflare preview",
    "deploy": "opennextjs-cloudflare build && opennextjs-cloudflare deploy",
    "cf-typegen": "wrangler types --env-interface CloudflareEnv cloudflare-env.d.ts"
  }
}
```

---

## DevOps — Operação em Produção

O deploy é apenas o começo. Um sistema de produção profissional requer:

### Estratégia de Ambientes

```
develop branch  → wrangler versions upload (staging automático, Preview URL)
feature/*       → wrangler versions upload por PR
main branch     → wrangler deploy / opennextjs-cloudflare deploy (produção)
```

```
.env.local          → desenvolvimento local (não commitar)
.env.staging        → staging (secrets do env.staging em wrangler.jsonc)
.env.production     → produção (secrets do env.production em wrangler.jsonc)
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

**Rollback de código (Cloudflare Workers):**
```bash
# Reverte 100% do tráfego de produção para a última versão estável imediatamente
wrangler rollback [version-id]

# Sem version-id, o Wrangler usa a última versão que já esteve em 100% do tráfego
wrangler rollback

# Ver histórico de versões/deployments antes de decidir o rollback
wrangler deployments list
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

```jsonc
// wrangler.jsonc — Cron Trigger para uptime/health check periódico
{
  "triggers": {
    "crons": ["*/5 * * * *"]
  }
}
// O handler `scheduled()` do Worker chama /api/health internamente ou dispara
// um serviço externo de uptime monitoring (ex: Better Uptime, UptimeRobot).
```

---

### Gestão de Secrets em Produção

```bash
# Rotação de secrets — nunca hardcode, sempre variáveis
# Verificar onde cada secret é usado antes de rotacionar
grep -r "ANTHROPIC_API_KEY\|SUPABASE_SERVICE_ROLE" src/ --include="*.ts"

# Rotacionar via Wrangler CLI (sobrescreve o secret existente)
wrangler secret put ANTHROPIC_API_KEY

# Listar quais secrets existem (não mostra o valor)
wrangler secret list

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
// wrangler.jsonc → "vars": { "NEXT_PUBLIC_FF_NEW_DASHBOARD": "true" } no env.staging primeiro
// Deploy via `wrangler versions upload` (Preview) antes de promover para produção
```

---

### Runbook de Incidentes

Documente em `docs/runbook.md`:

```markdown
# Runbook de Incidentes — [Nome do Projeto]

## Sistema fora do ar (503)
1. Verificar Cloudflare Status: cloudflarestatus.com
2. Verificar Supabase Status: status.supabase.com
3. Verificar último deployment: `wrangler deployments list`
4. Rollback se último deploy causou: `wrangler rollback`
5. Verificar logs: `wrangler tail`

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
| Comandos Wrangler (deploy, secrets, tail, rollback, environments) | `wrangler` |
| Workers/Pages, D1, R2, KV, Cron Triggers, WAF | `cloudflare` |
| Boas práticas de performance React/Next.js (independe do host) | `vercel-react-best-practices` |
| Verificação sistemática antes de declarar deploy pronto | `superpowers:verification-before-completion` |
| Finalizar branch e criar PR para main | `superpowers:finishing-a-development-branch` |
| Diagnosticar incidentes em produção | `superpowers:systematic-debugging` |

---

## Handover para Fase 09
> "Deploy concluído. Sistema em produção. Próxima fase: **intellix:handoff** para documentação final."

Atualize `.intellix-phase` para `done`.
