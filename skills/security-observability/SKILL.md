---
name: security-observability
description: >
  Use esta skill antes do deploy em qualquer projeto com autenticação, dados de usuário,
  APIs públicas ou sistema em produção. Auto-detecta a natureza do projeto e aplica
  apenas o checklist relevante — landing page simples recebe verificação básica, SaaS/CRM
  recebe auditoria completa. Esta é a Fase 06 do fluxo IntelliX — executada após testes
  (Fase 07) e antes do deploy (Fase 08). Também ativa quando o usuário mencionar:
  segurança, vulnerabilidade, rate limiting, logs, monitoramento, Sentry, auditoria,
  LGPD, OWASP, auth token, secrets, observabilidade.
user-invocable: true
---

# Fase 06 — Security & Observability

Configuração de observabilidade e do detalhe técnico de segurança específico da stack
Next.js/Supabase (rate limiting, logging, CSP, LLM/Agentic, Sentry) que
`devsecops:security-baseline` declara não duplicar. Auto-aplica o nível correto baseado
no tipo de projeto — sem overhead para projetos simples, sem brechas para sistemas
críticos. **O gate de segurança em si (RLS, secrets, auth, severidade, autorização de
deploy) é sempre do devsecops — ver Nível COMPLETO, item 1.**

---

## Auto-Detecção de Nível

Antes de qualquer checklist, classifique o projeto:

```
Projeto tem autenticação (Supabase Auth, NextAuth, etc.)? → Nível COMPLETO
Projeto tem dados de usuário ou pagamento? → Nível COMPLETO
Projeto é API pública (webhooks, route handlers públicos)? → Nível COMPLETO
Projeto é SaaS/CRM com múltiplos usuários? → Nível COMPLETO
Projeto é landing page estática sem auth? → Nível BÁSICO
Projeto é dashboard interno sem dados sensíveis? → Nível MÉDIO
```

> **LGPD:** Todo projeto que coleta dados de pessoas físicas brasileiras requer
> execução da skill `devsecops:lgpd-compliance` em paralelo com esta fase — é a
> única fonte de verdade de LGPD (mapa de dados, bases legais, tabelas Supabase,
> direitos dos titulares, incidentes, sigilo fiscal). Não existe mais uma versão
> resumida no plugin `intellix` — foi arquivada em 2026-09-07 por ser subconjunto
> redundante desta.
> Invoque: `Skill("devsecops:lgpd-compliance")`

---

## Nível BÁSICO (Landing Pages, Sites Estáticos)

- [ ] Sem variáveis de ambiente expostas no client (`NEXT_PUBLIC_` com valores sensíveis)
- [ ] `next.config.ts` com headers de segurança básicos
- [ ] Sem `console.log` com dados em produção
- [ ] HTTPS ativo (Vercel garante automaticamente)

```typescript
// next.config.ts — headers de segurança básicos
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ]
  },
}
```

---

## Nível MÉDIO (Dashboards Internos, Apps com Auth Simples)

Inclui Nível BÁSICO mais:

### Auth Security
- [ ] Tokens JWT com expiração configurada (não infinitos)
- [ ] Redirect após login não aceita URLs externas
- [ ] Session timeout configurado
- [ ] Middleware protegendo rotas autenticadas

