#!/usr/bin/env bash
# validate-hooks.sh — valida a fiação dos hooks do plugin IntelliX.
#
# Checa duas coisas:
#   1. todo script citado em hooks/hooks.json existe no plugin;
#   2. todo `suggest "<id>"` do skill-router.sh (se existir) aponta para
#      skills/<id>/SKILL.md — o runtime usa o NOME DA PASTA como ID da skill,
#      não o `name:` do frontmatter.
#
# Fail-closed: qualquer erro interno (arquivo ausente, JSON inválido, nenhum ID
# extraído) sai com código diferente de zero. Nunca reporta sucesso sem ter
# validado algo.
#
# Portável: só bash + sed + python3 (sem `grep -P`, indisponível no macOS).
#
# Uso:  bash hooks/scripts/validate-hooks.sh [raiz-do-plugin]
# Saída: 0 = ok | 1 = referência quebrada | 2 = erro interno do validador

set -uo pipefail

PLUGIN_DIR="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
HOOKS_JSON="$PLUGIN_DIR/hooks/hooks.json"
ROUTER="$PLUGIN_DIR/hooks/scripts/skill-router.sh"
SKILLS_DIR="$PLUGIN_DIR/skills"

fatal() { echo "ERRO INTERNO: $*" >&2; exit 2; }

[[ -f "$HOOKS_JSON" ]] || fatal "hooks.json não encontrado em $HOOKS_JSON"
[[ -d "$SKILLS_DIR" ]] || fatal "diretório de skills não encontrado em $SKILLS_DIR"
command -v python3 >/dev/null 2>&1 || fatal "python3 não disponível"

ERRORS=0
CHECKED=0

# ── 1. Scripts citados no hooks.json ────────────────────────────────────────
SCRIPTS=$(python3 - "$HOOKS_JSON" <<'EOF'
import json, re, sys
try:
    data = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception as e:
    print(f"__JSON_ERROR__ {e}")
    sys.exit(0)
for groups in data.get("hooks", {}).values():
    for group in groups:
        for h in group.get("hooks", []):
            if h.get("type") == "command":
                for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+)", h.get("command", "")):
                    print(m.group(1))
EOF
) || fatal "falha ao ler hooks.json"

if [[ "$SCRIPTS" == __JSON_ERROR__* ]]; then
  fatal "hooks.json inválido: ${SCRIPTS#__JSON_ERROR__ }"
fi

while IFS= read -r rel; do
  [[ -z "$rel" ]] && continue
  CHECKED=$((CHECKED + 1))
  if [[ -f "$PLUGIN_DIR/$rel" ]]; then
    echo "OK     hook → $rel"
  else
    echo "QUEBRA hook → $rel (arquivo inexistente)"
    ERRORS=$((ERRORS + 1))
  fi
done <<< "$SCRIPTS"

# ── 2. IDs sugeridos pelo skill-router.sh ───────────────────────────────────
if [[ -f "$ROUTER" ]]; then
  REFERENCED=$(sed -nE 's/.*suggest "([^"]+)".*/\1/p' "$ROUTER" | sort -u)
  [[ -n "$REFERENCED" ]] || fatal "skill-router.sh existe mas nenhum suggest \"...\" foi extraído"
  while IFS= read -r id; do
    CHECKED=$((CHECKED + 1))
    if [[ -f "$SKILLS_DIR/$id/SKILL.md" ]]; then
      echo "OK     router → skills/$id/SKILL.md"
    else
      echo "QUEBRA router → '$id' (não existe skills/$id/SKILL.md)"
      ERRORS=$((ERRORS + 1))
    fi
  done <<< "$REFERENCED"
fi

(( CHECKED > 0 )) || fatal "nenhuma referência validada — validador não testou nada"

echo ""
if (( ERRORS == 0 )); then
  echo "Validação OK — ${CHECKED} referência(s) verificada(s)."
  exit 0
fi
echo "${ERRORS} referência(s) quebrada(s) em ${CHECKED} verificada(s)."
exit 1
