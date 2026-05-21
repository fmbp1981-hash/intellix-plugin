# Os 4 Comandos IntelliX — Referência Completa

> Consulte este arquivo ao executar `/spec`, `/break`, `/plan` ou `/execute`.
> Índice: [`MASTER-ARCHITECTURE.md §2`](../MASTER-ARCHITECTURE.md)

---

## 2. Workflow de Implementação — Os 4 Comandos

Para cada feature/módulo, execute esta sequência. **Nunca pule etapas.**

```
Ideia/Requisito
     ↓
  /spec ──→ SPEC.md aprovado pelo usuário
     ↓
  /break ──→ issues/ ordenadas e aprovadas
     ↓
  /plan [issue] ──→ plano com 7 seções aprovado
     ↓
  /execute [issue] ──→ checklist verde
     ↓
  (repetir /plan + /execute para cada issue)
     ↓
  Deploy
```

### /spec — Especificação Formal

**Quando:** Início de projeto ou qualquer feature nova de porte.
**Gatilhos:** "quero criar", "nova feature", "novo módulo", "vou construir".

**Ação:** Criar ou atualizar `SPEC.md` na raiz:

```markdown
# [Nome do Projeto ou Feature]

## Overview
[O que faz em 2-3 linhas. O QUÊ existe, não o COMO implementar]

## [/rota-da-pagina]
[Propósito desta rota]

### Components
- **NomeEmPascalCase**: [O que renderiza e sua responsabilidade única]

### Behaviors
- **nome-em-kebab-case**: [O que acontece quando o usuário faz esta ação]
```

**Regras do SPEC.md:**
- Componentes em `PascalCase`, behaviors em `kebab-case`
- Cada behavior deve ser atômico o suficiente para virar uma issue isolada
- Descreva o QUÊ, nunca o COMO
- Apresente ao usuário e aguarde aprovação antes de continuar

---

### /break — Quebra em Issues Atômicas

**Quando:** Após SPEC.md aprovado.

**Ação:** Criar arquivo `.md` por behavior em `issues/`:

```
issues/
  01-implement-[pagina]-prototype.md        ← UI sem lógica (dados mockados)
  02-implement-[pagina2]-prototype.md       ← UI sem lógica
  03-implement-[behavior-1].md              ← behavior funcional completo
  04-implement-[behavior-2].md              ← behavior funcional completo
  05-implement-[integracao-externa].md      ← integrações após behaviors
```

**Ordem obrigatória de implementação:**
1. Protótipos de UI (páginas e componentes sem lógica)
2. Schema de banco (migrations)
3. Contratos e queries compartilhadas (`lib/`)
4. Behaviors funcionais (lógica + server actions + testes)
5. Integrações externas (APIs de terceiros)

**Exemplo real de issues/ para um app de chat:**
```
issues/
  01-implement-sidebar-prototype.md
  02-implement-new-page-prototype.md
  03-implement-chat-page-prototype.md
  04-implement-list-chats-in-sidebar.md
  05-implement-search-chats-in-sidebar.md
  06-implement-delete-chat-in-sidebar.md
  07-implement-rename-chat-in-sidebar.md
  08-implement-star-chat-in-sidebar.md
  09-implement-new-chat-in-new-page.md
  10-implement-send-message-in-chat-page.md
  11-implement-stream-response-in-chat-page.md
  12-implement-stop-streaming-in-chat-page.md
```
Cada comportamento e cada página vira uma issue separada.

**Conteúdo mínimo da issue neste momento:**
```markdown
# Implement [nome-do-behavior] in [/rota]

[Descrição em 1-2 linhas do que esta issue entrega]
```
O `/plan` completa o detalhamento técnico com as 7 seções.

**Regra:** Issue que parece grande demais para uma sessão → quebre mais.
Apresente ao usuário e aguarde confirmação da ordem antes de continuar.

---

### /plan [issue] — Pesquisa e Planejamento

**Quando:** Antes de implementar qualquer issue. Nunca pule.

**Sequência obrigatória:**
1. Ler a issue especificada
2. **Pesquisa em 3 frentes (obrigatório antes de planejar):**
   - **Frente 1 — Codebase interna:** buscar com glob/grep por componentes, hooks, actions e utilities já existentes. Nunca duplicar o que já existe.
   - **Frente 2 — Documentação oficial:** consultar docs de Next.js, Supabase, Shadcn etc. para padrões comprovados — não inventar o que já está documentado.
   - **Frente 3 — Repos de referência (hack poderoso):** se a issue envolve padrão complexo (auth, pagamentos, realtime), clonar repo aberto com solução similar para `.temp/`, ler, absorver padrões, deletar `.temp/` depois.
