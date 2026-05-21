---
name: code-audit
description: >
  Use esta skill quando o projeto for um sistema existente que precisa ser auditado,
  refatorado, reorganizado ou elevado ao padrão IntelliX de arquitetura clean.
  Ativa quando o usuário mencionar: revisar código, auditar sistema, refatorar,
  reorganizar código, código legado, melhorar qualidade, padronizar, "código bagunçado",
  "está mal organizado", "quero limpar o código", "adaptar ao padrão IntelliX",
  "enquadrar no padrão", code review do projeto, dívida técnica, technical debt,
  ou qualquer indicação de que o sistema já existe e precisa de melhoria estrutural.
  Esta skill substitui o project-kickoff quando o projeto já existe.
user-invocable: true
---

# Fase 00b — Code Audit & Refactoring Roadmap

Auditoria completa de sistemas existentes contra os padrões IntelliX de arquitetura
clean. Diagnostica gaps, gera relatório detalhado e produz um roadmap priorizado de
refatoração executável fase a fase.

> Esta skill é o equivalente de contratar um **Senior Developer de 15+ anos** para
> revisar seu codebase e dizer exatamente o que precisa mudar, por quê, e em que ordem.

---

## Quando usar esta skill vs project-kickoff

```
Sistema já existe com código? → code-audit (esta skill)
Sistema novo a ser criado?    → project-kickoff (Fase 00)
Sistema existente mas sem estrutura IntelliX alguma?     → code-audit primeiro
Sistema com estrutura parcial IntelliX e precisa avançar? → code-audit primeiro
```

---

## Workflow — 5 Fases do Audit

### Fase 1 — Mapeamento do Codebase

Antes de qualquer diagnóstico, entenda o que existe:

```bash
# Estrutura geral
find . -type f -name "*.ts" -o -name "*.tsx" | head -50
find . -type f -name "*.ts" -o -name "*.tsx" | wc -l

# Dependências
cat package.json | grep -E '"dependencies"|"devDependencies"' -A 50

# Tamanho dos arquivos (identificar God Files)
find src -name "*.ts" -o -name "*.tsx" | xargs wc -l | sort -rn | head -20

# Verificar se tem testes
find . -name "*.test.ts" -o -name "*.spec.ts" -o -name "*.test.tsx" | wc -l
```

**Mapeie:**
- [ ] Versão do Next.js (App Router ou Pages Router?)
- [ ] TypeScript configurado? Strict mode ativo?
- [ ] Existe design system? (Tailwind, Shadcn, tokens?)
- [ ] Existem testes? (unitários, E2E?)
- [ ] Existe RLS nas tabelas Supabase?
- [ ] Como está organizada a estrutura de pastas?
- [ ] Existem camadas (repository, service, components)?
- [ ] Tem CI/CD configurado?
- [ ] Tem monitoramento/observabilidade?

```bash
# Auditoria de multi-tenancy: queries sem filtro user_id
grep -rn "\.from\(" src/ app/ --include="*.ts" | grep -v "\.eq.*user_id\|\.eq.*userId" | grep -v "test\|spec\|health\|ping"

# Auditoria de credenciais hardcoded: emails em código
grep -rn "@gmail\|@hotmail\|@empresa\|@seudominio" src/ app/ --include="*.ts" --include="*.tsx"

# Auditoria de createClient dentro de funções (não singleton)
grep -rn "createClient" src/ app/ --include="*.ts" | grep -v "^src/lib/supabase\|//\|test"
```

---

### Fase 2 — Gap Analysis por Dimensão IntelliX

Para cada dimensão abaixo, classifique: ✅ OK | ⚠️ Parcial | ❌ Ausente | 🔴 Crítico

#### Dimensão 1 — TypeScript & Qualidade de Código
- [ ] `strict: true` no `tsconfig.json`
- [ ] Zero uso de `any` explícito
- [ ] Tipos centralizados em `src/types/`
- [ ] Sem `// @ts-ignore` sem justificativa
- [ ] Naming conventions: kebab-case arquivos, PascalCase componentes, camelCase hooks

#### Dimensão 2 — Arquitetura de Camadas (Clean Architecture)
- [ ] Componentes não acessam Supabase diretamente
- [ ] Existe camada `repositories/` (acesso a dados)
- [ ] Existe camada `services/` (lógica de negócio)
- [ ] Route handlers usam services, não queries diretas
- [ ] Sem lógica de negócio em componentes React

