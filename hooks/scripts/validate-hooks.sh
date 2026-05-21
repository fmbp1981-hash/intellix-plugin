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
TOTAL=$(echo "$REFERENCED" | wc -l | tr -d ' ')
if [ $ERRORS -eq 0 ]; then
  echo "✅ Todos os ${TOTAL} skills referenciados são válidos."
  exit 0
else
  echo "❌ ${ERRORS} referência(s) quebrada(s) encontrada(s)."
  exit 1
fi
