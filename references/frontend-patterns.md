# Frontend Patterns — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§5–12](../MASTER-ARCHITECTURE.md).
> Consulte ao criar componentes `.tsx`, hooks ou definir convenções de nomes.

## 10. TypeScript Strict — Regras Absolutas

```typescript
// ❌ NUNCA em projeto IntelliX
const data: any = response
function process(input: any) {}
// @ts-ignore
const result = riskyOperation()

// ✅ SEMPRE
const data: ApiResponse = response
function process(input: ContactFormData): ProcessResult {}
```

**`tsconfig.json` IntelliX:**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

---

## 11. Naming Conventions

| Artefato | Convenção | Exemplo |
|---|---|---|
| Arquivo de componente | PascalCase | `ContactCard.tsx` |
| Arquivo não-componente | kebab-case | `contact-form.ts`, `use-contacts.ts` |
| Pasta de página | kebab-case | `chat-history/` |
| Pasta de behavior | kebab-case | `send-message/` |
| Componente React | PascalCase | `ContactCard` |
| Hook | camelCase + `use` | `useContacts` |
| Server Action | camelCase | `createContact` |
| Função utilitária | camelCase | `formatPhone` |
| Tipo / Interface | PascalCase | `ContactFormData` |
| Constante global | SCREAMING_SNAKE | `MAX_RETRY_COUNT` |
| Variável / prop | camelCase | `contactList` |
| Rota de API | kebab-case | `api/send-message/` |
| Teste | mesmo nome + `.test` | `send-message.test.ts` |

---

## 12. Estrutura de Componentes

```typescript
// Ordem obrigatória dentro de qualquer componente

// 1. Imports externos (React, Next.js, libs)
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

// 2. Imports internos (componentes, hooks, libs)
import { Button } from '@/components/ui/button'
import { useContacts } from '@/hooks/use-contacts'

// 3. Imports de tipos
import type { Contact } from '@/types'

// 4. Tipos/interfaces locais
interface ContactCardProps {
  contact: Contact
  onDelete: (id: string) => void
}

// 5. Componente principal
export function ContactCard({ contact, onDelete }: ContactCardProps) {
  // 5a. Hooks (na ordem: state → context → custom hooks → efeitos)
  const [isDeleting, setIsDeleting] = useState(false)
  const router = useRouter()

  // 5b. Handlers
  const handleDelete = async () => {
    setIsDeleting(true)
    await onDelete(contact.id)
    setIsDeleting(false)
  }

  // 5c. Render helpers (se necessário)
  const formattedPhone = contact.phone ? formatPhone(contact.phone) : '—'

  // 5d. Render principal
  return (
    <div className="...">
      {/* JSX */}
    </div>
  )
}
```
