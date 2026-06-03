---
name: dev-standards
description: >
  Use esta skill sempre que o usuário mencionar: padrões de código,
  TypeScript, tipagem, naming conventions, ESLint, Prettier, imports,
  estrutura de componentes, "como nomear", "como organizar", boas práticas,
  code review, refatoração, ou antes de começar qualquer implementação nova.
  Esta é a Fase 03 do fluxo IntelliX — referência permanente durante o dev.
user-invocable: false
---

# Fase 03 — Dev Standards

Padrões de código obrigatórios IntelliX. Esta skill é referência contínua —
consulte antes de implementar qualquer feature.

---

## Passo 0 — Disciplina de Coding `karpathy-guidelines` (OBRIGATÓRIO)

**Invoke:** `Skill("karpathy-guidelines")`

Antes de escrever qualquer linha de código, aplique os 4 princípios de Andrej Karpathy
para evitar os erros mais comuns de LLMs em tarefas de desenvolvimento:

1. **Think Before Coding** — Surface assunções explicitamente. Se houver múltiplas interpretações, apresente-as; não escolha silenciosamente.
2. **Simplicity First** — Código mínimo que resolve o problema. Sem features especulativas, sem abstrações prematuras.
3. **Surgical Changes** — Toque APENAS o que precisa ser tocado. Não "melhore" código adjacente não relacionado à tarefa.
4. **Goal-Driven Execution** — Antes de começar: defina os critérios de sucesso verificáveis.

**Gatilho obrigatório:** Antes de qualquer implementação nova, refatoração ou bugfix.
**Exceção:** Tarefas triviais (renomear variável, adicionar import simples).

## Passo 0b — Disciplina de Git `git-workflow-and-versioning`

**Invoke:** `Skill("git-workflow-and-versioning")`

Executar em paralelo com o Passo 0 (karpathy-guidelines). Define o contrato de versionamento antes de começar:

- **Trunk-based:** branches de feature com vida máxima de 1-3 dias — sem branches de longa duração
- **Atomic commits:** cada commit faz uma coisa lógica, mensagem explica o *porquê* não o *o quê*
- **Save-point pattern:** a cada incremento que funciona → commit. Nunca perder mais de um incremento de trabalho
- **Worktrees para agentes paralelos:** quando múltiplos sub-agentes trabalham em paralelo, usar `git worktree` para isolamento
- **Pre-commit:** lint + typecheck + testes antes de qualquer commit (não na CI, no commit)

**Gatilho:** início de qualquer feature nova ou sessão de desenvolvimento.
**Exceção:** hotfixes triviais de 1 linha.

---

## TypeScript Strict — Regras absolutas

```typescript
// ❌ NUNCA
const data: any = response
function process(input: any) {}
// @ts-ignore
const result = riskyOperation()

// ✅ SEMPRE
const data: ApiResponse = response
function process(input: ContactFormData): ProcessResult {}
const result = riskyOperation() as ExpectedType // com type guard se possível
```

**`tsconfig.json` IntelliX:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

## Naming Conventions

```
Arquivos:        kebab-case         contact-form.tsx
Componentes:     PascalCase         ContactForm
Hooks:           camelCase com use  useContacts
Funções utils:   camelCase          formatPhone
Tipos/Interfaces: PascalCase        ContactFormData
Constantes:      SCREAMING_SNAKE    MAX_RETRY_COUNT
Variáveis:       camelCase          contactList
```

## Estrutura de Componentes

```typescript
// Ordem obrigatória dentro de um componente
// 1. Imports (externos → internos → tipos)
// 2. Types/Interfaces locais
// 3. Constantes
// 4. Componente (function declaration, não arrow function)
// 5. Export default

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import type { Contact } from '@/types'

interface ContactCardProps {
  contact: Contact
  onEdit: (id: string) => void
}

const MAX_NAME_LENGTH = 60

export function ContactCard({ contact, onEdit }: ContactCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  // ...
}
```

## Server vs Client Components

