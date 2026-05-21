# Plugin Hook Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar `validate-hooks.sh` — script que detecta automaticamente quando um nome de skill referenciado no `skill-router.sh` não tem `SKILL.md` correspondente com aquele `name:` no frontmatter.

**Architecture:** O script extrai todos os valores de `suggest "..."` do `skill-router.sh`, depois percorre todos os `SKILL.md` em `skills/` procurando `name: <valor>` no frontmatter. Qualquer nome sem correspondência é reportado como erro. Exit code 0 = tudo ok, 1 = há referências quebradas.

**Tech Stack:** Bash puro — sem dependências externas. Compatível com Git Bash (Windows) e bash Unix.

---

## Context — Por que este script existe

O `skill-router.sh` referencia skills pelo nome do frontmatter (`name:` no SKILL.md), não pelo nome do diretório. Por exemplo, a skill no diretório `frontend-design/` tem `name: frontend-design-workflow` no seu SKILL.md — e o hook usa `suggest "frontend-design-workflow"`. Se alguém renomeia o diretório ou altera o `name:` no frontmatter sem atualizar o hook, o hook silenciosamente deixa de funcionar.

Este script detecta esse desvio.

---

## Task 1: Criar `validate-hooks.sh`

**Files:**
- Create: `hooks/scripts/validate-hooks.sh`

- [ ] **Step 1: Criar o script com lógica de extração**

Criar o arquivo `C:\Users\Dell\.claude\plugins\marketplaces\intellix-plugin\hooks\scripts\validate-hooks.sh` com o conteúdo exato abaixo:

```bash
#!/bin/bash
# validate-hooks.sh — Verifica se cada skill referenciada no skill-router.sh
# tem um SKILL.md correspondente com name: <skill> no frontmatter.
#
# Uso: bash hooks/scripts/validate-hooks.sh
# Exit 0 → tudo ok | Exit 1 → referências quebradas
#
# Execute a partir da raiz do plugin:
#   cd /c/Users/Dell/.claude/plugins/marketplaces/intellix-plugin
#   bash hooks/scripts/validate-hooks.sh

PLUGIN_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ROUTER="$PLUGIN_DIR/hooks/scripts/skill-router.sh"
SKILLS_DIR="$PLUGIN_DIR/skills"

# Extrair nomes das skills referenciadas no router (suggest "nome")
REFERENCED=$(grep -oP '(?<=suggest ")[^"]+' "$ROUTER" | sort -u)

ERRORS=0

for skill_name in $REFERENCED; do
  # Procurar SKILL.md com name: <skill_name> no frontmatter
  MATCH=$(grep -rl "^name: ${skill_name}$" "$SKILLS_DIR" --include="SKILL.md" 2>/dev/null)

  if [ -z "$MATCH" ]; then
    echo "❌ BROKEN: skill-router.sh referencia '${skill_name}' mas nenhum SKILL.md tem 'name: ${skill_name}'"
    ERRORS=$((ERRORS + 1))
  else
    echo "✅ OK: '${skill_name}' → $(basename "$(dirname "$MATCH")")/SKILL.md"
  fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ Todos os ${skill_name:+$(echo "$REFERENCED" | wc -l | tr -d ' ')} skills referenciados são válidos."
  exit 0
else
  echo "❌ ${ERRORS} referência(s) quebrada(s) encontrada(s)."
  exit 1
fi
```

- [ ] **Step 2: Tornar o script executável**

```bash
chmod +x /c/Users/Dell/.claude/plugins/marketplaces/intellix-plugin/hooks/scripts/validate-hooks.sh
```

- [ ] **Step 3: Rodar o script e verificar o output**

```bash
cd /c/Users/Dell/.claude/plugins/marketplaces/intellix-plugin
bash hooks/scripts/validate-hooks.sh
```

Expected output (todos os 12 skills devem aparecer como ✅ OK):
```
✅ OK: 'architecture' → architecture/SKILL.md
✅ OK: 'agent-creation' → agent-creation/SKILL.md
✅ OK: 'code-audit' → code-audit/SKILL.md
✅ OK: 'deploy' → deploy/SKILL.md
✅ OK: 'dev-standards' → dev-standards/SKILL.md
✅ OK: 'frontend-design-workflow' → frontend-design/SKILL.md
✅ OK: 'handoff' → project-handoff/SKILL.md
✅ OK: 'integration' → integration/SKILL.md
✅ OK: 'live-chat' → live-chat/SKILL.md
✅ OK: 'project-kickoff' → project-kickoff/SKILL.md
✅ OK: 'security-observability' → security-observability/SKILL.md
✅ OK: 'test-e2e' → test-e2e/SKILL.md

✅ Todos os 12 skills referenciados são válidos.
```

Se algum aparecer como ❌ BROKEN, significa que o hook está desatualizado — corrigir o `name:` no SKILL.md correspondente ou atualizar o `suggest "..."` no skill-router.sh.

- [ ] **Step 4: Documentar o script no PLUGIN-CONVENTIONS.md**

Abrir `C:\Users\Dell\.claude\plugins\marketplaces\intellix-plugin\PLUGIN-CONVENTIONS.md` e adicionar esta seção após "## Versionamento do plugin":

```markdown
---

## Validação de integridade

Após qualquer alteração em `name:` de um SKILL.md ou em `suggest "..."` do skill-router.sh, rodar:

```bash
cd /c/Users/Dell/.claude/plugins/marketplaces/intellix-plugin
bash hooks/scripts/validate-hooks.sh
```

Exit 0 = tudo ok. Exit 1 = referência quebrada — o hook vai sugerir uma skill que não existe.
```

---

## Self-Review

**Spec coverage:**
- ✅ Script extrai nomes de `suggest "..."` — coberto no Step 1
- ✅ Valida contra frontmatter `name:` (não nome de diretório) — coberto com `grep -rl "^name: ${skill_name}$"`
- ✅ Exit code 0/1 para uso em CI ou sanity check manual — coberto
- ✅ Documentado em PLUGIN-CONVENTIONS.md — coberto no Step 4

**Placeholder scan:** Nenhum placeholder. Todo o código está completo e o expected output está literalizado.

**Observação de edge case:** O script usa `grep -oP` (Perl regex) que requer que o bash tenha `grep` com suporte a `-P`. Git Bash no Windows inclui GNU grep com `-P`. Se rodar em macOS com BSD grep nativo, trocar `-oP '(?<=suggest ")[^"]+'` por `-oE 'suggest "[^"]+"' | grep -oE '"[^"]+"' | tr -d '"'`. Documentar isso não é necessário para o uso atual (Windows + Git Bash).
