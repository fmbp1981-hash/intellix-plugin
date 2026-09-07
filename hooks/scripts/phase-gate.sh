#!/usr/bin/env bash
# IntelliX Phase Gate — verificação técnica de pré-requisitos entre fases.
#
# Por que existe: até 2026-08 o pipeline IntelliX dependia só de convenção
# documental ("lembre de ler references/architecture.md antes do /plan").
# Convenção não é gate — o agente esquece, o humano esquece, e a fase seguinte
# roda com contexto incompleto. Este script transforma o pré-requisito em
# verificação binária: ou o artefato existe em disco, ou o comando para.
#
# Uso:  bash phase-gate.sh <fase>
#       fases: plan | execute | deploy | handoff
# Saída: 0 = liberado | 1 = bloqueado (motivos em stderr)

set -uo pipefail

FASE="${1:-}"
FALHAS=()

exigir_arquivo() {
  local caminho="$1" motivo="$2"
  [[ -f "$caminho" ]] || FALHAS+=("FALTA: $caminho — $motivo")
}

exigir_dir_nao_vazio() {
  local caminho="$1" motivo="$2"
  if [[ ! -d "$caminho" ]] || [[ -z "$(ls -A "$caminho" 2>/dev/null)" ]]; then
    FALHAS+=("FALTA: $caminho/ vazio ou inexistente — $motivo")
  fi
}

case "$FASE" in
  plan)
    exigir_arquivo ".intellix-phase" \
      "projeto nao inicializado — rode intellix:project-kickoff (Fase 00)"
    exigir_arquivo "references/architecture.md" \
      "Fase 01 (architecture) nao concluida — /plan sem isso ignora as regras do projeto"
    exigir_dir_nao_vazio "issues" \
      "nenhuma issue para planejar — rode /break antes"
    ;;
  execute)
    exigir_arquivo ".intellix-phase" \
      "projeto nao inicializado — rode intellix:project-kickoff (Fase 00)"
    exigir_arquivo "references/architecture.md" \
      "Fase 01 (architecture) nao concluida"
    exigir_dir_nao_vazio "issues" \
      "nenhuma issue planejada — rode /plan antes"
    ;;
  deploy)
    exigir_arquivo ".intellix-phase" "projeto nao inicializado"
    exigir_arquivo "references/security.md" \
      "Fase 06 (security-observability) nao concluida — deploy sem checklist de seguranca"
    exigir_dir_nao_vazio "tests" \
      "Fase 07 (test-e2e) nao concluida — sem testes nao ha deploy"
    ;;
  handoff)
    exigir_arquivo ".intellix-phase" "projeto nao inicializado"
    exigir_arquivo "README.md" "handoff exige README tecnico"
    ;;
  *)
    echo "phase-gate: fase desconhecida '${FASE}'. Use: plan|execute|deploy|handoff" >&2
    exit 2
    ;;
esac

if (( ${#FALHAS[@]} > 0 )); then
  {
    echo "═══ INTELLIX PHASE GATE: BLOQUEADO (fase '${FASE}') ═══"
    for f in "${FALHAS[@]}"; do echo "  ✗ $f"; done
    echo ""
    echo "Resolva os itens acima antes de prosseguir. Se algum for intencionalmente"
    echo "dispensavel neste projeto, diga isso explicitamente ao usuario e peca"
    echo "confirmacao — nao pule silenciosamente."
  } >&2
  exit 1
fi

echo "✓ phase-gate '${FASE}': pre-requisitos satisfeitos."
exit 0