```typescript
// src/middleware.ts — proteção de rotas
import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const response = NextResponse.next()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    { cookies: { /* cookie handlers */ } }
  )

  const { data: { session } } = await supabase.auth.getSession()

  const protectedRoutes = ['/dashboard', '/api/protected']
  const isProtected = protectedRoutes.some(r => request.nextUrl.pathname.startsWith(r))

  if (isProtected && !session) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

### Basic Error Tracking
- [ ] Sentry instalado e configurado

```bash
npx @sentry/wizard@latest -i nextjs
```

```typescript
// sentry.client.config.ts
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
  // Não capturar dados sensíveis
  beforeSend(event) {
    if (event.request?.cookies) delete event.request.cookies
    return event
  },
})
```

---

## Nível COMPLETO (SaaS, CRM, APIs Públicas, Sistemas com Dados Sensíveis)

Inclui Níveis BÁSICO + MÉDIO mais:

### 1 — Security Gate (RLS, secrets, auth, LGPD, severidade, autorização)

> **Não reproduza aqui um checklist OWASP paralelo.** `devsecops:security-baseline` e
> `devsecops:security-gate` são a única fonte de verdade para RLS, `service_role`,
> secrets, autenticação/autorização, classificação de severidade (CRITICAL/HIGH/MEDIUM)
> e autorização explícita de deploy — incluindo o fleet de 5 revisores somente-leitura
> (`security-reviewer`, `privacy-lgpd-reviewer`, `multi-tenant-reviewer`,
> `database-architect`, `architect-reviewer`).

Antes de prosseguir com os itens técnicos abaixo, execute nesta ordem:
1. `Skill("devsecops:security-baseline")` — metodologia, threat model, fleet de revisores.
2. `Skill("devsecops:security-gate")` — gate mínimo de pré-deploy (~30 itens), resultado
   `SECURITY_GATE: PASS|FAIL`.

Esta skill assume esse gate já executado e cobre apenas o que `security-baseline`
declara **não** duplicar: OWASP LLM/Agentic, rate limiting, logging estruturado, audit
log, CSP, Sentry e Core Web Vitals — itens 2 a 10 abaixo.

### 2 — Rate Limiting

```typescript
// src/lib/rate-limit.ts
// Opção A: Usando Upstash Redis (recomendado para Vercel)
import { Ratelimit } from '@upstash/ratelimit'
import { Redis } from '@upstash/redis'

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, '10 s'),
  analytics: true,
})

export async function checkRateLimit(identifier: string) {
  const { success, limit, remaining, reset } = await ratelimit.limit(identifier)
  return { success, limit, remaining, reset }
}

// Opção B: In-memory simples (sem dependência externa, não funciona em serverless distribuído)
const requests = new Map<string, { count: number; resetAt: number }>()

export function checkRateLimitSimple(ip: string, maxRequests = 10, windowMs = 10000): boolean {
  const now = Date.now()
  const entry = requests.get(ip)

  if (!entry || now > entry.resetAt) {
    requests.set(ip, { count: 1, resetAt: now + windowMs })
    return true
  }

  if (entry.count >= maxRequests) return false
  entry.count++
  return true
}
```

```typescript
// Aplicar em route handlers críticos
// src/app/api/auth/route.ts
import { checkRateLimit } from '@/lib/rate-limit'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const ip = req.headers.get('x-forwarded-for') ?? 'anonymous'
  const { success } = await checkRateLimit(`auth:${ip}`)

  if (!success) {
    return NextResponse.json(
      { error: 'Too many requests' },
      { status: 429, headers: { 'Retry-After': '10' } }
    )
  }

  // ... handler logic
}
```

### 3 — Logging Estruturado

```typescript
// src/lib/logger.ts
type LogLevel = 'info' | 'warn' | 'error' | 'debug'

interface LogEntry {
  level: LogLevel
  message: string
  timestamp: string
  userId?: string
  action?: string
  metadata?: Record<string, unknown>
}

// Sanitizar dados antes de logar
function sanitize(data: Record<string, unknown>): Record<string, unknown> {
  const SENSITIVE_KEYS = ['password', 'token', 'secret', 'cpf', 'email', 'phone']
  return Object.fromEntries(
    Object.entries(data).map(([k, v]) =>
      SENSITIVE_KEYS.some(s => k.toLowerCase().includes(s)) ? [k, '[REDACTED]'] : [k, v]
    )
  )
}

export const logger = {
  info: (message: string, meta?: Omit<LogEntry, 'level' | 'message' | 'timestamp'>) =>
    log('info', message, meta),
  warn: (message: string, meta?: Omit<LogEntry, 'level' | 'message' | 'timestamp'>) =>
    log('warn', message, meta),
  error: (message: string, meta?: Omit<LogEntry, 'level' | 'message' | 'timestamp'>) =>
    log('error', message, meta),
}

function log(level: LogLevel, message: string, meta?: Record<string, unknown>) {
  const entry: LogEntry = {
    level,
    message,
    timestamp: new Date().toISOString(),
    ...(meta ? sanitize(meta) : {}),
  }
  // Em produção: enviar para Sentry/Datadog/Logtail
  // Em dev: console colorido
  if (process.env.NODE_ENV === 'production') {
    console.log(JSON.stringify(entry))
  } else {
    console.log(`[${level.toUpperCase()}] ${message}`, meta ?? '')
  }
}
```

### 4 — Audit Log para Ações Críticas

```sql
-- supabase/migrations/[timestamp]_audit_log.sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  action TEXT NOT NULL,           -- 'contact.created', 'user.deleted', etc.
  resource_type TEXT NOT NULL,    -- 'contact', 'user', 'payment'
  resource_id TEXT,
  ip_address TEXT,
  user_agent TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Admins podem ler, ninguém escreve diretamente (via service role)
