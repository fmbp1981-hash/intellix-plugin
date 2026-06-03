---
name: architecture
description: >
  Use esta skill sempre que o usuário mencionar: arquitetura do sistema,
  schema de banco de dados, rotas da aplicação, design do sistema,
  VibeStack, estrutura de componentes, modelagem de dados, definir as
  tabelas, "como organizar o sistema", ERD, diagrama de arquitetura,
  ou qualquer decisão técnica de alto nível antes de implementar.
  Esta é a Fase 01 do fluxo IntelliX — executada após project-kickoff.
---

# Fase 01 — Architecture

Define a arquitetura completa do sistema: schema Supabase, rotas Next.js,
componentes principais e fluxo de dados. Tudo antes de escrever uma linha de código.

## Workflow

### Passo 1 — Schema Supabase

Para cada tabela, definir com RLS obrigatório:

```sql
-- Exemplo padrão IntelliX
CREATE TABLE contacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  phone TEXT,
  email TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_contacts" ON contacts
  FOR ALL USING (auth.uid() = user_id);
```

**Regras de schema IntelliX:**
- `id` sempre UUID com `gen_random_uuid()`
- `created_at` e `updated_at` em toda tabela
- `user_id` FK para `auth.users` quando dados são por usuário
- `metadata JSONB` para campos extensíveis sem migração
- RLS em TODA tabela, sem exceção
- Soft delete preferível a hard delete em tabelas com dados pessoais (`deleted_at TIMESTAMPTZ`)

**Se o projeto processa dados pessoais de pessoas físicas (LGPD):**

Incluir a migration LGPD junto às primeiras migrations do projeto — não como afterthought na Fase 06:

```sql
-- supabase/migrations/00001_lgpd_tables.sql
-- Gerado automaticamente pelo /projeto novo; criar manualmente se ausente
-- Skill de referência: lgpd-compliance
CREATE TABLE consent_records ( ... );   -- consentimentos por finalidade
CREATE TABLE titular_requests ( ... );  -- direitos dos titulares (prazo: 15 dias)
CREATE TABLE data_processing_log ( ... ); -- log de operações + decisões por IA (Art. 20)
-- SQL completo: ver lgpd-compliance → Seção 2
```

> Invocar `lgpd-compliance` para o SQL completo + RLS. A decisão de incluir ou não é de arquitetura — tomada agora, não na Fase 06.

### Passo 2 — Rotas Next.js App Router

```
app/
├── (auth)/
│   ├── login/page.tsx
│   └── register/page.tsx
├── (dashboard)/
│   ├── layout.tsx              # Layout com sidebar autenticado
│   ├── page.tsx                # Dashboard home
│   └── [feature]/
│       ├── page.tsx            # List view
│       └── [id]/page.tsx       # Detail view
└── api/
    └── [feature]/
        └── route.ts            # Route handlers
```

### Passo 3 — Tipos TypeScript centralizados

```typescript
// src/types/index.ts — fonte única de verdade
export interface Contact {
  id: string
  userId: string
  name: string
  phone: string | null
  email: string | null
  metadata: Record<string, unknown>
  createdAt: string
  updatedAt: string
}

// Sempre criar tipos para formulários separados do tipo de DB
export type ContactFormData = Pick<Contact, 'name' | 'phone' | 'email'>
```

### Passo 3b — Design de API `api-and-interface-design` (condicional)

**Quando invocar:** projeto tem Route Handlers públicos, webhooks externos, ou API consumida por outros clientes.
**Não invocar:** projeto SaaS interno onde só Server Actions/componentes consomem os dados.

**Invoke:** `Skill("api-and-interface-design")`

Antes de escrever o primeiro `route.ts`:
- Contract-first: definir o contrato (request/response shapes) antes de implementar
- Versioning strategy: `/api/v1/` ou header `API-Version`?
- Error semantics: padronizar estrutura de erro (RFC 7807 — já padrão IntelliX)
- Validation boundary: Zod em toda entrada de `request.json()` sem exceção
- TypeScript branded types para IDs: `type UserId = string & { readonly __brand: 'UserId' }`

### Passo 4 — Handover para Fase 02 ou 03

Se houver agentes → `intellix:agent-creation`
Se não houver → `intellix:dev-standards`

Atualize `.intellix-phase` para `dev`.

---

## Passo 5 — Data Layer (Repository + Service Pattern)

Clean Architecture exige separação entre lógica de negócio e acesso a dados.
**Nunca acesse o Supabase diretamente de componentes ou route handlers.**

### Estrutura obrigatória