```typescript
// Server Component (padrão — sem 'use client')
// Pode fazer fetch direto, acessa DB via Supabase server client
export default async function ContactsPage() {
  const contacts = await getContacts() // server-side
  return <ContactList contacts={contacts} />
}

// Client Component (apenas quando necessário)
// Interatividade, useState, useEffect, event handlers
'use client'
export function ContactList({ contacts }: { contacts: Contact[] }) {
  const [selected, setSelected] = useState<string | null>(null)
  // ...
}
```

## Commits (Conventional Commits)

```
feat(contacts): adiciona campo de telefone secundário
fix(auth): corrige redirect após login em mobile
chore(deps): atualiza next.js para 15.2
docs(readme): adiciona instruções de setup local
test(contacts): adiciona testes de integração para RLS
refactor(utils): extrai lógica de formatação de telefone
```

## Server Actions vs Route Handlers

```typescript
// QUANDO usar Server Action (mutations de formulário, Next.js 15 padrão)
// src/app/(dashboard)/contacts/actions.ts
'use server'
import { revalidatePath } from 'next/cache'
import { contactsService } from '@/services/contacts.service'
import { createClient } from '@/lib/supabase/server'

export async function createContactAction(formData: FormData) {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Unauthorized')

  const input = {
    name: formData.get('name') as string,
    phone: formData.get('phone') as string,
    email: formData.get('email') as string,
  }

  await contactsService.create(user.id, input)
  revalidatePath('/dashboard/contacts')
}

// QUANDO usar Route Handler (APIs públicas, webhooks, dados para client components)
// src/app/api/contacts/route.ts
// → Quando o cliente precisa de JSON (TanStack Query, fetch manual)
// → Quando é um webhook externo
// → Quando precisa de streaming response
```

| Use Server Action | Use Route Handler |
|-------------------|-------------------|
| Formulário → mutation → redirect | API consumida por JS externo |
| Revalidar cache após mutation | Webhooks recebidos |
| Operação server-side sem resposta JSON | Streaming (IA, SSE) |
| Simplicidade máxima | Controle total do HTTP |

---

## TanStack Query — Data Fetching Client-Side

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query'

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,        // 1 minuto — não refetch desnecessário
        gcTime: 5 * 60 * 1000,       // 5 minutos no cache
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  })
}
```

```typescript
// src/hooks/use-contacts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Contact, CreateContactInput } from '@/types'

const QUERY_KEY = ['contacts'] as const

export function useContacts() {
  return useQuery({
    queryKey: QUERY_KEY,
    queryFn: async (): Promise<Contact[]> => {
      const res = await fetch('/api/contacts')
      if (!res.ok) throw new Error('Failed to fetch contacts')
      const { data } = await res.json()
      return data
    },
  })
}

export function useCreateContact() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (input: CreateContactInput) => {
      const res = await fetch('/api/contacts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      })
      if (!res.ok) throw new Error('Failed to create contact')
      const { data } = await res.json()
      return data as Contact
    },
    // Optimistic update
    onMutate: async (newContact) => {
      await queryClient.cancelQueries({ queryKey: QUERY_KEY })
      const previous = queryClient.getQueryData<Contact[]>(QUERY_KEY)

      queryClient.setQueryData<Contact[]>(QUERY_KEY, (old = []) => [
        { id: 'temp', ...newContact, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), userId: '', metadata: {} },
        ...old,
      ])

      return { previous }
    },
    onError: (_err, _newContact, context) => {
      if (context?.previous) {
        queryClient.setQueryData(QUERY_KEY, context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
    },
  })
}
```

---

## Caching Strategy (Next.js 15)

```typescript
// Nível 1 — fetch() com cache (Server Components)
// Cacheado até revalidar manualmente ou por tempo
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 3600 }  // revalida a cada 1h
})

// Nível 2 — unstable_cache (funções server-side)
import { unstable_cache } from 'next/cache'

const getCachedContacts = unstable_cache(
  async (userId: string) => contactsRepository.findAll(userId),
  ['contacts'],
  { revalidate: 60, tags: ['contacts'] }   // cache por 60s, tag para invalidação
)

// Nível 3 — revalidateTag (invalidar cache por tag)
import { revalidateTag } from 'next/cache'