CREATE POLICY "admins_read_audit" ON audit_log
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM user_roles
      WHERE user_id = auth.uid() AND role = 'admin'
    )
  );
```

```typescript
// src/lib/audit.ts
import { createClient } from '@/lib/supabase/server'

export async function auditLog(params: {
  userId: string
  action: string
  resourceType: string
  resourceId?: string
  metadata?: Record<string, unknown>
}) {
  const supabase = createClient()
  await supabase.from('audit_log').insert({
    user_id: params.userId,
    action: params.action,
    resource_type: params.resourceType,
    resource_id: params.resourceId,
    metadata: params.metadata,
  })
}

// Uso: await auditLog({ userId, action: 'contact.deleted', resourceType: 'contact', resourceId: id })
```

### 5 — Validação de Inputs (Zod)

```typescript
// src/lib/validations/contact.ts
import { z } from 'zod'

export const createContactSchema = z.object({
  name: z.string().min(1, 'Nome obrigatório').max(100),
  phone: z.string().regex(/^\+?[\d\s\-()]{8,20}$/, 'Telefone inválido').optional(),
  email: z.string().email('Email inválido').optional(),
  metadata: z.record(z.unknown()).optional().default({}),
})

export type CreateContactInput = z.infer<typeof createContactSchema>

// Em route handlers:
// const result = createContactSchema.safeParse(await req.json())
// if (!result.success) return NextResponse.json({ error: result.error.flatten() }, { status: 400 })
```

### 6 — Content Security Policy

```typescript
// next.config.ts — CSP completo
const ContentSecurityPolicy = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline' *.vercel.app *.sentry.io;
  style-src 'self' 'unsafe-inline';
  img-src * blob: data:;
  media-src 'none';
  connect-src * *.supabase.co *.sentry.io;
  font-src 'self' data:;
`.replace(/\n/g, '')

export default {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'Content-Security-Policy', value: ContentSecurityPolicy },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
        ],
      },
    ]
  },
}
```

### 7 — Performance & Core Web Vitals

```bash
# Verificar bundle size
npx @next/bundle-analyzer

# Core Web Vitals targets IntelliX
# LCP (Largest Contentful Paint): < 2.5s
# INP (Interaction to Next Paint): < 200ms
# CLS (Cumulative Layout Shift): < 0.1
```

```typescript
// src/app/layout.tsx — font loading sem layout shift
import { Inter } from 'next/font/google'  // substitua por fonte escolhida no design system

const displayFont = localFont({
  src: '../public/fonts/[chose-display-font].woff2',
  variable: '--font-display',
  display: 'swap',  // evita FOIT
  preload: true,
})
```

### 8 — Auditoria de Dependências

```bash
# Rodar antes de qualquer deploy
npm audit --audit-level=high

# Zero vulnerabilidades high/critical permitidas
# Se houver: npm audit fix ou atualizar manualmente
```

### 9 — Segurança LLM (OWASP LLM Top 10 2025)

> Executar quando o projeto tem chamadas a LLMs (OpenAI, Anthropic, etc.)

| Risco OWASP LLM | Verificação | Status |
|----------------|-------------|--------|
| LLM01 Prompt Injection | Pré-prompt filter ativo — input sanitizado antes de enviar ao modelo | [ ] |
| LLM02 Insecure Output Handling | Pós-output validator ativo — output sanitizado antes de exibir/executar | [ ] |
| LLM06 Excessive Agency | Agentes têm allowlist de tools — acesso apenas ao necessário | [ ] |
| LLM08 Vector/Embedding Weakness | RAG com filtragem por entitlement (usuário só recupera o que tem permissão) | [ ] |
| LLM09 Misinformation | Validador de output verificável implementado | [ ] |
| LLM10 Unbounded Consumption | Rate limit por usuário/tenant + limite de tokens por request | [ ] |