```
src/
├── repositories/          # Acesso a dados — só interage com Supabase
│   └── contacts.repository.ts
├── services/              # Lógica de negócio — usa repositories
│   └── contacts.service.ts
└── app/
    └── api/
        └── contacts/
            └── route.ts   # HTTP layer — usa services
```

### Repository Pattern

```typescript
// src/repositories/contacts.repository.ts
import { createClient } from '@/lib/supabase/server'
import type { Contact, CreateContactInput } from '@/types'

export const contactsRepository = {
  async findAll(userId: string): Promise<Contact[]> {
    const supabase = createClient()
    const { data, error } = await supabase
      .from('contacts')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

    if (error) throw new Error(`contacts.findAll: ${error.message}`)
    return data
  },

  async findById(id: string, userId: string): Promise<Contact | null> {
    const supabase = createClient()
    const { data, error } = await supabase
      .from('contacts')
      .select('*')
      .eq('id', id)
      .eq('user_id', userId)
      .single()

    if (error?.code === 'PGRST116') return null
    if (error) throw new Error(`contacts.findById: ${error.message}`)
    return data
  },

  async create(userId: string, input: CreateContactInput): Promise<Contact> {
    const supabase = createClient()
    const { data, error } = await supabase
      .from('contacts')
      .insert({ ...input, user_id: userId })
      .select()
      .single()

    if (error) throw new Error(`contacts.create: ${error.message}`)
    return data
  },

  async update(id: string, userId: string, input: Partial<CreateContactInput>): Promise<Contact> {
    const supabase = createClient()
    const { data, error } = await supabase
      .from('contacts')
      .update({ ...input, updated_at: new Date().toISOString() })
      .eq('id', id)
      .eq('user_id', userId)
      .select()
      .single()

    if (error) throw new Error(`contacts.update: ${error.message}`)
    return data
  },

  async delete(id: string, userId: string): Promise<void> {
    const supabase = createClient()
    const { error } = await supabase
      .from('contacts')
      .delete()
      .eq('id', id)
      .eq('user_id', userId)

    if (error) throw new Error(`contacts.delete: ${error.message}`)
  },
}
```

### Service Layer

```typescript
// src/services/contacts.service.ts
import { contactsRepository } from '@/repositories/contacts.repository'
import { createContactSchema, type CreateContactInput } from '@/lib/validations/contact'
import type { Contact } from '@/types'

export const contactsService = {
  async getAll(userId: string): Promise<Contact[]> {
    return contactsRepository.findAll(userId)
  },

  async getById(id: string, userId: string): Promise<Contact> {
    const contact = await contactsRepository.findById(id, userId)
    if (!contact) throw new Error('Contact not found')
    return contact
  },

  async create(userId: string, rawInput: unknown): Promise<Contact> {
    // Validação na service layer
    const input = createContactSchema.parse(rawInput)
    return contactsRepository.create(userId, input)
  },

  async update(id: string, userId: string, rawInput: unknown): Promise<Contact> {
    const input = createContactSchema.partial().parse(rawInput)
    return contactsRepository.update(id, userId, input)
  },

  async delete(id: string, userId: string): Promise<void> {
    // Verificar existência antes de deletar
    await this.getById(id, userId)
    return contactsRepository.delete(id, userId)
  },
}
```

### LLM Layer (se o projeto tiver IA/agentes)

Se o projeto usa LLMs, criar estes dois arquivos como **artefatos de arquitetura** — não como afterthought na Fase 06:

```
src/lib/
├── ai/
│   └── guardrails.ts        # prePromptFilter + postOutputValidator
└── lgpd/
    └── pii-redactor.ts      # redactPII — strip CPF/email/tel antes do LLM
```

**Motivo:** Toda chamada LLM do projeto deve passar por estes helpers. Definir na arquitetura garante que nenhum desenvolvedor faça chamadas diretas sem guardrails. Invocar `lgpd-compliance` para o código completo de ambos os arquivos.

```typescript
// Padrão obrigatório para qualquer chamada LLM no projeto
import { prePromptFilter, postOutputValidator } from '@/lib/ai/guardrails'

const pre = prePromptFilter(userInput)
if (!pre.safe) return { error: 'Input inválido' }
const raw = await llm.complete(pre.sanitized)
const post = postOutputValidator(raw)
return post.sanitized
```

---

## Passo 6 — API Design Standards

### Formato de resposta padronizado (RFC 7807 adaptado)

