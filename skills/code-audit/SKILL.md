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

#### Dimensão 7 — Segurança & DevSecOps

**Segurança Base:**
- [ ] Headers de segurança no `next.config.ts` (CSP, HSTS, X-Frame-Options)
- [ ] Middleware protegendo rotas autenticadas
- [ ] Sem secrets expostos no client-side (`NEXT_PUBLIC_` com valores sensíveis)
- [ ] `npm audit` com zero high/critical
- [ ] Sem `console.log` com dados em produção
- [ ] **[CRÍTICO]** Toda query multi-tenant tem `.eq("user_id", userId)` explícito
- [ ] **[CRÍTICO]** Nenhuma string literal de email/ID como portão de autorização em API routes
- [ ] **[CRÍTICO]** `process.env.ADMIN_EMAIL` (ou equivalente) documentado no `.env.example`

**DevSecOps CI/CD:**
- [ ] `.github/workflows/security.yml` existe com Gitleaks + Semgrep + Trivy
- [ ] Gitleaks: zero secrets detectados no histórico git
- [ ] Semgrep: zero vulnerabilidades CRITICAL/HIGH
- [ ] Trivy: zero CVEs CRITICAL em dependências

**Segurança LLM** (verificar apenas se o projeto usa LLMs):
- [ ] `src/lib/ai/guardrails.ts` ou equivalente existe
- [ ] `prePromptFilter()` — sanitiza input antes de enviar ao modelo
- [ ] `postOutputValidator()` — sanitiza output antes de exibir ao usuário
- [ ] `redactPII()` aplicado antes de qualquer chamada LLM
- [ ] **[CRÍTICO]** Conta API comercial (OpenAI API / Anthropic API) — não conta de consumo
- [ ] Rate limiting por usuário/tenant em chamadas LLM
- [ ] Limite de tokens por request definido

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

#### Dimensão 12 — LGPD & Privacy by Design

```bash
# Verificar existência das tabelas LGPD
grep -rn "consent_records\|titular_requests\|data_processing_log" supabase/migrations/

# Verificar pii-redactor
find src -name "pii-redactor*" -o -name "pii_redactor*"

# Verificar se PII vai para logs
grep -rn "console\.\(log\|info\|warn\)" src/ app/ --include="*.ts" --include="*.tsx" | grep -i "cpf\|email\|phone\|nome\|name" | head -10
```

**Mapeamento de dados pessoais:**
- [ ] O sistema coleta dados pessoais? (nome, email, CPF, telefone, IP, comportamento)
  → SE SIM: todas as verificações abaixo se aplicam
- [ ] Dados sensíveis presentes? (saúde, biometria, religião, origem racial)
  → SE SIM: marcar como 🔴 CRÍTICO — regime de proteção reforçado

**Tabelas e Schema:**
- [ ] **[CRÍTICO se dados pessoais]** Tabela `consent_records` existe com RLS
- [ ] **[CRÍTICO se dados pessoais]** Tabela `titular_requests` existe com RLS e `deadline` de 15 dias
- [ ] Tabela `data_processing_log` existe para registrar decisões automatizadas (Art. 20)
- [ ] Todas as tabelas com PII têm RLS ativo

**Código:**
- [ ] `src/lib/lgpd/pii-redactor.ts` ou equivalente existe
- [ ] **[CRÍTICO se LLM + dados pessoais]** `redactPII()` invocado antes de toda chamada LLM
- [ ] PII não aparece em logs de produção (Sentry, Vercel, console)
- [ ] Soft delete implementado (sem exclusão física imediata de dados regulados)

**Compliance:**
- [ ] Base legal LGPD documentada por tabela/operação (Art. 7)
- [ ] Política de privacidade publicada e acessível
- [ ] Fluxo de exclusão de dados implementado (Art. 18, VI)
- [ ] Endpoint de exportação de dados existe (portabilidade — Art. 18, V)
- [ ] Plano de resposta a incidentes documentado (prazos: 2h/24h/3 dias ANPD)

---

### Fase 2b — Comandos de Auditoria DevSecOps

Execute estes comandos para medir o estado atual antes de gerar o relatório:

