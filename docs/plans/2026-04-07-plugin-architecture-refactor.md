# IntelliX Plugin — Refatoração Arquitetural Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o plugin IntelliX profissional, lean e manutenível: corrigir contradição interna, desacoplar o god-document em referências focadas, eliminar numeração frágil de skills e documentar convenções de extensão.

**Architecture:** Cinco mudanças independentes em ordem de impacto: (1) corrigir contradição @ts-nocheck, (2) extrair MASTER-ARCHITECTURE.md em 7 arquivos de referência focados, (3) reescrever o master como índice de ~170 linhas, (4) renomear diretórios de skills removendo o prefixo numérico, (5) adicionar PLUGIN-CONVENTIONS.md como guia de extensão. Nenhuma das mudanças quebra funcionalidade — hooks e session-start.sh usam nomes semânticos, não caminhos de diretório.

**Tech Stack:** Markdown, Bash (renaming), plugin IntelliX v2.0

---

## Mapa de Arquivos

### Criados
- `references/four-commands.md` — detalhes completos dos 4 comandos (/spec /break /plan /execute)
- `references/anti-patterns.md` — §2b + §18 (anti-patterns que matam SaaS + armadilhas)
- `references/data-layer.md` — §5 + §6 + §7 (repository/service pattern, behavior isolation, schema)
- `references/api-standards.md` — §8 + §9 (API response RFC 7807, paginação cursor)
- `references/frontend-patterns.md` — §10 + §11 + §12 (TypeScript strict, naming, componentes)
- `references/security-rules.md` — §13 + §14 (segurança OWASP, estratégia de testes)
- `references/operations.md` — §3 + §15 + §16 + §17 (estrutura de pastas, env vars, init, deploy)
- `PLUGIN-CONVENTIONS.md` — guia de extensão do plugin (commands vs skills, sub-resources)

### Modificados
- `MASTER-ARCHITECTURE.md` — de 1200+ linhas → ~170 linhas (índice + princípios + workflow macro)
- `skills/04-dev-standards/SKILL.md` — corrigir hierarquia @ts-nocheck
- Diretórios de skills renomeados (13 renames, apenas cosmético)

### Inalterados
- `hooks/` — nenhuma mudança (referencia por nome semântico, não por path)
- `commands/` — nenhuma mudança
- Todos os `SKILL.md` das skills — nenhuma mudança de conteúdo

---

## Task 1: Corrigir contradição @ts-nocheck vs Princípio #4

> **Contexto:** Princípio #4 diz "nunca `@ts-ignore`" mas o fix de strictNullChecks adicionou
> `// @ts-nocheck` em 5 arquivos como solução prescrita. O plugin contradiz a si mesmo.
> Fix: diferenciar os dois casos na regra, introduzindo hierarquia clara de supressão.