```typescript
// src/lib/api-response.ts
import { NextResponse } from 'next/server'

type ApiSuccess<T> = {
  data: T
  meta?: {
    total?: number
    page?: number
    pageSize?: number
    cursor?: string
  }
}

type ApiError = {
  error: {
    code: string
    message: string
    details?: unknown
  }
}

export const apiResponse = {
  ok: <T>(data: T, meta?: ApiSuccess<T>['meta'], status = 200) =>
    NextResponse.json({ data, ...(meta ? { meta } : {}) }, { status }),

  created: <T>(data: T) =>
    NextResponse.json({ data }, { status: 201 }),

  noContent: () =>
    new NextResponse(null, { status: 204 }),

  badRequest: (message: string, details?: unknown) =>
    NextResponse.json(
      { error: { code: 'BAD_REQUEST', message, details } },
      { status: 400 }
    ),

  unauthorized: () =>
    NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Authentication required' } },
      { status: 401 }
    ),

  forbidden: () =>
    NextResponse.json(
      { error: { code: 'FORBIDDEN', message: 'Insufficient permissions' } },
      { status: 403 }
    ),

  notFound: (resource = 'Resource') =>
    NextResponse.json(
      { error: { code: 'NOT_FOUND', message: `${resource} not found` } },
      { status: 404 }
    ),

  tooManyRequests: () =>
    NextResponse.json(
      { error: { code: 'RATE_LIMITED', message: 'Too many requests' } },
      { status: 429, headers: { 'Retry-After': '10' } }
    ),

  serverError: (message = 'Internal server error') =>
    NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message } },
      { status: 500 }
    ),
}
```

### Route Handler padrão IntelliX

```typescript
// src/app/api/contacts/route.ts
import { contactsService } from '@/services/contacts.service'
import { apiResponse } from '@/lib/api-response'
import { createClient } from '@/lib/supabase/server'
import { ZodError } from 'zod'
import type { NextRequest } from 'next/server'

export async function GET(_req: NextRequest) {
  try {
    const supabase = createClient()
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error || !user) return apiResponse.unauthorized()

    const contacts = await contactsService.getAll(user.id)
    return apiResponse.ok(contacts, { total: contacts.length })
  } catch (err) {
    return apiResponse.serverError()
  }
}

export async function POST(req: NextRequest) {
  try {
    const supabase = createClient()
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error || !user) return apiResponse.unauthorized()

    const body = await req.json()
    const contact = await contactsService.create(user.id, body)
    return apiResponse.created(contact)
  } catch (err) {
    if (err instanceof ZodError) {
      return apiResponse.badRequest('Validation failed', err.flatten())
    }
    return apiResponse.serverError()
  }
}
```

### Paginação Cursor-Based (para listas grandes)

```typescript
// src/lib/pagination.ts
export interface PaginationParams {
  cursor?: string      // ID do último item da página anterior
  pageSize?: number    // default: 20, max: 100
}

export interface PaginatedResult<T> {
  items: T[]
  nextCursor: string | null
  hasMore: boolean
}

// No repository:
async function findAllPaginated(userId: string, params: PaginationParams) {
  const pageSize = Math.min(params.pageSize ?? 20, 100)
  const supabase = createClient()

  let query = supabase
    .from('contacts')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(pageSize + 1)  // +1 para detectar hasMore

  if (params.cursor) {
    query = query.lt('created_at', params.cursor)
  }

  const { data, error } = await query
  if (error) throw error

  const hasMore = data.length > pageSize
  const items = hasMore ? data.slice(0, pageSize) : data
  const nextCursor = hasMore ? items[items.length - 1].created_at : null

  return { items, nextCursor, hasMore }
}
```

---

## Passo 7 — RBAC para SaaS (Quando Aplicável)

Para projetos SaaS com múltiplos roles (admin, manager, user):

```sql
-- supabase/migrations/[timestamp]_rbac.sql
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'user');

CREATE TABLE user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role user_role NOT NULL DEFAULT 'user',
  organization_id UUID,           -- Se multi-tenant por organização
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, organization_id)
);

ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

-- Helper function para verificar role
CREATE OR REPLACE FUNCTION public.get_user_role(check_user_id UUID DEFAULT auth.uid())
RETURNS user_role AS $$
  SELECT role FROM user_roles WHERE user_id = check_user_id LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER;

-- Exemplo de policy com RBAC
CREATE POLICY "admins_manage_all" ON contacts
  FOR ALL USING (
    auth.uid() = user_id
    OR public.get_user_role() = 'admin'
  );
```

