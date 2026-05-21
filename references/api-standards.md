# API Standards — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§5–12](../MASTER-ARCHITECTURE.md).
> Consulte ao criar Route Handlers ou implementar paginação.

## 8. API Response — Formato Padronizado (RFC 7807)

```typescript
// src/lib/api-response.ts
import { NextResponse } from 'next/server'

export const apiResponse = {
  ok: <T>(data: T, meta?: { total?: number; cursor?: string }, status = 200) =>
    NextResponse.json({ data, ...(meta ? { meta } : {}) }, { status }),

  created: <T>(data: T) => NextResponse.json({ data }, { status: 201 }),

  noContent: () => new NextResponse(null, { status: 204 }),

  badRequest: (message: string, details?: unknown) =>
    NextResponse.json({ error: { code: 'BAD_REQUEST', message, details } }, { status: 400 }),

  unauthorized: () =>
    NextResponse.json({ error: { code: 'UNAUTHORIZED', message: 'Authentication required' } }, { status: 401 }),

  forbidden: () =>
    NextResponse.json({ error: { code: 'FORBIDDEN', message: 'Insufficient permissions' } }, { status: 403 }),

  notFound: (resource = 'Resource') =>
    NextResponse.json({ error: { code: 'NOT_FOUND', message: `${resource} not found` } }, { status: 404 }),

  tooManyRequests: () =>
    NextResponse.json(
      { error: { code: 'RATE_LIMITED', message: 'Too many requests' } },
      { status: 429, headers: { 'Retry-After': '10' } }
    ),

  serverError: (message = 'Internal server error') =>
    NextResponse.json({ error: { code: 'INTERNAL_ERROR', message } }, { status: 500 }),
}
```

### Route Handler Padrão

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
  } catch {
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
    if (err instanceof ZodError) return apiResponse.badRequest('Validation failed', err.flatten())
    return apiResponse.serverError()
  }
}
```

---

## 9. Paginação Cursor-Based

```typescript
// src/lib/pagination.ts
export interface PaginationParams {
  cursor?: string   // ID/timestamp do último item da página anterior
  pageSize?: number // default: 20, max: 100
}

export interface PaginatedResult<T> {
  items: T[]
  nextCursor: string | null
  hasMore: boolean
}

// Uso no repository:
async function findAllPaginated(userId: string, params: PaginationParams): Promise<PaginatedResult<Contact>> {
  const pageSize = Math.min(params.pageSize ?? 20, 100)
  const supabase = createClient()

  let query = supabase
    .from('contacts').select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(pageSize + 1) // +1 para detectar hasMore

  if (params.cursor) query = query.lt('created_at', params.cursor)

  const { data, error } = await query
  if (error) throw error

  const hasMore = data.length > pageSize
  const items = hasMore ? data.slice(0, pageSize) : data
  const nextCursor = hasMore ? items[items.length - 1].created_at : null

  return { items, nextCursor, hasMore }
}
```