export async function createContactAction(formData: FormData) {
  // ... criar contato
  revalidateTag('contacts')   // invalida tudo com a tag 'contacts'
}

// Nível 4 — TanStack Query (Client Components)
// Ver seção anterior
```

| Nível | Onde | Quando usar |
|-------|------|-------------|
| `fetch` cache | Server Component | Dados públicos, CDN-friendly |
| `unstable_cache` | Server functions | Dados privados por usuário |
| `revalidateTag` | Server Actions | Após mutations |
| TanStack Query | Client Components | Dados interativos, realtime |

---

## State Management

```typescript
// REGRA: Server State → TanStack Query. UI State → useState. Global UI State → Zustand

// Quando usar useState:
// - Estado local de UI (modal aberto, tab ativa, loading de botão)
const [isOpen, setIsOpen] = useState(false)

// Quando usar TanStack Query:
// - Dados do servidor (contacts, users, etc.)
const { data: contacts } = useContacts()

// Quando usar Zustand (estado global de UI):
// - Estado compartilhado entre múltiplos componentes
// - Preferências do usuário, sidebar collapsed, notificações
import { create } from 'zustand'

interface AppStore {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  notifications: Notification[]
  addNotification: (n: Notification) => void
}

export const useAppStore = create<AppStore>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  notifications: [],
  addNotification: (n) => set((s) => ({ notifications: [...s.notifications, n] })),
}))
```

| Estado | Solução |
|--------|---------|
| Dados do banco | TanStack Query |
| UI local (modal, tab) | useState |
| UI global (sidebar, theme) | Zustand |
| Formulários | React Hook Form + Zod |
| URL state (filtros, paginação) | `useSearchParams` |

---

## Formulários com React Hook Form + Zod

```typescript
// src/components/contacts/create-contact-form.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { createContactSchema, type CreateContactInput } from '@/lib/validations/contact'
import { useCreateContact } from '@/hooks/use-contacts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage
} from '@/components/ui/form'

export function CreateContactForm() {
  const { mutate: createContact, isPending } = useCreateContact()

  const form = useForm<CreateContactInput>({
    resolver: zodResolver(createContactSchema),
    defaultValues: { name: '', phone: '', email: '' },
  })

  function onSubmit(data: CreateContactInput) {
    createContact(data, {
      onSuccess: () => form.reset(),
    })
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nome</FormLabel>
              <FormControl>
                <Input placeholder="Nome do contato" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {/* outros campos... */}
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Criando...' : 'Criar Contato'}
        </Button>
      </form>
    </Form>
  )
}
```

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Workflow completo de desenvolvimento de UI (obrigatório antes de criar components) | `frontend-dev-workflow` |
| Performance, memoização e boas práticas React/Next.js (Vercel Engineering) | `vercel-react-best-practices` |
| UI com design profissional, tokens, shadcn/ui avançado | `ckm-ui-styling` |
| Implementar feature nova com TDD (escrever teste ANTES do código) | `superpowers:test-driven-development` |
| Debug de comportamento inesperado durante desenvolvimento | `superpowers:systematic-debugging` |
| Simplificar código após implementação | `simplify` |

---

## Segurança em SaaS Multi-tenant — Regras Absolutas

### 1. Toda query de dados de usuário requer filtro explícito

```typescript
// ❌ Retorna TUDO — viola multi-tenancy mesmo com RLS
const { data } = await supabase.from('leads').select('*')

// ✅ Sempre passar userId como parâmetro e filtrar
export async function getLeads(userId: string) {
  const { data, error } = await supabase
    .from('leads')
    .select('*')
    .eq('user_id', userId)   // <- obrigatório
  if (error) throw new Error(`leads.getAll: ${error.message}`)
  return data ?? []
}
```

### 2. Credenciais de autorização nunca em código-fonte

```typescript
// ❌ BLOQUEIO ABSOLUTO — literal string como portão de segurança
const ADMIN_EMAIL = 'admin@empresa.com'

