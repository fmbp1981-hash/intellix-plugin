# IntelliX Plugin Update — Senior Review Lessons — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Incorporar ao plugin IntelliX as 5 falhas críticas identificadas no code review sênior do LeadFinder Pro, tornando-as checklist obrigatório em projetos futuros.

**Architecture:** Atualizar 3 arquivos do plugin: MASTER-ARCHITECTURE.md (princípios), 04-dev-standards/SKILL.md (anti-patterns), 00b-code-audit/SKILL.md (checklist de auditoria). Cada file tem uma responsabilidade clara — sem duplicar conteúdo entre eles.

**Tech Stack:** Markdown, plugin IntelliX v2.0

---

## Mapa de Arquivos

- Modify: `MASTER-ARCHITECTURE.md` — adicionar 4 Princípios Invioláveis novos
- Modify: `skills/04-dev-standards/SKILL.md` — adicionar seção "Anti-patterns Críticos de Produção"
- Modify: `skills/00b-code-audit/SKILL.md` — adicionar itens nas dimensões Segurança e Banco de Dados
- Modify: `skills/01-architecture/SKILL.md` — adicionar seção sobre multi-tenancy e singleton de DB client

---

## Task 1: Atualizar Princípios Invioláveis no MASTER-ARCHITECTURE.md

> Adicionar 4 novos princípios aprendidos com o review do LeadFinder Pro.

**File:** `C:\Users\Dell\.claude\plugins\marketplaces\intellix-plugin\MASTER-ARCHITECTURE.md`

- [ ] **Step 1: Ler a tabela atual de Princípios Invioláveis**

```bash
grep -n "Princípios Invioláveis" -A 15 \
  "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/MASTER-ARCHITECTURE.md"
```

- [ ] **Step 2: Adicionar 4 novos princípios após o Princípio #7**

Localizar a linha da tabela com `| 7 | **Arquitetura > Velocidade**` e adicionar logo abaixo:

```markdown
| 8 | **Multi-tenant por Padrão** | Toda query que acessa dados de usuário DEVE ter `.eq("user_id", userId)` explícito — mesmo com RLS ativo. RLS é a segunda linha de defesa, não a única |
| 9 | **Zero Credencial no Código** | Emails de admin, IDs de tenant, secrets e URLs de ambiente nunca em código-fonte. Sempre `process.env.*`. Se está em `.ts`, está errado |
| 10 | **Singleton de DB Client** | Clientes de banco de dados são criados uma vez no módulo, nunca por chamada. `createClient()` dentro de uma função = vazamento de conexão em serverless |
| 11 | **IDs Nunca por COUNT** | Gerar IDs/refs com `COUNT(*) + 1` é race condition garantida. Usar UUID, sequências PostgreSQL ou timestamp+random |
```

- [ ] **Step 3: Adicionar seção "Anti-patterns que Matam SaaS em Produção" antes da seção 3 (Estrutura de Pastas)**

Inserir antes do `## 3. Estrutura de Pastas Canônica`:

```markdown
---

## 2b. Anti-patterns que Matam SaaS em Produção

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
```

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add MASTER-ARCHITECTURE.md
git commit -m "feat: adicionar Princípios #8-11 e seção anti-patterns críticos de produção"
```

---

## Task 2: Atualizar `04-dev-standards/SKILL.md` com seção de anti-patterns

> Adicionar ao dev-standards os padrões de segurança que o review revelou como ausentes.

**File:** `C:\Users\Dell\.claude\plugins\marketplaces\intellix-plugin\skills\04-dev-standards\SKILL.md`

- [ ] **Step 1: Localizar o final do arquivo**

```bash
tail -30 "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/skills/04-dev-standards/SKILL.md"
```

- [ ] **Step 2: Adicionar seção "Padrões de Segurança em SaaS" antes das Armadilhas comuns**

Localizar `## Armadilhas comuns` e inserir ANTES:

```markdown
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

Se herdou projeto com strict desativado:
1. Habilitar `strictNullChecks: true`
2. Corrigir `src/repositories/` e `src/services/` (camadas novas)
3. Adicionar `// @ts-nocheck` nos arquivos legados como marcador de dívida técnica
4. Criar issue para eliminar os `@ts-nocheck` progressivamente
```

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add skills/04-dev-standards/SKILL.md
git commit -m "feat(dev-standards): adicionar padrões de segurança SaaS e TypeScript obrigatório"
```

---

## Task 3: Atualizar `00b-code-audit/SKILL.md` com novos itens de checklist

> O audit checklist atual cobre RLS mas não os padrões de multi-tenancy explícita, credenciais hardcoded, singletons ou race conditions.

**File:** `C:\Users\Dell\.claude\plugins\marketplaces\intellix-plugin\skills\00b-code-audit\SKILL.md`

- [ ] **Step 1: Localizar a Dimensão 7 — Segurança no arquivo**

```bash
grep -n "Dimensão 7\|Segurança" \
  "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/skills/00b-code-audit/SKILL.md"
```

- [ ] **Step 2: Adicionar itens à Dimensão 7 — Segurança**

Localizar o bloco da Dimensão 7 e adicionar os itens:

```markdown
#### Dimensão 7 — Segurança
- [ ] Headers de segurança no `next.config.ts`
- [ ] Middleware protegendo rotas autenticadas
- [ ] Sem secrets expostos no client-side
- [ ] `npm audit` com zero high/critical
- [ ] Sem `console.log` com dados em produção
- [ ] **[NOVO]** Toda query multi-tenant tem `.eq("user_id", userId)` explícito — não depende só de RLS
- [ ] **[NOVO]** Nenhuma string literal de email/ID usada como portão de autorização em API routes
- [ ] **[NOVO]** `process.env.ADMIN_EMAIL` (ou equivalente) documentado no `.env.example`
```