#### Dimensão 3 — Banco de Dados & Supabase
- [ ] RLS ativo em TODAS as tabelas
- [ ] UUID + `gen_random_uuid()` como PKs
- [ ] `created_at` e `updated_at` em todas as tabelas
- [ ] Migrations versionadas em `supabase/migrations/`
- [ ] Sem queries N+1 (usar `select` com joins)
- [ ] Índices nas colunas de FK e filtros frequentes
- [ ] **[CRÍTICO]** Supabase client criado como singleton de módulo — não dentro de funções
- [ ] **[CRÍTICO]** IDs sequenciais usam PostgreSQL sequence ou UUID — nunca `COUNT(*) + 1`
- [ ] **[CRÍTICO]** Nenhum god-file de acesso a dados (>300 linhas com múltiplas responsabilidades)

#### Dimensão 4 — Frontend & UI
- [ ] App Router (não Pages Router)
- [ ] Server Components por padrão, Client só quando necessário
- [ ] Design system definido (tokens de cor, tipografia, espaçamento)
- [ ] Mobile-first em todos os componentes
- [ ] Loading states com Skeleton
- [ ] Error boundaries configurados
- [ ] Sem hardcode de cores (usar variáveis CSS/Tailwind tokens)

#### Dimensão 5 — API Design
- [ ] Formato de resposta padronizado (`{ data, error, meta }`)
- [ ] Validação Zod em todas as entradas
- [ ] Middleware de autenticação centralizado
- [ ] Tratamento de erro consistente (não leak de stack traces)
- [ ] Rate limiting em endpoints críticos

#### Dimensão 6 — State Management & Data Fetching
- [ ] TanStack Query para dados do servidor (client-side)
- [ ] Server Actions para mutations de formulário
- [ ] Sem `useEffect` para buscar dados (substituir por TanStack Query)
- [ ] Sem prop drilling excessivo (Zustand para estado global de UI)

#### Dimensão 7 — Segurança
- [ ] Headers de segurança no `next.config.ts`
- [ ] Middleware protegendo rotas autenticadas
- [ ] Sem secrets expostos no client-side
- [ ] `npm audit` com zero high/critical
- [ ] Sem `console.log` com dados em produção
- [ ] **[CRÍTICO]** Toda query multi-tenant tem `.eq("user_id", userId)` explícito — não depende só de RLS
- [ ] **[CRÍTICO]** Nenhuma string literal de email/ID usada como portão de autorização em API routes
- [ ] **[CRÍTICO]** `process.env.ADMIN_EMAIL` (ou equivalente) documentado no `.env.example`

#### Dimensão 8 — Testes
- [ ] Testes unitários para services e utilities (`vitest`)
- [ ] Testes de integração para API routes
- [ ] Testes E2E para fluxos críticos (`playwright`)
- [ ] Coverage mínima de 60% nas regras de negócio

#### Dimensão 9 — Observabilidade
- [ ] Error tracking (Sentry ou equivalente)
- [ ] Logging estruturado sem PII
- [ ] Audit log para ações críticas
- [ ] Core Web Vitals sendo monitorados

#### Dimensão 10 — DevOps & CI/CD
- [ ] GitHub Actions com test → build → deploy
- [ ] Branch protection em `main`
- [ ] Estratégia de ambientes (dev/staging/prod)
- [ ] Rollback procedure documentado
- [ ] Database migrations em CI

#### Dimensão 11 — Multi-tenancy
- [ ] **[CRÍTICO]** Toda tabela com dados de usuário tem coluna `user_id` FK para `auth.users`
- [ ] **[CRÍTICO]** Toda query de listagem filtra por `user_id` explicitamente (não só RLS)
- [ ] **[CRÍTICO]** Funções de acesso a dados aceitam `userId` como parâmetro — sem acessar contexto global
- [ ] **[CRÍTICO]** Nenhuma função global (ex: `syncAllLeads()` sem parâmetros) que retorne dados cross-tenant
- [ ] Credenciais de tenant (API keys, webhook URLs) armazenadas em tabela de configuração por tenant
- [ ] Testes verificam que tenant A não consegue ler dados do tenant B

---

### Fase 3 — Relatório de Gaps

Gere o relatório em `docs/intellix-audit-[data].md`:

```markdown
# IntelliX Code Audit — [Nome do Projeto]
**Data:** [data]
**Auditado por:** IntelliX Engineering Plugin v2.0

## Score Geral: [X]/100

| Dimensão | Score | Status |
|----------|-------|--------|
| TypeScript & Qualidade | X/10 | ✅/⚠️/❌ |
| Arquitetura de Camadas | X/10 | ... |
| Banco de Dados | X/10 | ... |
| Frontend & UI | X/10 | ... |
| API Design | X/10 | ... |
| State Management | X/10 | ... |
| Segurança | X/10 | ... |
| Testes | X/10 | ... |
| Observabilidade | X/10 | ... |
| DevOps & CI/CD | X/10 | ... |

## Críticos (resolver antes de qualquer nova feature)
[Lista de itens 🔴 encontrados]

## Alta Prioridade
[Lista de itens ❌ encontrados]

## Média Prioridade
[Lista de itens ⚠️ encontrados]

## Pontos Positivos
[Lista de itens ✅ encontrados]
```