**Files:**
- Modify: `MASTER-ARCHITECTURE.md` (linha 31 — Princípio #4)
- Modify: `skills/04-dev-standards/SKILL.md` (seção "Configuração TypeScript IntelliX")

- [ ] **Step 1: Atualizar Princípio #4 em MASTER-ARCHITECTURE.md**

Localizar a linha:
```
| 4 | **TypeScript Strict Zero-Any** | `any` é bloqueio absoluto — nunca use, nunca `@ts-ignore` |
```

Substituir por:
```markdown
| 4 | **TypeScript Strict Zero-Any** | `any` explícito = bloqueio absoluto. `@ts-ignore` inline = nunca (esconde bugs). `@ts-nocheck` em arquivo = permitido APENAS em legado com `// @ts-nocheck — TODO: remover — issue #N` e prazo definido |
```

- [ ] **Step 2: Atualizar a seção TypeScript em `skills/04-dev-standards/SKILL.md`**

Localizar o bloco abaixo da linha `**`strict: false` é bloqueio de PR.**`:

```markdown
Se herdou projeto com strict desativado:
1. Habilitar `strictNullChecks: true`
2. Corrigir `src/repositories/` e `src/services/` (camadas novas)
3. Adicionar `// @ts-nocheck` nos arquivos legados como marcador de dívida técnica
4. Criar issue para eliminar os `@ts-nocheck` progressivamente
```

Substituir por:
```markdown
**Hierarquia de supressão TypeScript (da mais aceitável à menos):**

| Supressão | Quando usar | Condição |
|-----------|-------------|----------|
| `// @ts-nocheck` no topo do arquivo | Arquivo legado herdado, migração incremental | Obrigatório: `// @ts-nocheck — TODO: remover — issue #N` |
| `// @ts-expect-error` na linha | Incompatibilidade de tipo com biblioteca de terceiros | Obrigatório: comentário explicando o porquê |
| `// @ts-ignore` | **NUNCA** — esconde bugs sem evidência | Bloqueio absoluto |
| `any` explícito | **NUNCA** | Bloqueio absoluto |

**Migração de projeto com strict desativado:**
1. Habilitar `strictNullChecks: true` no tsconfig.json
2. Corrigir erros nas camadas novas (`src/repositories/`, `src/services/`)
3. Para cada arquivo legado com erros: adicionar `// @ts-nocheck — TODO: remover — issue #N`
4. Criar issue rastreável para cada arquivo suprimido com prazo definido
5. Sprint de quitação de dívida: remover `@ts-nocheck` um arquivo por vez, corrigindo os erros
```

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add MASTER-ARCHITECTURE.md skills/04-dev-standards/SKILL.md
git commit -m "fix: corrigir contradição @ts-nocheck vs Princípio #4 — introduzir hierarquia de supressão"
```

---

## Task 2: Criar arquivos de referência — Grupo 1 (four-commands + anti-patterns)

> **Contexto:** MASTER-ARCHITECTURE.md tem 1200+ linhas. A seção §2 (Os 4 Comandos) tem 206 linhas
> com templates completos — é a seção mais longa e mais consultada. §2b (anti-patterns) tem 111 linhas.
> Extrair ambas preserva todo o conteúdo mas torna o master navegável.

**Files:**
- Create: `references/four-commands.md`
- Create: `references/anti-patterns.md`
- Modify: `MASTER-ARCHITECTURE.md` (substituir §2 e §2b por sumários de 5 linhas cada)

- [ ] **Step 1: Criar `references/four-commands.md`**

Criar o arquivo com o cabeçalho e copiar integralmente as linhas 63–267 de `MASTER-ARCHITECTURE.md`
(seção `## 2. Workflow de Implementação — Os 4 Comandos` até antes de `## 2b.`):

```markdown
# Os 4 Comandos IntelliX — Referência Completa

> Consulte este arquivo ao executar `/spec`, `/break`, `/plan` ou `/execute`.
> Referência rápida: `MASTER-ARCHITECTURE.md §2`

[COLAR AQUI: linhas 63–267 de MASTER-ARCHITECTURE.md — seção completa §2]
```

- [ ] **Step 2: Verificar que `references/four-commands.md` foi criado corretamente**

```bash
wc -l "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/references/four-commands.md"
```

Expected: ~210 linhas. Se menos de 200, o conteúdo foi truncado — reverificar.

- [ ] **Step 3: Criar `references/anti-patterns.md`**

Criar o arquivo com o cabeçalho e copiar:
- Linhas 269–379 de MASTER-ARCHITECTURE.md (seção §2b completa)
- Linhas 1155–1175 de MASTER-ARCHITECTURE.md (seção §18 — Armadilhas)

```markdown
# Anti-patterns IntelliX — O que NUNCA Fazer

> Estes erros foram identificados em code reviews reais.
> São sutis, não quebram em dev, explodem em produção.

[COLAR AQUI: §2b — Anti-patterns que Matam SaaS em Produção (linhas 269–379)]

---

[COLAR AQUI: §18 — Armadilhas — O que NUNCA fazer (linhas 1155–1175)]
```

- [ ] **Step 4: Substituir §2 no MASTER-ARCHITECTURE.md por sumário com link**

No MASTER-ARCHITECTURE.md, localizar:
```
## 2. Workflow de Implementação — Os 4 Comandos
```

Substituir TODO o bloco §2 (linhas 63–267) por:

```markdown
## 2. Workflow de Implementação — Os 4 Comandos

Para cada feature/módulo: `/spec` → `/break` → `/plan` → `/execute`. Nunca pule.

| Comando | Quando | O que faz |
|---------|--------|-----------|
| `/spec` | Início de feature | Cria/atualiza `SPEC.md` — O QUÊ, não o COMO |
| `/break` | Após SPEC aprovado | Cria `issues/` com behaviors atômicos ordenados |
| `/plan` | Antes de cada issue | Pesquisa codebase, preenche 7 seções, aguarda aprovação |
| `/execute` | Após plan aprovado | Implementa APENAS os arquivos do plano, roda checklist |

> **Referência completa (templates, exemplos, regras):** [`references/four-commands.md`](references/four-commands.md)
```

- [ ] **Step 5: Substituir §2b no MASTER-ARCHITECTURE.md por link**

Localizar `## 2b. Anti-patterns que Matam SaaS em Produção` e substituir TODO o bloco §2b (linhas 269–379) por:

```markdown
## 2b. Anti-patterns Críticos

Os 5 erros que destroem SaaS em produção: data leak multi-tenant, credencial hardcoded,
race condition em IDs, DB client por chamada, e sistemas coexistindo sem migração completa.

> **Referência completa com exemplos de código:** [`references/anti-patterns.md`](references/anti-patterns.md)
```

- [ ] **Step 6: Verificar que o master ainda compila (sem broken links)**

```bash
grep -n "\[COLAR AQUI\]" "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/MASTER-ARCHITECTURE.md"
```

Expected: nenhuma saída. Se houver, o conteúdo não foi substituído corretamente.

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add references/four-commands.md references/anti-patterns.md MASTER-ARCHITECTURE.md
git commit -m "refactor: extrair §2 e §2b para references/ — master passa a ser índice"
```

---

## Task 3: Criar arquivos de referência — Grupo 2 (data-layer + api-standards + frontend-patterns)

> **Contexto:** Seções §5–§12 do MASTER-ARCHITECTURE.md cobrem data layer, behavior isolation,
> schema, API response, paginação, TypeScript, naming e componentes — 570 linhas de conteúdo
> técnico especializado que raramente precisam ser lidas juntas.

**Files:**
- Create: `references/data-layer.md`
- Create: `references/api-standards.md`
- Create: `references/frontend-patterns.md`
- Modify: `MASTER-ARCHITECTURE.md` (substituir §5–§12 por sumários)

- [ ] **Step 1: Criar `references/data-layer.md`**

```markdown
# Data Layer — Repository, Service & Schema

> Padrões IntelliX para acesso a dados, regras de negócio e banco de dados.
> Referência obrigatória ao criar qualquer `*.repository.ts` ou `*.service.ts`.

[COLAR AQUI: §5 — Data Layer — Repository + Service Pattern (linhas 556–665)]

---

[COLAR AQUI: §6 — Behavior Isolation — Comunicação Entre Módulos (linhas 666–698)]

---

[COLAR AQUI: §7 — Schema de Banco de Dados — Padrão IntelliX (linhas 699–769)]
```

- [ ] **Step 2: Criar `references/api-standards.md`**

```markdown
# API Standards — Response Format & Pagination

> Padrão RFC 7807 para todas as API routes do projeto.
> Referência obrigatória ao criar qualquer `route.ts`.

[COLAR AQUI: §8 — API Response — Formato Padronizado RFC 7807 (linhas 770–847)]

---

[COLAR AQUI: §9 — Paginação Cursor-Based (linhas 848–888)]
```

- [ ] **Step 3: Criar `references/frontend-patterns.md`**

```markdown
# Frontend Patterns — TypeScript, Naming & Components

> Padrões IntelliX para código TypeScript, nomenclatura e estrutura de componentes.
> Referência obrigatória ao criar qualquer `.tsx` ou hook.

[COLAR AQUI: §10 — TypeScript Strict — Regras Absolutas (linhas 889–917)]

---

[COLAR AQUI: §11 — Naming Conventions (linhas 918–937)]

---

[COLAR AQUI: §12 — Estrutura de Componentes (linhas 938–986)]
```

- [ ] **Step 4: Substituir §5–§12 no MASTER-ARCHITECTURE.md por sumários com links**

No MASTER-ARCHITECTURE.md, localizar `## 5. Data Layer` e substituir TODO o bloco §5–§12
(linhas 556–986) por:

```markdown
## 5–12. Referências Técnicas

| Tópico | Quando consultar | Arquivo |
|--------|-----------------|---------|
| Repository pattern, Service layer, Schema SQL, Behavior isolation | Ao criar acesso a dados | [`references/data-layer.md`](references/data-layer.md) |
| API Response RFC 7807, Paginação cursor-based | Ao criar Route Handlers | [`references/api-standards.md`](references/api-standards.md) |
| TypeScript strict, Naming conventions, Estrutura de componentes | Ao criar `.tsx` ou hooks | [`references/frontend-patterns.md`](references/frontend-patterns.md) |
```

- [ ] **Step 5: Verificar linha count do master após as remoções**

```bash
wc -l "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/MASTER-ARCHITECTURE.md"
```

Expected: < 600 linhas (era 1200+). Se ainda acima de 700, seção não foi removida completamente.

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add references/data-layer.md references/api-standards.md references/frontend-patterns.md MASTER-ARCHITECTURE.md
git commit -m "refactor: extrair §5–§12 para references/ — data-layer, api-standards, frontend-patterns"
```

---

## Task 4: Criar arquivos de referência — Grupo 3 (security-rules + operations)

> **Contexto:** Seções §13–§17 cobrem segurança, testes, env vars, inicialização e deploy.
> São consultas pontuais — ninguém lê segurança e deploy juntos. Separar em dois arquivos
> focados: segurança+testes (lidos juntos) e operações (lidos juntos).

**Files:**
- Create: `references/security-rules.md`
- Create: `references/operations.md`
- Modify: `MASTER-ARCHITECTURE.md` (substituir §3 e §13–§17 por links)

- [ ] **Step 1: Criar `references/security-rules.md`**

```markdown
# Security Rules & Testing Strategy

> Checklist de segurança OWASP e estratégia de testes IntelliX.
> Executar Fase 06 (security) e Fase 07 (testes) com base neste documento.

[COLAR AQUI: §13 — Segurança — Checklist por Nível (linhas 987–1028)]

---

[COLAR AQUI: §14 — Testes — Estratégia por Camada (linhas 1029–1045)]
```

- [ ] **Step 2: Criar `references/operations.md`**

```markdown
# Operations — Estrutura, Variáveis de Ambiente, Inicialização & Deploy

> Referência para: scaffolding de novo projeto, configuração de ambiente e checklist de deploy.
> Consultar na Fase 00 (kickoff) e Fase 08 (deploy).

[COLAR AQUI: §3 — Estrutura de Pastas Canônica (linhas 380–502)]

---

[COLAR AQUI: §15 — Variáveis de Ambiente (linhas 1046–1079)]

---

[COLAR AQUI: §16 — Inicialização de Projeto (linhas 1080–1121)]

---

[COLAR AQUI: §17 — Deploy Checklist (linhas 1122–1154)]
```

- [ ] **Step 3: Substituir §3 no MASTER-ARCHITECTURE.md por link**

Localizar `## 3. Estrutura de Pastas Canônica` e substituir o bloco §3 (linhas 380–502) por:

```markdown
## 3. Estrutura de Pastas Canônica

Estrutura padronizada IntelliX para Next.js 15 App Router com TypeScript, Supabase e Vercel.
Inclui `.claude/agents/`, `references/`, `issues/`, `src/app/`, `src/components/`, `src/lib/`.

> **Estrutura completa com regras por pasta:** [`references/operations.md`](references/operations.md)
```

- [ ] **Step 4: Substituir §13–§17 no MASTER-ARCHITECTURE.md por links**

Localizar `## 13. Segurança` e substituir TODO o bloco §13–§17 (linhas 987–1154) por:

```markdown
## 13–17. Operações & Segurança

| Tópico | Quando consultar | Arquivo |
|--------|-----------------|---------|
| Segurança OWASP, rate limiting, headers, LGPD | Fase 06 (security) | [`references/security-rules.md`](references/security-rules.md) |
| Estratégia de testes: unit, integration, E2E | Fase 07 (testes) | [`references/security-rules.md`](references/security-rules.md) |
| Estrutura de pastas, env vars, init, deploy | Fase 00 e 08 | [`references/operations.md`](references/operations.md) |
```

- [ ] **Step 5: Verificar linha count final do master**

```bash
wc -l "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/MASTER-ARCHITECTURE.md"
```

Expected: entre 150 e 250 linhas. Esse é o target.

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add references/security-rules.md references/operations.md MASTER-ARCHITECTURE.md
git commit -m "refactor: extrair §3 e §13–§17 para references/ — security-rules, operations"
```

---

## Task 5: Atualizar seção §19 do MASTER-ARCHITECTURE.md como índice navegável

> **Contexto:** §19 "Arquivos de Referência por Projeto" ainda descreve os arquivos
> de referência DO PROJETO (references/architecture.md, DESIGN.md, etc.). Agora existe
> também o conceito de referências DO PLUGIN (os arquivos que acabamos de criar).
> Reescrever §19 como índice claro dos dois tipos.

**Files:**
- Modify: `MASTER-ARCHITECTURE.md` — reescrever §19

- [ ] **Step 1: Ler o §19 atual**

```bash
sed -n '1176,1191p' "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/MASTER-ARCHITECTURE.md"
```

- [ ] **Step 2: Substituir §19 pelo novo índice duplo**

Localizar `## 19. Arquivos de Referência por Projeto` e substituir o bloco completo por:

```markdown
## 19. Índice de Referências

### Referências do Plugin IntelliX (regras e padrões globais)

| Arquivo | Conteúdo | Quando consultar |
|---------|----------|-----------------|
| [`references/four-commands.md`](references/four-commands.md) | Templates completos de /spec /break /plan /execute | Ao executar qualquer comando do workflow |
| [`references/anti-patterns.md`](references/anti-patterns.md) | Anti-patterns que destroem SaaS + armadilhas comuns | Code review e design de features |
| [`references/data-layer.md`](references/data-layer.md) | Repository pattern, Service, Schema SQL, Behavior isolation | Ao criar acesso a dados |
| [`references/api-standards.md`](references/api-standards.md) | API Response RFC 7807, Paginação cursor-based | Ao criar Route Handlers |
| [`references/frontend-patterns.md`](references/frontend-patterns.md) | TypeScript strict, Naming, Estrutura de componentes | Ao criar `.tsx` ou hooks |
| [`references/security-rules.md`](references/security-rules.md) | Segurança OWASP, Estratégia de testes | Fases 06 e 07 |
| [`references/operations.md`](references/operations.md) | Estrutura de pastas, Env vars, Init, Deploy | Fases 00 e 08 |

### Referências por Projeto (criadas no kickoff de cada projeto)

| Arquivo | Conteúdo |
|---------|----------|
| `references/architecture.md` | Decisões de arquitetura específicas do projeto |
| `references/DESIGN.md` | Design system: tokens, paleta, tipografia |
| `references/workflow.md` | Resumo do workflow em formato de referência rápida |
| `references/specification.md` | Template de SPEC.md e issues/ para o time |
```

- [ ] **Step 3: Verificar que todos os links de referência existem**

```bash
ls "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/references/"
```

Expected: `four-commands.md  anti-patterns.md  data-layer.md  api-standards.md  frontend-patterns.md  security-rules.md  operations.md`

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add MASTER-ARCHITECTURE.md
git commit -m "docs: reescrever §19 como índice duplo — referências do plugin + referências por projeto"
```

---

## Task 6: Renomear diretórios de skills (remover prefixo numérico)

> **Contexto:** A numeração `00-`, `00b-`, `01-` etc. é frágil — inserir nova skill entre
> 05 e 06 gera `05b-`. Os hooks e session-start.sh usam nomes semânticos (`intellix:code-audit`),
> não caminhos de diretório. Renomear é seguro e elimina o hack `00b`.
>
> **VERIFICAÇÃO PRÉVIA OBRIGATÓRIA:** Confirmar que nenhum arquivo usa o path do diretório.

**Files:**
- Modify: `skills/` — renomear 13 diretórios

- [ ] **Step 1: Verificar que não há referências hardcoded aos paths dos diretórios**

```bash
grep -rn "00-master\|00b-code\|01-arch\|02-front\|03-agent\|04-dev\|05-int\|06-sec\|07-test\|08-dep\|09-proj\|10-live" \
  "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/" 2>/dev/null
```

Expected: nenhuma saída. Se houver saída, NÃO prosseguir — investigar antes.

- [ ] **Step 2: Executar os renames**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/skills"

mv "00-master-workflow"   "master-workflow"
mv "00-project-kickoff"   "project-kickoff"
mv "00b-code-audit"       "code-audit"
mv "01-architecture"      "architecture"
mv "02-frontend-design"   "frontend-design"
mv "03-agent-creation"    "agent-creation"
mv "04-dev-standards"     "dev-standards"
mv "05-integration"       "integration"
mv "06-security-observability" "security-observability"
mv "07-test-e2e"          "test-e2e"
mv "08-deploy"            "deploy"
mv "09-project-handoff"   "project-handoff"
mv "10-live-chat"         "live-chat"
```

- [ ] **Step 3: Verificar que os SKILL.md ainda existem nos novos paths**

```bash
find "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/skills" -name "SKILL.md" | sort
```

Expected: 11 linhas com paths usando os novos nomes sem prefixo numérico.

- [ ] **Step 4: Verificar que os hooks ainda funcionam (referem por nome, não por path)**

```bash
grep -n "suggest\|intellix:" \
  "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/hooks/scripts/skill-router.sh" | head -10
```

Expected: todas as referências são `suggest "code-audit"`, `suggest "architecture"` etc. — sem path de diretório.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add skills/
git commit -m "refactor: remover prefixo numérico dos diretórios de skills — eliminar hack 00b"
```

---

## Task 7: Adicionar PLUGIN-CONVENTIONS.md

> **Contexto:** Sem convenções documentadas, futuros contribuidores (ou a IA) não sabe:
> (1) quando criar um command vs uma skill, (2) quando adicionar sub-resources/,
> (3) como nomear e estruturar uma nova skill, (4) como atualizar o session-start.sh.
> Um arquivo de 1 página elimina essa ambiguidade sem burocracia.

**Files:**
- Create: `PLUGIN-CONVENTIONS.md`

- [ ] **Step 1: Criar `PLUGIN-CONVENTIONS.md`**

```markdown
# IntelliX Plugin — Convenções de Extensão

Guia de 1 página para quem vai adicionar ou modificar o plugin.
Leia antes de criar qualquer arquivo novo.

---

## commands/ vs skills/ — Quando usar cada um

| | `commands/` | `skills/` |
|--|------------|-----------|
| **Invocado por** | Usuário via `/comando` no Claude Code | Claude internamente via `Skill("intellix:nome")` |
| **Gatilho** | Explícito (usuário digita o comando) | Implícito (skill-router.sh detecta intenção) ou por chamada direta |
| **Responsabilidade** | Thin wrapper — apenas diz "use a skill X" | Contém o conhecimento e as instruções reais |
| **Exemplo** | `commands/audit.md` → chama `intellix:code-audit` | `skills/code-audit/SKILL.md` → executa o audit |

**Regra:** Todo command DEVE ter uma skill correspondente. Skills podem existir sem command.
Se algo precisa de atalho de usuário → crie o command. Se é orquestração interna → só skill.

---

## Quando criar sub-resources/ em uma skill

| Situação | Abordagem |
|----------|-----------|
| A skill cabe em um `SKILL.md` de < 300 linhas | Só `SKILL.md` — sem subpastas |
| A skill tem exemplos, schemas ou templates reutilizáveis | `SKILL.md` + `resources/` |
| A skill tem múltiplos modos (ex: GPT Maker vs n8n vs Blueprint) | `SKILL.md` + `resources/` com subpastas por modo |

**Estrutura quando usar resources/:**
```
skills/nome-da-skill/
  SKILL.md                    ← instrução principal
  resources/
    examples/                 ← exemplos de input/output (JSON, MD)
    templates/                ← templates prontos para uso
    references/               ← documentação de apoio
    schemas/                  ← schemas de validação
```

Nunca criar recursos soltos fora de `resources/`. Nunca criar `resources/` vazia.

---

## Como adicionar uma nova skill

1. **Criar o diretório:** `skills/nome-semantico/` — sem número, sem prefixo
2. **Criar `SKILL.md`** com frontmatter obrigatório:

```markdown
---
name: nome-da-skill
description: >
  Uma frase clara do que esta skill faz e QUANDO deve ser invocada.
  Inclua os gatilhos de linguagem natural que ativam esta skill.
user-invocable: false  # true se o usuário pode chamar diretamente
---

# Título da Skill

[conteúdo]
```

3. **Adicionar ao skill-router.sh** se precisar de detecção automática:

```bash
# Adicionar ao final de hooks/scripts/skill-router.sh antes do exit 0:
echo "$PROMPT" | grep -qiE "palavra1|palavra2|frase gatilho" && suggest "nome-da-skill"
```

4. **Adicionar ao session-start.sh** na lista `<intellix-phases>` se for uma fase do workflow.

5. **Adicionar ao `skills/master-workflow/SKILL.md`** na tabela de fases.

6. **Criar command** em `commands/nome.md` se precisar de atalho de usuário.

---

## Como atualizar MASTER-ARCHITECTURE.md

`MASTER-ARCHITECTURE.md` é um **índice**, não um manual. Não adicione conteúdo longo nele.

| O que fazer | Como |
|-------------|------|
| Adicionar Princípio Inviolável | Adicionar linha na tabela §0b |
| Adicionar anti-pattern de código | Adicionar em `references/anti-patterns.md` |
| Documentar padrão de data layer | Adicionar em `references/data-layer.md` |
| Documentar padrão de API | Adicionar em `references/api-standards.md` |
| Documentar regra de frontend | Adicionar em `references/frontend-patterns.md` |
| Documentar regra de segurança | Adicionar em `references/security-rules.md` |
| Documentar padrão operacional | Adicionar em `references/operations.md` |
| Documentar os 4 comandos | Adicionar em `references/four-commands.md` |

**Regra de ouro:** Se você está tentando adicionar mais de 10 linhas ao MASTER-ARCHITECTURE.md,
provavelmente o conteúdo pertence a um arquivo de references/.

---

## Versionamento do plugin

O plugin não tem semver formal ainda. Como controle mínimo:

- `plugin.json` tem campo `"version"` — incrementar quando houver mudança breaking
- Mudanças adicionais (novos princípios, novas skills) → incrementar `patch`
- Mudanças que reorganizam estrutura (como esta refatoração) → incrementar `minor`
- Mudanças que quebram nomes de skills existentes → incrementar `major`
```

- [ ] **Step 2: Verificar que o arquivo foi criado**

```bash
wc -l "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/PLUGIN-CONVENTIONS.md"
```

Expected: entre 80 e 120 linhas.

- [ ] **Step 3: Atualizar plugin.json — incrementar minor version**

Ler o plugin.json:
```bash
grep "version" "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/.claude-plugin/plugin.json"
```

Editar o campo version de `"2.0"` para `"2.1"` (ou incrementar o minor existente):
```json
"version": "2.1"
```

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/Dell/.claude/plugins/marketplaces/intellix-plugin"
git add PLUGIN-CONVENTIONS.md .claude-plugin/plugin.json
git commit -m "docs: adicionar PLUGIN-CONVENTIONS.md — guia de extensão do plugin"
```

---

## Resultado Esperado

Após as 7 tasks, o plugin terá:

```
intellix-plugin/
├── MASTER-ARCHITECTURE.md        ← ~200 linhas (era 1200+)
├── PLUGIN-CONVENTIONS.md         ← NOVO — guia de extensão
├── references/
│   ├── four-commands.md          ← NOVO — /spec /break /plan /execute completo
│   ├── anti-patterns.md          ← NOVO — anti-patterns + armadilhas
│   ├── data-layer.md             ← NOVO — repository, service, schema
│   ├── api-standards.md          ← NOVO — RFC 7807, paginação
│   ├── frontend-patterns.md      ← NOVO — TypeScript, naming, componentes
│   ├── security-rules.md         ← NOVO — OWASP, testes
│   └── operations.md             ← NOVO — folder structure, env, deploy
├── skills/
│   ├── master-workflow/          ← renomeado (era 00-master-workflow)
│   ├── project-kickoff/          ← renomeado (era 00-project-kickoff)
│   ├── code-audit/               ← renomeado (era 00b-code-audit)
│   ├── architecture/             ← renomeado (era 01-architecture)
│   ├── frontend-design/          ← renomeado (era 02-frontend-design)
│   ├── agent-creation/           ← renomeado (era 03-agent-creation)
│   ├── dev-standards/            ← renomeado (era 04-dev-standards)
│   ├── integration/              ← renomeado (era 05-integration)
│   ├── security-observability/   ← renomeado (era 06-security-observability)
│   ├── test-e2e/                 ← renomeado (era 07-test-e2e)
│   ├── deploy/                   ← renomeado (era 08-deploy)
│   ├── project-handoff/          ← renomeado (era 09-project-handoff)
│   └── live-chat/                ← renomeado (era 10-live-chat)
├── commands/                     ← inalterado
├── hooks/                        ← inalterado (funciona por nome semântico)
└── .claude-plugin/plugin.json    ← versão bumped para 2.1
```

**O que muda para quem usa:**
- Princípio #4 agora tem hierarquia clara de supressão (sem contradição)
- MASTER-ARCHITECTURE.md abre em 5 segundos, não em 5 minutos de scroll
- Nova skill → saber exatamente onde e como adicionar (PLUGIN-CONVENTIONS.md)
- Skills têm nomes limpos e semânticos
- Hooks e session-start.sh: **zero mudança** — continuam funcionando identicamente

---

## Self-Review

### Spec coverage
- ✅ Contradição @ts-nocheck → Task 1
- ✅ MASTER-ARCHITECTURE.md god document → Tasks 2, 3, 4, 5
- ✅ Numeração frágil de skills → Task 6
- ✅ commands/ vs skills/ sem distinção → Task 7
- ✅ Sub-resources sem convenção → Task 7
- ✅ "Plugin não come o próprio dog food" → parcialmente — PLUGIN-CONVENTIONS.md é a documentação de contribuição que o plugin precisava. Testes do plugin em si ficam fora do escopo desta refatoração.

### Placeholder scan
Sem placeholders — cada step tem instrução exata.

### Verificação de impacto zero nos hooks
Task 6 Step 1 verifica explicitamente que não há referência hardcoded a paths de diretório antes de fazer qualquer rename. Se encontrar referência, o plano para e investiga.