> **Fonte canônica:** o código completo de `src/lib/ai/guardrails.ts` (Camadas 1 e 4:
> `prePromptFilter` + `postOutputValidator`) vive em
> `intellix-templates/references-template/security.md` (gerado como `references/security.md`
> no projeto). Não duplique aqui — leia de lá antes de implementar ou revisar chamadas LLM.

**Regra de Conta LLM — sem exceção:**

| Provedor | Produto seguro | Proibido com dados de clientes |
|----------|---------------|-------------------------------|
| OpenAI | API (platform.openai.com) | ChatGPT Free/Plus/Pro/Team |
| Anthropic | API (console.anthropic.com) | Claude.ai Free/Pro/Max |
| Azure OpenAI | Qualquer tier | — |

### 10 — Segurança de Agentes (OWASP Agentic Top 10 2026)

> Executar quando o projeto tem agentes autônomos (n8n multi-step, GPT Maker com tools, agentes Anthropic/OpenAI)

| Risco OWASP Agêntico | Verificação | Status |
|---------------------|-------------|--------|
| A01 Privilege Escalation | Cada agente tem allowlist de tools — nenhum herda privilégios de outro | [ ] |
| A02 Context Poisoning | Memória/contexto persistente sanitizado antes de gravar | [ ] |
| A03 Insecure Tool Use | Tools com ações irreversíveis têm step de confirmação humana | [ ] |
| A05 Resource Overuse | Timeout + max_tokens + max_iterations configurados | [ ] |
| A07 Human Manipulation | Output para o usuário validado — sem instrução de ação financeira sem confirmação | [ ] |
| A09 Cascading Failures | Circuit breaker em workflows multi-step | [ ] |

**As 4 Perguntas Obrigatórias Antes de Colocar Agente em Produção**

> Regra IntelliX: Se qualquer resposta for "não sei" → o problema NÃO é técnico, é de processo.
> Reverter ao `/plan` antes de avançar.

1. **Quais dados (incluindo PII) entram no agente e qual LLM os processa?**
   → Mapeado + base legal LGPD documentada + conta API comercial confirmada

2. **Qual o critério objetivo para "essa resposta é boa"? Existe validador implementado?**
   → Não é feeling — é função que retorna true/false com threshold definido

3. **Quem valida o output antes de impactar usuário ou sistema externo?**
   → Humano (human-in-the-loop) ou validador automático com fallback definido

4. **Em workflows multi-step: como valido estados intermediários?**
   → Cada step tem saída verificável + rollback se falhar

```typescript
// src/lib/ai/agent-guardrails.ts

// Menor privilégio: allowlist explícita de tools por agente
const AGENT_TOOL_ALLOWLIST: Record<string, string[]> = {
  'sdr-agent': ['search_contacts', 'send_whatsapp', 'update_lead_status'],
  'analyst-agent': ['read_reports', 'generate_chart'],
  // Sem wildcard — cada agente lista APENAS suas tools
}

// Ação irreversível: exige confirmação antes de executar
export async function executeIrreversibleAction(
  agentId: string,
  action: string,
  payload: unknown,
  requireConfirmation = true
) {
  if (requireConfirmation) {
    // Em produção: criar pending_action e aguardar aprovação humana
    // Nunca executar delete, envio de mensagem, pagamento sem aprovação
    throw new Error(`HUMAN_REVIEW_REQUIRED: ${action}`)
  }
  // ... execução
}
```

### 11 — Pipeline DevSecOps CI/CD

> Configurar uma vez por repositório. Jobs rodando em todo PR.

> **Fonte canônica:** o YAML completo de `.github/workflows/security.yml`
> (Gitleaks + Semgrep + Trivy) vive em
> `intellix-templates/references-template/security.md` (gerado como `references/security.md`
> no projeto). Não duplique aqui — copie de lá ao configurar o pipeline.

**Regra de bloqueio:** PRs com vulnerabilidade CRITICAL não fazem merge.
HIGH exige dispensa documentada com justificativa no PR.

**Gestão de Credenciais por Ambiente:**

