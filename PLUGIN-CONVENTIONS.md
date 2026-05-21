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

O plugin usa semver informal: `major.minor.patch`.

- `patch` — correções de texto, clarificações de regras existentes
- `minor` — novos princípios, novas skills, reorganização de estrutura (como esta refatoração)
- `major` — mudanças que quebram nomes de skills existentes

Atualizar `version` em `.claude-plugin/plugin.json` a cada mudança.

---

## Validação de integridade

Após qualquer alteração em `name:` de um SKILL.md ou em `suggest "..."` do skill-router.sh, rodar:

```bash
cd /c/Users/Dell/.claude/plugins/marketplaces/intellix-plugin
bash hooks/scripts/validate-hooks.sh
```

Exit 0 = tudo ok. Exit 1 = referência quebrada — o hook vai sugerir uma skill que não existe.
