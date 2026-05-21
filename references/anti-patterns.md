# Anti-patterns IntelliX — O que NUNCA Fazer

> Estes erros foram identificados em code reviews reais.
> São sutis, não quebram em dev, explodem em produção.

---

## Anti-patterns Críticos de Produção

Estes erros foram identificados em code reviews reais de sistemas em produção.
São sutis, não quebram em dev, e explodem em produção com múltiplos tenants.

### 🔴 Data Leak Multi-tenant

```typescript
// ❌ MATA O SAAS — retorna dados de TODOS os tenants
const { data } = await supabase
  .from('leads')
  .select('*')
  .order('created_at')

// ✅ SEMPRE filtrar por user_id (defesa dupla com RLS)
const { data } = await supabase
  .from('leads')
  .select('*')
  .eq('user_id', userId)   // ← obrigatório
  .order('created_at')
```

**Quando acontece:** Funções de listagem criadas sem userId no escopo, depois
chamadas de um contexto onde o userId existe mas não é passado.

**Como auditar:** `grep -rn "\.from\(" src/ app/ | grep -v "\.eq.*user_id"` —
qualquer resultado é suspeito.

---

### 🔴 Credencial Hardcoded como Portão de Autenticação

```typescript
// ❌ QUEBRA quando o email muda, VAZA se o repositório for público
const ADMIN_EMAIL = 'fulano@empresa.com'
if (user.email !== ADMIN_EMAIL) return unauthorized()

// ✅ Environment variable — muda sem deploy, nunca vaza em git
const ADMIN_EMAIL = process.env.ADMIN_EMAIL
if (!ADMIN_EMAIL) throw new Error('ADMIN_EMAIL env var not set')
if (user.email !== ADMIN_EMAIL) return unauthorized()
```

**Regra:** Se um string literal é usado em lógica de autorização, é uma
vulnerabilidade. Sempre `process.env.*`.

---

### 🔴 Race Condition em ID Sequential por COUNT

```typescript
// ❌ RACE CONDITION — 2 chamadas simultâneas geram ID duplicado
const { count } = await supabase.from('items').select('*', { count: 'exact', head: true })
const nextId = `Item-${(count + 1).toString().padStart(3, '0')}`

// ✅ Opção 1: UUID (nunca colide)
const id = crypto.randomUUID()

// ✅ Opção 2: Timestamp + random (display-friendly, sem colisão prática)
const ref = `Item-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2,6).toUpperCase()}`

// ✅ Opção 3: PostgreSQL sequence (garantia de banco)
const { data } = await supabase.rpc('next_item_seq', { p_user_id: userId })
```

---

### 🔴 DB Client Instanciado por Chamada em Serverless

```typescript
// ❌ CRIA NOVA CONEXÃO A CADA REQUEST — esgota o pool em < 1min sob carga
export async function getUser(id: string) {
  const supabase = createClient(url, key)  // ← dentro da função!
  return supabase.from('users').select().eq('id', id).single()
}

// ✅ SINGLETON de módulo — criado uma vez, reutilizado
const supabase = createClient<Database>(    // ← nível de módulo
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function getUser(id: string) {
  return supabase.from('users').select().eq('id', id).single()
}
```

**Em Vercel serverless:** O módulo é inicializado uma vez por cold start e
reutilizado em warm requests. Colocar o client no módulo = 1 conexão por
instância de função. Colocar dentro da função = 1 conexão por request.

---

### 🟡 Arquitetura Aditiva Deixa Dois Sistemas Coexistindo

```
❌ O que acontece quando se refatora sem deletar o legado:
├── lib/oldCRM.ts          ← 600 linhas, sem user_id, sem tipagem
├── src/lib/oldCRM.ts      ← 700 linhas, versão divergida
└── src/repositories/      ← correto, mas o frontend ainda usa os de cima

✅ Migração real = DELETE o arquivo antigo no mesmo PR que cria o novo
   Não existe "vou deletar depois" — depois nunca chega.
```

**Regra:** Toda refatoração que cria um novo arquivo para substituir um antigo
deve deletar o arquivo antigo no mesmo commit. Coexistência é dívida técnica
com juros altos.

---

## Armadilhas — Lista de Verificação

```
❌ Criar código antes de /plan aprovado
❌ Modificar arquivos fora da lista do /plan
❌ Lógica de negócio em componentes React
❌ Secrets em variáveis NEXT_PUBLIC_
❌ Tabelas Supabase sem RLS
❌ Usar pages/ router (apenas App Router)
❌ Tipos inline nos componentes (centralizar em src/types/)
❌ Supabase queries diretas em componentes (usar repository)
❌ Lógica de negócio em route handlers (mover para services)
❌ Behaviors importando lógica diretamente de outros behaviors
❌ Usar `any` em TypeScript
❌ Avançar para próxima issue sem testes na issue atual
❌ Instalar dependências não aprovadas no /plan
❌ Refatorar código fora do escopo da issue atual
```

---