```bash
# 1. Verificar existência do pipeline CI/CD de segurança
ls -la .github/workflows/security.yml 2>/dev/null || echo "AUSENTE — adicionar no Sprint 0"

# 2. Verificar secrets hardcoded (amostra rápida)
grep -rn "sk-\|eyJ\|-----BEGIN\|api_key\s*=\|API_KEY\s*=" src/ app/ --include="*.ts" --include="*.tsx" | grep -v ".env\|process.env\|//\|test" | head -10

# 3. Verificar NEXT_PUBLIC com valores sensíveis
grep -rn "NEXT_PUBLIC_.*KEY\|NEXT_PUBLIC_.*SECRET\|NEXT_PUBLIC_.*TOKEN" src/ app/ next.config* --include="*.ts" --include="*.tsx" | head -10

# 4. Verificar uso de contas LLM de consumo (proibido com dados de clientes)
grep -rn "chat.openai.com\|claude.ai\|chatgpt" src/ app/ --include="*.ts" --include="*.tsx" | head -5

# 5. Verificar tabelas sem RLS
# (via Supabase MCP ou psql)
# SELECT tablename FROM pg_tables WHERE schemaname = 'public'
# EXCEPT
# SELECT tablename FROM pg_tables pt JOIN pg_class pc ON pt.tablename = pc.relname
# WHERE pc.relrowsecurity = true;

# 6. Verificar PII em chamadas LLM sem redação
grep -rn "\.create\|\.messages\.create\|\.chat\.completions" src/ app/ --include="*.ts" -l | xargs grep -l "cpf\|email\|phone\|nome\|telefone" 2>/dev/null | head -5

# 7. Verificar se lgpd-compliance está no projeto
ls -la references/lgpd* docs/lgpd* 2>/dev/null || echo "Sem documentação LGPD"
```

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
| Segurança & DevSecOps | X/10 | ... |
| Testes | X/10 | ... |
| Observabilidade | X/10 | ... |
| DevOps & CI/CD | X/10 | ... |
| Multi-tenancy | X/10 | ... |
| LGPD & Privacy | X/10 | ... |

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

### Fase 3b — DevSecOps Retrofit (executar para itens ausentes)

Quando o audit identificar lacunas de DevSecOps/LGPD, criar os arquivos faltantes **antes** de iniciar o Sprint 1. Esta fase é análoga ao Passo 4b do `/projeto novo` — aplica o mesmo scaffolding em projetos existentes.

#### Retrofit 1 — CI/CD de Segurança (SEMPRE, se ausente)

Criar `.github/workflows/security.yml`:

```yaml
name: DevSecOps Security Scan
on: [push, pull_request]
jobs:
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
        env: { GITHUB_TOKEN: '${{ secrets.GITHUB_TOKEN }}' }
  sast-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: "p/typescript p/owasp-top-ten p/nextjs"
  sca-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          format: "sarif"
          output: "trivy-results.sarif"
          severity: "CRITICAL,HIGH"
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with: { sarif_file: "trivy-results.sarif" }
```

> Custo zero. PRs com CRITICAL bloqueados. HIGH exige dispensa documentada.

---

#### Retrofit 2 — PII Redactor (se projeto usa LLM + dados pessoais)

Criar `src/lib/lgpd/pii-redactor.ts`:

```typescript
const PII_PATTERNS = [
  { regex: /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, token: '[CPF]' },
  { regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, token: '[EMAIL]' },
  { regex: /\b(\+55\s?)?(\(?\d{2}\)?\s?)?[\d\s\-]{8,}\b/g, token: '[TELEFONE]' },
  { regex: /\b\d{5}-?\d{3}\b/g, token: '[CEP]' },
]
export function redactPII(text: string): string {
  return PII_PATTERNS.reduce((acc, { regex, token }) => acc.replace(regex, token), text)
}
```

---

#### Retrofit 3 — Guardrails LLM (se projeto usa LLM)

Criar `src/lib/ai/guardrails.ts`:

```typescript
import { redactPII } from '@/lib/lgpd/pii-redactor'

const INJECTION_PATTERNS = [
  /ignore\s+(previous|all|above)\s+instructions/i,
  /you\s+are\s+now\s+(a|an)\s+/i,
  /system\s*:\s*you/i,
]

export function prePromptFilter(input: string): { safe: boolean; sanitized: string } {
  if (INJECTION_PATTERNS.some(p => p.test(input))) return { safe: false, sanitized: '' }
  return { safe: true, sanitized: redactPII(input) }
}

export function postOutputValidator(output: string): { valid: boolean; sanitized: string } {
  const LEAKS = [/you are (a|an) .+ assistant/i, /system prompt/i]
  if (LEAKS.some(p => p.test(output)))
    return { valid: false, sanitized: '[Resposta bloqueada por política de segurança]' }
  return { valid: true, sanitized: redactPII(output) }
}
```