| Ambiente | Onde guardar | Nunca fazer |
|----------|-------------|-------------|
| Local | `.env.local` (no .gitignore) | Commitar qualquer `.env` |
| CI/CD | GitHub Encrypted Secrets | Printar secrets em logs |
| Produção (Vercel) | Vercel Environment Variables | Prefixar com `NEXT_PUBLIC_` |
| n8n self-hosted | n8n Credentials (criptografadas) | Deixar `N8N_ENCRYPTION_KEY` vazio |
| Dados sensíveis por tenant | Supabase Vault (pgcrypto) | Armazenar em tabela sem criptografia |

---

## Checklist de Conclusão

**Nível Básico:**
- [ ] Headers de segurança no `next.config.ts`
- [ ] Sem secrets no client-side

**Nível Médio (+ básico):**
- [ ] middleware.ts protegendo rotas autenticadas
- [ ] Sentry configurado com `beforeSend` sanitizando PII
- [ ] Auth tokens com expiração adequada

**Nível Completo (+ médio):**
- [ ] `devsecops:security-gate` executado com `SECURITY_GATE: PASS` (RLS, secrets, auth, LGPD, severidade, autorização)
- [ ] Rate limiting em endpoints críticos (auth, webhook, API pública)
- [ ] Logging estruturado sem PII
- [ ] Audit log para ações destrutivas
- [ ] Zod validando 100% das entradas externas
- [ ] CSP configurado e testado
- [ ] `npm audit` zero high/critical
- [ ] Core Web Vitals medidos (LCP < 2.5s, INP < 200ms, CLS < 0.1)

**LLM & IA (se o projeto usa LLMs):**
- [ ] Pré-prompt filter ativo (redação de PII + detecção de injection)
- [ ] Pós-output validator ativo (sanitização de output + detecção de vazamento)
- [ ] System prompt separado do user input por delimitadores explícitos
- [ ] Conta API comercial (não conta de consumo ChatGPT/Claude.ai)
- [ ] Rate limiting por usuário/tenant em chamadas LLM
- [ ] Limite de tokens por request definido (previne Denial of Wallet)

**Agentes (se o projeto tem agentes autônomos):**
- [ ] Allowlist de tools por agente definida
- [ ] 4 Perguntas de go-live respondidas com SIM
- [ ] Ações irreversíveis têm human-in-the-loop ou confirmação explícita
- [ ] Circuit breaker em workflows multi-step

**DevSecOps CI/CD (por repositório):**
- [ ] `.github/workflows/security.yml` configurado (Gitleaks + Semgrep + Trivy)
- [ ] Zero secrets detectados pelo Gitleaks
- [ ] Zero vulnerabilidades CRITICAL abertas
- [ ] Gestão de credenciais por ambiente seguindo tabela da Seção 11

**LGPD (se o projeto processa dados pessoais):**
- [ ] `devsecops:lgpd-compliance` executada em paralelo com esta skill
- [ ] Mapa de dados e base legal documentados
- [ ] Tabelas LGPD no schema (`consent_records`, `titular_requests`, `data_processing_log`)

---

## Handover para Fase 07 (Test E2E)

> "Security & Observability configurados (Nível [BÁSICO/MÉDIO/COMPLETO]).
> Security Gate (devsecops): [PASS/FAIL/não aplicável no nível BÁSICO ou MÉDIO].
> LGPD: [executada/não aplicável].
> LLM Security: [executada/não aplicável].
> Agentic Security: [executada/não aplicável].
> DevSecOps CI/CD: [configurado/não aplicável].
> Próxima fase: **intellix:test-e2e** para validação completa antes do deploy."

Atualize `.intellix-phase` para `test`.

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Verificação final antes de declarar pronto | `superpowers:verification-before-completion` |
| Debug sistemático de vulnerabilidade encontrada | `superpowers:systematic-debugging` |
| Boas práticas de performance React/Next.js | `vercel-react-best-practices` |
| Queries Supabase otimizadas e RLS avançado | `supabase-postgres-best-practices` |

---

## Armadilhas comuns
- ❌ `SUPABASE_SERVICE_ROLE_KEY` em variável `NEXT_PUBLIC_` → exposição total do banco
- ❌ RLS desabilitado em "tabelas internas" → toda tabela precisa de RLS
- ❌ `console.log(user)` em produção → vazar email/CPF nos logs do Vercel
- ❌ Rate limiting apenas no frontend → bypassável via curl/Postman
- ❌ Sentry sem `beforeSend` → capturar senhas e tokens nos logs de erro
