---
description: Executa o checklist completo de deploy IntelliX (Vercel + DNS + health check). Só executar após os testes passarem.
disable-model-invocation: true
---

**Phase gate (bloqueante), rode primeiro:**
`bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/phase-gate.sh deploy`
Se sair com código 1, PARE e mostre os itens faltantes ao usuário.

Depois, use a skill `intellix:deploy` para executar o checklist completo de deploy.

IMPORTANTE: Este comando só deve ser executado manualmente por você.
Confirme antes de prosseguir que a Fase 07 (test-e2e) foi concluída com sucesso.
