---
description: Executa um Task Contract aprovado com fileset, evidência, revisão independente e CI. Quarto comando do Epic Workflow. Uso: /execute TASK-NNN
argument-hint: [TASK-NNN]
disable-model-invocation: false
---

Task alvo: $ARGUMENTS

1. Rode o phase gate legado e valide o contrato:
   - `bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/phase-gate.sh execute`
   - `python3 ${CLAUDE_PLUGIN_ROOT}/framework/validate.py --task tasks/$ARGUMENTS.yaml`
   - `python3 ${CLAUDE_PLUGIN_ROOT}/framework/validate.py --tasks-dir tasks`
2. Prossiga somente se a task estiver `READY`, fontes estiverem legíveis e os
   gates humanos necessários estiverem registrados.
3. Confirme branch curta. Risco médio/alto/crítico exige worktree isolada. Registre
   baseline, arquivos permitidos e estado limpo/alterações preexistentes.
4. Leia o papel em `framework/roles`. Implemente o comportamento completo, não um
   arquivo por agente. Não altere nada fora de `scope.create`/`scope.modify`.
5. Se `ownership.executor` for `codex`, gere um handoff de execução contendo o
   contrato e solicite execução no Codex; Claude não deve assumir a implementação.
   Se o executor for Claude, execute, mas atribua revisão a outro responsável.
6. Rode todos os comandos de `verification`, os testes de regressão e os gates
   aplicáveis. Falha é bloqueante; não enfraqueça o teste.
7. Compare o diff ao fileset, registre arquivos/evidências/riscos no handoff e
   mova para `IN_REVIEW`.
8. O reviewer independente verifica spec, arquitetura, segurança e qualidade.
   Gaps voltam como `CHANGES_REQUESTED`. Limite: 3 ciclos; depois escale decisão.
9. CI é o árbitro final. Só marque `APPROVED` com CI verde e aprovações exigidas.
   Merge, deploy e ações irreversíveis continuam sujeitos às políticas e ao
   responsável humano.

Os agentes tipados existentes podem auxiliar um papel, mas não substituem o
Task Contract nem criam aprovação própria.