```typescript
// src/lib/permissions.ts
type Role = 'admin' | 'manager' | 'user'

const PERMISSIONS = {
  'contacts:read':   ['admin', 'manager', 'user'],
  'contacts:write':  ['admin', 'manager'],
  'contacts:delete': ['admin'],
  'users:manage':    ['admin'],
} as const

type Permission = keyof typeof PERMISSIONS

export function hasPermission(role: Role, permission: Permission): boolean {
  return (PERMISSIONS[permission] as readonly string[]).includes(role)
}
```

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Otimizar queries, índices e performance no Supabase | `supabase-postgres-best-practices` |
| Escrever plano de arquitetura detalhado antes de implementar | `superpowers:writing-plans` |
| Projeto é landing page / site de marketing | `vibestack-architect` |
| Performance de componentes React e Server Components | `vercel-react-best-practices` |

---

## Passo 8 — Multi-tenancy: Isolamento Obrigatório de Dados

Em qualquer SaaS com múltiplos usuários/organizações, **todo acesso ao banco
deve ser explicitamente escopado por tenant**. RLS é a segunda linha de defesa.
A primeira é o código.

### Regra do Repository Multi-tenant

Todo método de repository que retorna dados de usuário DEVE:
1. Receber `userId` (ou `organizationId`) como parâmetro
2. Aplicar `.eq('user_id', userId)` na query
3. Nunca ter uma versão "sem filtro" acessível externamente

```typescript
// ❌ ERRADO — retorna todos os leads de todos os tenants
export const leadsRepository = {
  async findAll(): Promise<Lead[]> {
    const { data } = await supabase.from('leads').select('*')
    return data ?? []
  }
}

// ✅ CORRETO — sempre escopado por tenant
export const leadsRepository = {
  async findAll(userId: string): Promise<Lead[]> {
    const { data, error } = await supabase
      .from('leads')
      .select('*')
      .eq('user_id', userId)     // ← obrigatório
      .order('created_at', { ascending: false })

    if (error) throw new Error(`leads.findAll: ${error.message}`)
    return data ?? []
  },

  async findById(id: string, userId: string): Promise<Lead | null> {
    const { data, error } = await supabase
      .from('leads')
      .select('*')
      .eq('id', id)
      .eq('user_id', userId)     // ← obrigatório mesmo no findById
      .single()

    if (error?.code === 'PGRST116') return null
    if (error) throw new Error(`leads.findById: ${error.message}`)
    return data
  }
}
```

### Singleton de DB Client (padrão obrigatório)

O cliente de banco de dados deve ser instanciado **no nível do módulo**, não
dentro de funções. Em ambientes serverless (Vercel), o módulo é inicializado
uma vez por cold start e reutilizado em warm requests.

```typescript
// src/lib/supabase/service-client.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from '@/integrations/supabase/types'

// Singleton: criado uma vez, reutilizado em todas as chamadas
export const supabaseAdmin = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)
```

```typescript
// src/repositories/leads.repository.ts
import { supabaseAdmin } from '@/lib/supabase/service-client'  // ← import, não createClient()

export const leadsRepository = {
  async findAll(userId: string) {
    return supabaseAdmin.from('leads').select('*').eq('user_id', userId)
  }
}
```

### Schema SQL para Multi-tenancy

```sql
-- Toda tabela de dados de usuário DEVE ter user_id FK
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: SEGUNDA linha de defesa (não a primeira)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_leads" ON leads FOR ALL USING (auth.uid() = user_id);

-- Índice obrigatório em user_id (performance em multi-tenant)
CREATE INDEX idx_leads_user_id ON leads(user_id);
```

---

## Armadilhas comuns
- ❌ Tabelas sem RLS → bloqueio absoluto, não prosseguir sem RLS
- ❌ Usar `pages/` router → apenas App Router
- ❌ Tipos definidos inline nos componentes → centralizar em `src/types/`
- ❌ Supabase queries diretas em componentes → usar repository pattern
- ❌ Lógica de negócio em route handlers → mover para services
- ❌ Sem formato de resposta padronizado → clientes não sabem como tratar erros
- ❌ Query sem `.eq('user_id', userId)` em tabela multi-tenant → vazamento de dados entre tenants
- ❌ `createClient()` dentro de função async → nova conexão por request, esgota pool em prod
- ❌ Credencial admin hardcoded no código → `process.env.ADMIN_EMAIL` sempre
- ❌ Função de listagem sem parâmetro userId → impossível de usar seguramente em multi-tenant
- ❌ `COUNT(*) + 1` para gerar IDs sequenciais → race condition garantida com 2+ usuários simultâneos