- [ ] **Step 3: Adicionar itens à Dimensão 3 — Banco de Dados**

```markdown
#### Dimensão 3 — Banco de Dados & Supabase
- [ ] RLS ativo em TODAS as tabelas
- [ ] UUID + `gen_random_uuid()` como PKs
- [ ] `created_at` e `updated_at` em todas as tabelas
- [ ] Migrations versionadas em `supabase/migrations/`
- [ ] Sem queries N+1
- [ ] Índices nas colunas de FK e filtros frequentes
- [ ] **[NOVO]** Supabase client criado como singleton de módulo — não dentro de funções
- [ ] **[NOVO]** IDs sequenciais usam PostgreSQL sequence ou UUID — nunca `COUNT(*) + 1`
- [ ] **[NOVO]** Nenhum god-file de acesso a dados (>300 linhas com múltiplas responsabilidades)
```

- [ ] **Step 4: Adicionar nova Dimensão 11 — Multi-tenancy (após Dimensão 10)**

```markdown
#### Dimensão 11 — Multi-tenancy
- [ ] Toda tabela com dados de usuário tem coluna `user_id` FK para `auth.users`
- [ ] Toda query de listagem filtra por `user_id` explicitamente (não só RLS)
- [ ] Funções de acesso a dados aceitam `userId` como parâmetro — sem acessar contexto global
- [ ] Nenhuma função global (ex: `syncAllLeads()` sem parâmetros) que retorne dados cross-tenant
- [ ] Credenciais de tenant (API keys, consultant WA) armazenadas em tabela de configuração por tenant
- [ ] Testes verificam que tenant A não consegue ler dados do tenant B
```

- [ ] **Step 5: Adicionar comando de auditoria rápida na Fase 1**

Na Fase 1 (Mapeamento do Codebase), adicionar após os comandos existentes:

```markdown
# Auditoria de multi-tenancy: queries sem filtro user_id
grep -rn "\.from\(" src/ app/ --include="*.ts" | grep -v "\.eq.*user_id\|\.eq.*userId" | grep -v "test\|spec\|health\|ping"

# Auditoria de credenciais hardcoded: emails em código
grep -rn "@gmail\|@hotmail\|@empresa\|@seudominio" src/ app/ --include="*.ts" --include="*.tsx"

# Auditoria de createClient dentro de funções (não singleton)
grep -rn "createClient" src/ app/ --include="*.ts" | grep -v "^src/lib/supabase\|//\|test"
```

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add skills/00b-code-audit/SKILL.md
git commit -m "feat(audit): adicionar Dimensão 11 multi-tenancy e itens críticos de segurança"
```

---

## Task 4: Atualizar `01-architecture/SKILL.md` com seção multi-tenancy

> A skill de arquitetura ensina repository/service pattern mas não menciona multi-tenancy explícita — o gap mais crítico encontrado no review.

**File:** `C:\Users\Dell\.claude\plugins\marketplaces\intellix-plugin\skills\01-architecture\SKILL.md`

- [ ] **Step 1: Localizar o final da seção de Repository Pattern**

```bash
grep -n "## Passo\|## Skills\|## Armadilhas" \
  "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/skills/01-architecture/SKILL.md"
```

- [ ] **Step 2: Adicionar "Passo 8 — Multi-tenancy Data Isolation" antes das Armadilhas**

Localizar `## Armadilhas comuns` e inserir ANTES:

```markdown
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
  -- ...campos de negócio...
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS: SEGUNDA linha de defesa (não a primeira)
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_leads" ON leads
  FOR ALL USING (auth.uid() = user_id);

-- Índice obrigatório em user_id (performance em multi-tenant)
CREATE INDEX idx_leads_user_id ON leads(user_id);
```
```

- [ ] **Step 3: Adicionar ao final das Armadilhas comuns**

Localizar `## Armadilhas comuns` e adicionar itens ao final da lista:

```markdown
- ❌ Query sem `.eq('user_id', userId)` em tabela multi-tenant → vazamento de dados entre tenants
- ❌ `createClient()` dentro de função async → nova conexão por request, esgota pool em prod
- ❌ Credencial admin hardcoded no código → `process.env.ADMIN_EMAIL` sempre
- ❌ Função de listagem sem parâmetro userId → impossível de usar seguramente em multi-tenant
- ❌ `COUNT(*) + 1` para gerar IDs sequenciais → race condition garantida com 2+ usuários simultâneos
```

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add skills/01-architecture/SKILL.md
git commit -m "feat(architecture): adicionar Passo 8 multi-tenancy, singleton client e anti-patterns"
```

---

## Resultado esperado

Após as 4 tasks, o plugin IntelliX vai:

1. **Prevenir o data leak multi-tenant** em novos projetos — por princípio inviolável (#8) + checklist de auditoria (Dimensão 11) + exemplo de código correto no architecture skill
2. **Prevenir credenciais hardcoded** — por princípio inviolável (#9) + item de auditoria + exemplo em dev-standards
3. **Prevenir DB client por chamada** — por princípio inviolável (#10) + singleton obrigatório em architecture skill
4. **Prevenir race condition em IDs** — por princípio inviolável (#11) + auditoria + alternativas corretas
5. **Enforçar strictNullChecks** — dev-standards agora diz que `strict: false` é bloqueio de PR

**Score de impacto:** Um sistema construído do zero com o plugin atualizado não teria nenhum dos 5 issues críticos encontrados no LeadFinder Pro.