3. Consultar `MASTER-ARCHITECTURE.md` e `references/DESIGN.md`
4. Preencher as 7 seções obrigatórias na issue
5. Apresentar ao usuário e aguardar aprovação explícita
6. **NÃO escrever código ainda**
7. **`/clear` antes de `/execute`** — após o PRD/plan aprovado, limpe o contexto. A pesquisa poluiu a janela com logs e arquivos lidos. O plano aprovado substitui tudo isso com 1/10 dos tokens.

**Template da issue completa (7 seções):**

```markdown
# Implement [nome] in [/rota]

[Descrição técnica atualizada]

# Functional Specification

## Behavior: [nome-do-behavior]
File: `app/(pages)/[rota]/behaviors/[nome-do-behavior]/`

[Descrição do comportamento]

### Preconditions
* [Condição necessária para executar]

### Happy Path

#### Input
[O que dispara este behavior]

#### Workflow
* [Passo 1]
* [Passo 2]

#### Output
[O que o usuário vê como resultado]

### Edge Cases
[Cenários de borda e como tratar]

### Error Cases
[Cenários de erro e como tratar]

## Database Schema
| Coluna | Tipo | Descrição |
|--------|------|-----------|
[Omitir seção se não houver alteração no banco]

## Files

### Files to Create
* `caminho/exato/arquivo.ts` — [O que este arquivo contém]

### Files to Modify
* `caminho/exato/arquivo.ts` — [O que será alterado e por quê]

### Files to NOT Touch
* `caminho/de/behavior-vizinho/*` — (issue separada)
* `lib/modulo-existente/*` — (apenas importar, não modificar)

## External Dependencies
* [Pacote necessário. Omitir se nenhum]

## Notes
[Decisões de arquitetura, advertências, dependências entre issues]

## Tasks
- [ ] [Tarefa de implementação 1]
- [ ] [Tarefa de implementação 2]
- [ ] Escrever testes para [behavior]
- [ ] Confirmar: nenhum arquivo fora da lista acima foi modificado
```

**Escalada:** Plano > 10 arquivos → sinalize ao usuário. Issue precisa ser quebrada.

---

### /execute [issue] — Execução com Review em Dois Estágios

**Quando:** Somente após aprovação explícita do `/plan`.

O `/execute` usa um ciclo de **agente especializado → spec review → quality review** por arquivo/task.
Cada arquivo da seção "Files" do plano passa por 3 estágios antes de ser marcado como concluído.

---

#### Pré-execução (uma vez por issue)

1. Ler a issue com plano aprovado
2. Consultar `MASTER-ARCHITECTURE.md` e `references/DESIGN.md`
3. Extrair todos os arquivos das seções "Files to Create" e "Files to Modify"
4. Para cada arquivo, identificar o agente correto (ver tabela em `MASTER-ARCHITECTURE.md §4`)
5. Criar lista de tasks no TodoWrite: um item por arquivo

---

#### Ciclo por arquivo/task

```
Para cada arquivo na lista "Files":

  ESTÁGIO 1 — Implementação (agente tipado)
  ─────────────────────────────────────────
  Dispatch: agente correto para o tipo de arquivo
  Contexto fornecido:
    - Spec completa da issue (seção Functional Specification)
    - Caminho exato do arquivo e o que deve conter
    - references/architecture.md do projeto
    - references/DESIGN.md (se .tsx)
    - forbidden_paths do agente (não herdar contexto da sessão)
  O agente: implementa → roda testes → faz self-review → reporta

  ESTÁGIO 2 — Spec Review (subagente revisor)
  ─────────────────────────────────────────────
  Dispatch: subagente spec-reviewer com:
    - A spec da issue (Happy Path + Edge Cases + Error Cases)
    - O diff do arquivo implementado
  O revisor responde: ✅ APROVADO ou ❌ GAPS com lista exata
  Se ❌ → agente implementador corrige → spec review repete
  Avança para Estágio 3 somente com ✅

  ESTÁGIO 3 — Quality Review (subagente revisor)
  ─────────────────────────────────────────────────
  Dispatch: subagente code-quality-reviewer com:
    - O diff do arquivo
    - Padrões IntelliX: TypeScript strict, zero any, Zod, naming conventions
  O revisor responde: ✅ APROVADO ou ❌ ISSUES com prioridade (Critical/Important/Minor)
  Se ❌ Critical ou Important → agente implementador corrige → quality review repete
  Minor → registrar como nota, não bloqueia

  ✅ Arquivo concluído → marcar no TodoWrite → próximo arquivo
```

---

#### Tabela: Agente por Tipo de Arquivo

| Arquivo | Agente | Contexto obrigatório |
|---------|--------|---------------------|
| `.tsx` (componente/página) | `component-writer` | architecture.md + DESIGN.md |
| `actions.ts` (Server Action) | `action-writer` | architecture.md |
| `use-*.ts` (hook) | `hook-writer` | architecture.md |
| `route.ts` (Route Handler) | `route-writer` | architecture.md + api-standards.md |
| `*.sql` / tipos (schema) | `model-writer` | architecture.md + data-layer.md |
| SDK / webhook / integração | `integration-writer` | architecture.md |
| `*.test.ts` | `test-writer` | architecture.md + spec da issue |

---

#### Prompt padrão — Spec Reviewer

```
Você é um spec-reviewer. Sua única tarefa é verificar se o código implementado
atende à spec fornecida. Não avalie qualidade de código, apenas conformidade com spec.

SPEC:
[colar seções: Happy Path, Edge Cases, Error Cases da issue]

CÓDIGO IMPLEMENTADO:
[colar diff ou conteúdo do arquivo]

Responda com uma das duas opções:
✅ APROVADO — o código atende todos os requisitos da spec.
❌ GAPS — liste exatamente o que está faltando ou errado, um item por linha.
Não adicione sugestões além do que a spec pede.
```

---

#### Prompt padrão — Code Quality Reviewer

```
Você é um code-quality-reviewer IntelliX. Avalie o código implementado
contra os padrões IntelliX (TypeScript strict, zero any, Zod em inputs,
forbidden_paths respeitados, naming conventions, sem lógica no frontend).

CÓDIGO IMPLEMENTADO:
[colar diff ou conteúdo do arquivo]

Responda com:
✅ APROVADO
ou
❌ ISSUES — para cada problema, classifique:
  - Critical: viola segurança, expõe secret, any explícito, lógica no frontend
  - Important: naming errado, Zod ausente em input, import fora do escopo
  - Minor: comentário desnecessário, arquivo grande demais
Não invente issues que não existem no código.
```

---

#### Pós-execução (ao final de todos os arquivos da issue)

**Checklist de conclusão de issue:**
- [ ] Todos os arquivos da lista "Files" concluídos com ✅ nos dois reviews
- [ ] `tsc --noEmit` limpo (zero erros de tipo)
- [ ] Nenhum arquivo fora da lista "Files to NOT Touch" foi modificado
- [ ] Testes da issue passando (`npm test` ou `vitest run`)
- [ ] Issue marcada como concluída no TodoWrite

Se qualquer item falhar → corrija antes de passar para a próxima issue.

---

#### Quando o agente reportar um status especial

| Status | O que fazer |
|--------|-------------|
| `DONE` | Prosseguir para spec review |
| `DONE_WITH_CONCERNS` | Ler as preocupações antes de revisar. Se afetam correção → corrigir primeiro |
| `NEEDS_CONTEXT` | Fornecer o contexto faltante e re-despachar o agente |
| `BLOCKED` | Avaliar: contexto insuficiente → re-despachar com mais info / issue grande demais → `/break` novamente |

Nunca force retry sem mudança. Nunca pule spec review mesmo que pareça óbvio.

---

**Regra de ouro:** Um arquivo só está "feito" quando passou pelos 3 estágios.
Spec review antes de quality review — sempre nessa ordem.

---

## Checklist Fatal — Antes de Qualquer `/execute`

Se algum item estiver desmarcado, **não execute**. Volte e ajuste.

```
[ ] Spec completa com TODOS os comportamentos listados
[ ] Cada comportamento virou issue independente
[ ] Issue tem caminho feliz + edge cases + erros esperados
[ ] Issue tem seção "Files to NOT Touch" preenchida
[ ] /plan rodou e gerou PRD / plano completo
[ ] /clear executado depois do plano aprovado
[ ] Plano tático com paths absolutos pronto
[ ] references/architecture.md e references/DESIGN.md lidos
[ ] Agente correto identificado para cada tipo de arquivo
[ ] Context window abaixo de 50% antes de iniciar execução
```

**3 sintomas de que você está fazendo errado:**
- IA duplica componentes que já existem
- Consertar A quebra B
- Você está com medo de mexer no código

Se algum dos três aparecer, pare. O problema não é a IA — é a arquitetura.

> **Gerenciamento de context window:** ver [`references/context-window.md`](context-window.md)

---
