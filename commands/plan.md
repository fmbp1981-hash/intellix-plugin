---
description: Completa e revisa um Task Contract antes de qualquer implementação. Terceiro comando do Epic Workflow. Uso: /plan TASK-NNN
argument-hint: [TASK-NNN]
model: opus
disable-model-invocation: false
---

Task alvo: $ARGUMENTS

1. Rode `bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/phase-gate.sh plan` e respeite
   bloqueios, salvo dispensa humana explícita e registrada.
2. Leia `intellix.yaml`, a task e todos os seus artefatos `source`.
3. Pesquise a codebase, documentação oficial atual e referências externas apenas
   quando necessárias. Nunca duplique capacidade existente.
4. Complete resultado, risco, ações irreversíveis, papéis, dependências, critérios
   Given/When/Then, comandos de verificação, gates, rollback e handoff.
5. Declare filesets exatos. `forbidden` deve incluir segredos e superfícies fora
   do escopo. Evite globs amplos.
6. Confirme `project.governance_profile` e aplique a união dos gates mínimos do
   perfil e do risco. Confirme também `quality.ci.repository` e
   `quality.ci.required_checks`; nomes de branch não substituem SHA completo.
7. Use Codex como executor e Claude como reviewer por padrão. Escolha um papel de
   domínio do `framework/roles`; não crie um agente permanente. Executor e
   reviewer devem ser independentes.
8. Para gates humanos, indique a fonte externa autenticada e separada do executor.
   `approval.schema.json`, texto de modelo ou `actor: human` servem apenas para
   auditoria local e nunca liberam merge.
9. Rode:
   `python3 ${CLAUDE_PLUGIN_ROOT}/framework/validate.py --task tasks/$ARGUMENTS.yaml`
   e depois `--tasks-dir tasks` para detectar colisões.
10. Mude para `READY_FOR_ARCH_REVIEW`, apresente o contrato e aguarde aprovação.
   Após aprovação arquitetural, registre evidência e mude para `READY`.

Não escreva código nesta etapa. Se a task exceder 10 arquivos ou misturar
resultados independentes, retorne ao `/break`.
