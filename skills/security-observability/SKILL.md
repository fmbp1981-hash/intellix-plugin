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

Auditoria de segurança e configuração de observabilidade. Auto-aplica o nível correto
baseado no tipo de projeto — sem overhead para projetos simples, sem brechas para sistemas críticos.

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
> execução da skill `lgpd-compliance` em paralelo com esta fase.
> Invoque: `Skill("lgpd-compliance")`

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

### 1 — Checklist OWASP Top 10 (Next.js + Supabase)

| Vulnerabilidade | Verificação | Status |
|----------------|-------------|--------|
| A01 Broken Access Control | RLS ativo em TODA tabela Supabase | [ ] |
| A01 Broken Access Control | Nenhum `service_role` key no client | [ ] |
| A02 Cryptographic Failures | Dados sensíveis nunca em localStorage | [ ] |
| A02 Cryptographic Failures | HTTPS enforced, HSTS configurado | [ ] |
| A03 Injection | Nunca concatenar SQL — usar Supabase query builder | [ ] |
| A03 Injection | Validação Zod em TODA entrada de usuário | [ ] |
| A05 Security Misconfiguration | Sem `.env` commitado | [ ] |
| A05 Security Misconfiguration | CORS configurado explicitamente | [ ] |
| A06 Vulnerable Components | `npm audit` executado, zero high/critical | [ ] |
| A07 Auth Failures | PKCE habilitado no Supabase Auth | [ ] |
| A07 Auth Failures | Rate limiting em login/register | [ ] |
| A09 Logging Failures | Logs sem PII (email, CPF, senha) | [ ] |
| A09 Logging Failures | Audit log para ações críticas | [ ] |

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
- [ ] OWASP Top 10 checklist 100% verde
- [ ] Rate limiting em endpoints críticos (auth, webhook, API pública)
- [ ] Logging estruturado sem PII
- [ ] Audit log para ações destrutivas
- [ ] Zod validando 100% das entradas externas
- [ ] CSP configurado e testado
- [ ] `npm audit` zero high/critical
- [ ] Core Web Vitals medidos (LCP < 2.5s, INP < 200ms, CLS < 0.1)

---

## Handover para Fase 07 (Test E2E)

> "Security & Observability configurados (Nível [BÁSICO/MÉDIO/COMPLETO]).
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
