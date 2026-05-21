# Gerenciamento de Context Window — Padrão IntelliX

> Consulte este arquivo quando a IA começar a se comportar de forma estranha,
> duplicar código, ou quando você estiver prestes a iniciar uma nova fase.
> Índice: [`MASTER-ARCHITECTURE.md §0c`](../MASTER-ARCHITECTURE.md)

---

## Regra de Ouro

Mantenha o context window **entre 40% e 50% de uso**. Acima de 70%, a qualidade despenca.

A IA não "fica cansada" — ela literalmente perde acesso ao contexto anterior quando a janela
enche. Symptoms não são falhas de inteligência, são falhas de arquitetura de contexto.

---

## Diagnóstico — Sintoma → Causa → Solução

| Sintoma | Diagnóstico | Solução |
|---------|-------------|---------|
| IA esquece arquivo que criou há 5 mensagens | Context >70% | `/clear` + retomar com plano aprovado |
| IA cria componente duplicado | Não buscou na codebase antes | Forçar fase `/plan` com Frente 1 (grep codebase) |
| IA "trava" ou demora muito para responder | Context cheio de logs de MCPs | `/clear` + reduzir verbose dos MCPs |
| IA modifica arquivo fora do escopo | Sem isolamento de pasta + "Files to NOT Touch" ausente | Aplicar compartimentação de behaviors |
| IA reinventa padrão que já existe no projeto | Contexto não carregou `references/` | Referenciar explicitamente `references/architecture.md` antes do `/execute` |
| IA contradiz decisão tomada 10 mensagens atrás | Context overflow apagou a decisão | Registrar decisões no `references/architecture.md` do projeto |

---

## Práticas Operacionais

### 1. `/clear` entre fases — obrigatório

Execute `/clear` (ou equivalente de limpeza de contexto) nos seguintes momentos:
- Após `/plan` aprovado, antes de `/execute`
- Após pesquisa de codebase ou docs, antes de escrever código
- Ao trocar de issue para outra issue

**Por quê:** A pesquisa da Frente 1/2/3 polui a janela com logs, arquivos lidos e outputs de MCP.
O plano aprovado substitui tudo isso com 1/10 dos tokens e carrega apenas o que importa.

### 2. PRD substitui pesquisa

Após gerar o PRD / plano da issue:
- O plano aprovado = resumo destilado da pesquisa
- Delete o histórico de navegação/pesquisa da sessão
- Carregue apenas: plano + `references/architecture.md` + `references/DESIGN.md`

### 3. Agentes em contextos separados

`model_writer` e `component_writer` **não compartilham contexto**.
Cada agente (subagente) recebe apenas o necessário para sua tarefa:
- O plano da issue específica
- Os arquivos do seu escopo
- As references relevantes (architecture.md, DESIGN.md)

Nunca passe o histórico completo da sessão para um subagente.

### 4. Não cole o codebase inteiro

Use `glob` e `grep` para puxar apenas o relevante. Regras:
- Precisa de um componente? `grep -r "ComponentName" src/` — não leia todo `src/`
- Precisa do schema? Leia `src/types/index.ts` — não leia toda a codebase
- Precisa de um padrão? Leia 1 arquivo de exemplo — não leia todos os similares

### 5. MCPs com cuidado

Cada chamada MCP custa tokens no contexto:
- Desabilite MCPs que não estão em uso na fase atual
- Evite chamadas MCP redundantes (cache mental: se já sabe a resposta, não chame novamente)
- Logs verbosos de MCP podem preencher 20-30% da janela — reduza o log level

---

## Mapa de Uso de Tokens por Fase

| Fase | O que consome contexto | O que pode ser limpado antes |
|------|----------------------|------------------------------|
| `/spec` | Requisitos + conversa | — |
| `/break` | SPEC.md + issues geradas | Conversa anterior ao spec |
| `/plan` | Frente 1/2/3 + MCP outputs | — (é fase de pesquisa, precisa de espaço) |
| `/execute` | Plano aprovado + arquivos sendo editados | TODO o histórico de pesquisa |
| Depuração | Logs de erro + arquivos afetados | Histórico de issues não relacionadas |

---

## Regra de Ouro — Resumo

```
Antes de /execute:
  1. /plan aprovado ✓
  2. /clear executado ✓
  3. Carregue: plano + references/ ✓
  4. Context window < 50% ✓
```

Seguindo estas 4 regras, a IA tem o máximo de "memória de trabalho" disponível
para a tarefa e o mínimo de ruído de contexto anterior.