---

### Fase 4 — Roadmap de Refatoração Priorizado

Organize as correções em sprints de refatoração:

```markdown
## Sprint 1 — Estabilização (itens críticos, sem novas features)
Estimativa: [N] dias

### Segurança Crítica
- [ ] Adicionar RLS na tabela [X] — risco: exposição de dados
- [ ] Remover service_role_key do client-side
- [ ] Adicionar middleware de auth em /dashboard/*

### TypeScript
- [ ] Habilitar strict mode no tsconfig.json
- [ ] Corrigir [N] erros de tipagem resultantes
- [ ] Centralizar tipos em src/types/index.ts

## Sprint 2 — Arquitetura (refatoração das camadas)
Estimativa: [N] dias

### Data Layer
- [ ] Criar src/repositories/ com [listar entidades]
- [ ] Criar src/services/ com [listar entidades]
- [ ] Mover queries dos componentes para repositories
- [ ] Mover lógica dos route handlers para services

## Sprint 3 — Qualidade (testes, observabilidade, DevOps)
Estimativa: [N] dias

### Testes
- [ ] Setup Vitest + configuração
- [ ] Testes unitários para services críticos
- [ ] Setup Playwright + smoke tests

### Observabilidade
- [ ] Instalar e configurar Sentry
- [ ] Implementar logger estruturado
- [ ] Configurar Core Web Vitals monitoring

### CI/CD
- [ ] Criar .github/workflows/ci.yml
- [ ] Configurar branch protection em main
- [ ] Configurar Preview Deployments no Vercel

## Sprint 4 — Evolução (melhorias de UX e performance)
Estimativa: [N] dias

### Frontend
- [ ] Migrar fetches em useEffect para TanStack Query
- [ ] Implementar loading skeletons
- [ ] Definir e aplicar design system
- [ ] Otimizar Server vs Client Components
```

---

### Fase 5 — Execução Guiada

Após validar o roadmap com o usuário, execute sprint por sprint usando as skills IntelliX:

| Sprint | Skills a usar |
|--------|---------------|
| Sprint 1 — Segurança Crítica | `intellix:security-observability` |
| Sprint 2 — Data Layer | `intellix:architecture` (Passos 5-7) |
| Sprint 2 — API Design | `intellix:architecture` (Passo 6) |
| Sprint 3 — TypeScript | `intellix:dev-standards` |
| Sprint 3 — Frontend | `intellix:frontend-design` |
| Sprint 3 — Integrações | `intellix:integration` |
| Sprint 4 — Testes | `intellix:test-e2e` |
| Sprint 4 — CI/CD | `intellix:deploy` (seção GitHub Actions) |
| Final — Deploy & Handoff | `intellix:deploy` + `intellix:handoff` |

---

## Princípio de Execução

**Refatorar sem quebrar features existentes:**

```
1. Escrever testes ANTES de refatorar (safety net)
2. Refatorar em pequenos incrementos verificáveis
3. Manter backward compatibility durante transição
4. Usar feature flags para mudanças de UI
5. Deploy incremental: um sprint de cada vez
```

**Regra de ouro: Boy Scout Rule**
> Sempre deixe o código melhor do que encontrou.
> Cada PR de refatoração deve melhorar pelo menos uma métrica do audit.

---

## Anti-Patterns de Refatoração

- ❌ "Big Bang Rewrite" → refatorar tudo de uma vez → sistema quebra em produção
- ❌ Refatorar sem testes → sem safety net → regressões invisíveis
- ❌ Misturar refatoração com novas features no mesmo PR → difícil de revisar
- ❌ Pular sprints → resolver performance antes de segurança → prioridade errada
- ❌ Documentar antes de estabilizar → docs ficam desatualizados rapidamente

---

## Handover

Após apresentar o relatório e o roadmap:
> "Audit concluído. Score: [X]/100. [N] itens críticos, [N] alta prioridade.
> Recomendo começar pelo Sprint 1 de estabilização antes de qualquer nova feature.
> Confirma que podemos iniciar? Vou guiar cada sprint usando as skills IntelliX."

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Executar refatoração de arquitetura | `intellix:architecture` |
| Refatorar frontend e design system | `intellix:frontend-design` |
| Implementar segurança pós-audit | `intellix:security-observability` |
| Setup de testes em projeto legado | `intellix:test-e2e` |
| Setup CI/CD e DevOps | `intellix:deploy` |
| Code review após refatoração | `superpowers:requesting-code-review` |
| Debug de comportamento inesperado ao refatorar | `superpowers:systematic-debugging` |
| Supabase — otimização de queries existentes | `supabase-postgres-best-practices` |
| React/Next.js — identificar antipatterns | `vercel-react-best-practices` |
