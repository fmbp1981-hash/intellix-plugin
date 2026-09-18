---
description: Executa um Task Contract aprovado com fileset, evidência, revisão independente e CI. Quarto comando do Epic Workflow. Uso: /execute TASK-NNN
argument-hint: [TASK-NNN]
disable-model-invocation: false
---

Task alvo: $ARGUMENTS

1. Rode o phase gate legado e acione o dispatcher com raiz explícita:
   - `bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/phase-gate.sh execute`
   - `python3 ${CLAUDE_PLUGIN_ROOT}/framework/dispatch.py --root . --task tasks/$ARGUMENTS.yaml --current-adapter claude`
2. O dispatcher valida projeto, contrato, dependências, filesets e gates; resolve
   somente adapter instalado e permitido; registra a decisão em `runtime.records_path`.
   Falhas movem estados aplicáveis para `BLOCKED` com motivo durável.
   Fallback para Claude exige reviewer com identidade distinguível de Claude;
   `claude-independent` é conservadoramente tratado como a mesma família.
3. O dispatcher cria worktree dedicado e reserva durável do fileset para risco
   médio/alto/crítico. Nunca force, limpe ou remova worktree suja. Estados parciais
   `reserving` exigem reconciliação manual antes de nova execução.
   Depois da reserva, todas as transições e correções usam `--root` apontando para
   o worktree reservado; a raiz original responde com o caminho correto e não
   altera sua cópia obsoleta do contrato.
4. Leia o papel em `framework/roles`. Implemente o comportamento completo, não um
   arquivo por agente. Não altere nada fora de `scope.create`/`scope.modify`.
5. Se `ownership.executor` for `codex`, gere um handoff de execução contendo o
   contrato e solicite execução no Codex; Claude não deve assumir a implementação.
   Se o executor for Claude, execute, mas atribua revisão a outro responsável.
   O handoff ao reviewer contém digest, commit, diff e evidências, sempre com
   acesso `read-only` e checkpoint estruturado para retomada.
6. Rode todos os comandos de `verification`, os testes de regressão e os gates
   aplicáveis. Falha é bloqueante; não enfraqueça o teste.
7. Compare o diff ao fileset, registre arquivos/evidências/riscos no handoff e
   solicite a transição permitida:
   - `python3 ${CLAUDE_PLUGIN_ROOT}/framework/dispatch.py --root . --task tasks/$ARGUMENTS.yaml --target-state IN_REVIEW --reason "verification and handoff complete"`
8. O reviewer independente verifica spec, arquitetura, segurança e qualidade.
   Gaps voltam como `CHANGES_REQUESTED`. Limite: 3 ciclos; depois escale decisão.
9. CI é o árbitro final. Após o workflow terminar, consulte os checks configurados
   para o SHA completo revisado e grave somente a cópia de auditoria:
   `python3 ${CLAUDE_PLUGIN_ROOT}/framework/ci.py --root . --revision <sha-40> --output .intellix/runtime/ci/$ARGUMENTS.json`.
   Check ausente, antigo, incompleto, indeterminado ou falho bloqueia. JSON local,
   texto de modelo e resultado de outro repositório/SHA não são prova de CI.
10. O dispatcher desta etapa não promove `APPROVED`, merge, release ou deploy;
   esses gates permanecem externos e autenticados. Mesmo com CI verde, ausência
   de aprovação humana externa e credencialmente separada mantém merge bloqueado.
   Invocações contra estados terminais falham sem alterar o contrato; recuperação
   de escrita interrompida e concorrência pertencem ao hardening posterior.
   Merge, deploy e ações irreversíveis continuam sujeitos às políticas e ao
   responsável humano.

Os agentes tipados existentes podem auxiliar um papel, mas não substituem o
Task Contract nem criam aprovação própria.