// ✅
const ADMIN_EMAIL = process.env.ADMIN_EMAIL
if (!ADMIN_EMAIL) throw new Error('ADMIN_EMAIL env var obrigatória')
```

**Adicionar ao `.env.example` qualquer valor que varie por ambiente ou tenant.**

### 3. Supabase client como singleton de módulo

```typescript
// ❌ Cria nova conexão por chamada — esgota pool em produção
export async function createThing() {
  const supabase = createClient(url, key)
  // ...
}

// ✅ Module-level singleton
const supabaseAdmin = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function createThing() {
  return supabaseAdmin.from('things').insert(...)
}
```

### 4. IDs sequenciais requerem mecanismo de banco, não COUNT

```typescript
// ❌ Race condition garantida em ambiente concorrente
const { count } = await supabase.from('items').select('*', { count: 'exact', head: true })
const id = count + 1

// ✅ Timestamp + random (display-friendly)
const ref = `${prefix}-${Date.now().toString(36).toUpperCase()}`

// ✅ PostgreSQL sequence (garantia forte)
const { data } = await supabase.rpc('next_sequence', { p_table: 'items', p_user_id: userId })
```

### 5. Chamadas LLM sempre com guardrails (projetos com IA)

```typescript
// ❌ Chamada direta ao LLM — sem filtro de input, sem PII, sem validação de output
const result = await anthropic.messages.create({ messages: [{ role: 'user', content: userMessage }] })

// ✅ Sempre envolver com prePromptFilter + postOutputValidator
import { prePromptFilter, postOutputValidator } from '@/lib/ai/guardrails'

const pre = prePromptFilter(userMessage)
if (!pre.safe) return { error: 'Input inválido' }  // detectou injection ou PII

const raw = await anthropic.messages.create({
  messages: [{ role: 'user', content: pre.sanitized }]
})

const post = postOutputValidator(raw.content[0].text)
return post.sanitized  // PII removida, system prompt leak bloqueado
```

**Por quê:** Chamada direta expõe CPF/email no contexto do LLM (LGPD Art. 6 III) e permite prompt injection (OWASP LLM01). Os guardrails estão em `src/lib/ai/guardrails.ts` — criados na Fase 01 (Architecture), obrigatórios em todas as chamadas LLM do projeto.

---

## Configuração TypeScript IntelliX (obrigatória)

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

**`strict: false` é bloqueio de PR.** Com `strictNullChecks: false`, null pointer
exceptions são invisíveis ao compilador e explodem em produção. O custo de
habilitar no início é 2h de fixes. O custo de habilitar depois de 6 meses é
uma semana.

**Hierarquia de supressão TypeScript (da mais aceitável à menos):**
> Princípio Inviolável #4 — ver também `MASTER-ARCHITECTURE.md §0b`

| Supressão | Quando usar | Condição |
|-----------|-------------|----------|
| `// @ts-nocheck` no topo do arquivo | Arquivo legado herdado, migração incremental | Obrigatório: `// @ts-nocheck — TODO: remover — issue #N` |
| `// @ts-expect-error` na linha | Incompatibilidade de tipo com biblioteca de terceiros | Obrigatório: `// @ts-expect-error — <motivo> (lib: <pacote>@<versão>)` |
| `// @ts-ignore` | **NUNCA** — esconde bugs sem evidência | Bloqueio absoluto |
| `any` explícito | **NUNCA** | Bloqueio absoluto |

**Migração de projeto com strict desativado:**
1. Habilitar `strictNullChecks: true` no tsconfig.json
2. Corrigir erros nas camadas novas (`src/repositories/`, `src/services/`, `src/app/api/`)
3. Para cada arquivo legado com erros: adicionar `// @ts-nocheck — TODO: remover — issue #N`
4. Criar issue rastreável para cada arquivo suprimido com prazo definido
5. Sprint de quitação de dívida: remover `@ts-nocheck` um arquivo por vez, corrigindo os erros

---

## Armadilhas comuns
- ❌ `export default` em arrow functions → usar `function` declaration
- ❌ Fetch no client component → mover para Server Component ou Route Handler
- ❌ Lógica de negócio no componente → extrair para `lib/` ou hook
- ❌ Estilos inline → usar classes Tailwind
- ❌ `console.log` em produção → usar logger ou remover antes do commit
