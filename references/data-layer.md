# Data Layer — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§5–12](../MASTER-ARCHITECTURE.md).
> Consulte ao criar repositories, services, schemas SQL ou behaviors.

## 5. Repository + Service Pattern

**Lei fundamental:** Nunca acesse o banco diretamente de componentes, hooks ou route handlers.

```
Frontend Component
      ↓ (captura intenção)
Server Action / Route Handler
      ↓ (usa)
Service Layer (lógica de negócio + validação Zod)
      ↓ (usa)
Repository Layer (acesso ao Supabase)
      ↓ (query)
Supabase / PostgreSQL
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
      .from('contacts').select('*')
      .eq('id', id).eq('user_id', userId).single()
    if (error?.code === 'PGRST116') return null
    if (error) throw new Error(`contacts.findById: ${error.message}`)
    return data
  },

  async create(userId: string, input: CreateContactInput): Promise<Contact> {
    const supabase = createClient()
    const { data, error } = await supabase
      .from('contacts').insert({ ...input, user_id: userId }).select().single()
    if (error) throw new Error(`contacts.create: ${error.message}`)
    return data
  },

  async update(id: string, userId: string, input: Partial<CreateContactInput>): Promise<Contact> {
    const supabase = createClient()
    const { data, error } = await supabase
      .from('contacts')
      .update({ ...input, updated_at: new Date().toISOString() })
      .eq('id', id).eq('user_id', userId).select().single()
    if (error) throw new Error(`contacts.update: ${error.message}`)
    return data
  },

  async delete(id: string, userId: string): Promise<void> {
    const supabase = createClient()
    const { error } = await supabase
      .from('contacts').delete().eq('id', id).eq('user_id', userId)
    if (error) throw new Error(`contacts.delete: ${error.message}`)
  },
}
```

### Service Layer (lógica de negócio + validação)

```typescript
// src/services/contacts.service.ts
import { contactsRepository } from '@/repositories/contacts.repository'
import { createContactSchema } from '@/validations/contact.schema'
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
    const input = createContactSchema.parse(rawInput) // Validação aqui
    return contactsRepository.create(userId, input)
  },

  async update(id: string, userId: string, rawInput: unknown): Promise<Contact> {
    const input = createContactSchema.partial().parse(rawInput)
    return contactsRepository.update(id, userId, input)
  },

  async delete(id: string, userId: string): Promise<void> {
    await this.getById(id, userId) // Verifica existência antes
    return contactsRepository.delete(id, userId)
  },
}
```

---

## 6. Behavior Isolation — Comunicação Entre Módulos

### Estrutura de um Behavior

```
app/(dashboard)/[feature]/behaviors/
  send-message/
    index.ts                ← exporta a função principal (ponto de entrada)
    actions.ts              ← Server Actions específicas deste behavior
    send-message.test.ts    ← testes: happy path + edge cases + error cases
```

### Regra de Comunicação

```typescript
// ❌ ERRADO — behavior importando lógica de outro behavior
import { createChat } from '../new-chat/actions'

// ✅ CORRETO — via contrato compartilhado em lib/
import { createChat } from '@/lib/chat/contracts'
```

### Contratos Compartilhados

```
src/lib/
  chat/
    contracts.ts    ← interfaces TypeScript compartilhadas entre behaviors
    queries.ts      ← queries Supabase reutilizáveis por múltiplos behaviors
```

---

## 7. Schema de Banco de Dados — Padrão IntelliX

```sql
-- Padrão obrigatório para toda tabela
CREATE TABLE [nome] (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  -- campos específicos da tabela
  metadata    JSONB       DEFAULT '{}',          -- extensível sem migração
  created_at  TIMESTAMPTZ DEFAULT now(),
  updated_at  TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE [nome] ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_[nome]" ON [nome]
  FOR ALL USING (auth.uid() = user_id);

-- Trigger de updated_at (criar uma vez, reusar)
CREATE TRIGGER set_updated_at BEFORE UPDATE ON [nome]
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Regras de schema:**
- `id` sempre UUID com `gen_random_uuid()`
- `created_at` e `updated_at` em toda tabela
- `metadata JSONB` para campos extensíveis sem migração futura
- RLS em TODA tabela, sem exceção

### RBAC para SaaS Multi-Tenant

```sql
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'user');

CREATE TABLE user_roles (
  id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role            user_role   NOT NULL DEFAULT 'user',
  organization_id UUID,
  created_at      TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, organization_id)
);

ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION public.get_user_role(check_user_id UUID DEFAULT auth.uid())
RETURNS user_role AS $$
  SELECT role FROM user_roles WHERE user_id = check_user_id LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER;
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