Após criar, **localizar todas as chamadas LLM existentes** e adicionar os guardrails:

```bash
# Encontrar chamadas LLM sem guardrails
grep -rn "\.create\|messages\.create\|chat\.completions\|anthropic\." src/ app/ --include="*.ts" -l
```

Para cada arquivo encontrado: envolver o input com `prePromptFilter()` e o output com `postOutputValidator()`.

---

#### Retrofit 4 — Tabelas LGPD (se projeto tem dados pessoais e tabelas ausentes)

Criar `supabase/migrations/[timestamp]_lgpd_retrofit.sql` com o conteúdo das tabelas `consent_records`, `titular_requests` e `data_processing_log` + RLS (ver `lgpd-compliance` Seção 2 para o SQL completo).

Verificar se já existem antes de criar:
```bash
grep -rn "consent_records\|titular_requests" supabase/migrations/
```

---

#### Retrofit 5 — Atualizar `references/security.md`

Se o arquivo existe mas é a versão antiga (sem DevSecOps v2.0), substituí-lo pelo template atualizado em `intellix-templates/references-template/security.md`.

---

### Fase 4 — Roadmap de Refatoração Priorizado

Organize as correções em sprints de refatoração:

```markdown
## Sprint 0 — DevSecOps Retrofit (execução imediata, < 2h)
Estimativa: 1-2 horas
Não bloqueia novas features — executa em paralelo.

### CI/CD de Segurança
- [ ] Criar .github/workflows/security.yml (Retrofit 1)
- [ ] Executar primeira varredura: verificar alertas existentes

### LGPD & Privacidade (se dados pessoais presentes)
- [ ] Criar src/lib/lgpd/pii-redactor.ts (Retrofit 2)
- [ ] Criar tabelas LGPD no banco (Retrofit 4)
- [ ] Documentar bases legais por tabela no references/architecture.md

### Guardrails LLM (se projeto usa LLM)
- [ ] Criar src/lib/ai/guardrails.ts (Retrofit 3)
- [ ] Envolver chamadas LLM existentes com prePromptFilter + postOutputValidator

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
| **Sprint 0 — DevSecOps Retrofit** | Fase 3b desta skill (retrofits 1-5) |
| Sprint 1 — Segurança Crítica | `intellix:security-observability` + `lgpd-compliance` |
| Sprint 2 — Data Layer | `intellix:architecture` (Passos 5-7) |
| Sprint 2 — API Design | `intellix:architecture` (Passo 6) |
| Sprint 3 — TypeScript | `intellix:dev-standards` |
| Sprint 3 — Frontend | `intellix:frontend-design` |
| Sprint 3 — Integrações | `intellix:integration` |
| Sprint 2 — Migração de Tech Debt (se aplicável) | `deprecation-and-migration` |
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
>
> DevSecOps: [CI/CD security.yml: ✅/❌] | [LGPD tabelas: ✅/❌/N/A] | [Guardrails LLM: ✅/❌/N/A]
>
> Recomendo começar pelo **Sprint 0** (DevSecOps Retrofit — ~2h, não bloqueia features)
> em paralelo com o Sprint 1 de estabilização.
> Confirma que podemos iniciar? Vou guiar cada sprint usando as skills IntelliX."

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Executar refatoração de arquitetura | `intellix:architecture` |
| Refatorar frontend e design system | `intellix:frontend-design` |
| Implementar segurança técnica pós-audit | `intellix:security-observability` |
| Compliance LGPD, tabelas e direitos dos titulares | `lgpd-compliance` |
| Setup de testes em projeto legado | `intellix:test-e2e` |
| Setup CI/CD e DevOps | `intellix:deploy` |
| Code review após refatoração | `superpowers:requesting-code-review` |
| Debug de comportamento inesperado ao refatorar | `superpowers:systematic-debugging` |
| Supabase — otimização de queries existentes | `supabase-postgres-best-practices` |
| React/Next.js — identificar antipatterns | `vercel-react-best-practices` |
| Migrar dependências legadas, strangler pattern, zombie code | `deprecation-and-migration` |
