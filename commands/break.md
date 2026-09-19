---
description: Decompõe o SPEC aprovado em Task Contracts atômicos, ordenados e validáveis. Segundo comando do Epic Workflow.
disable-model-invocation: false
---

Use `framework/framework.yaml`, `framework/templates/TASK.yaml` e
`references/four-commands.md` como referências. O framework prevalece.

Pré-condição: `SPEC.md` aprovado e documentos apontados por `intellix.yaml`
existem. Se não, pare e solicite `/spec`.

1. Leia PRD, Architecture, ADRs e SPEC.
2. Decomponha por comportamento verificável, não por arquivo ou por agente.
3. Crie `tasks/TASK-NNN.yaml` a partir do template. Neste estágio use `DRAFT`,
   objetivo, fontes, risco preliminar, domínio e critérios de aceite. Não invente
   detalhes ausentes; registre-os em `handoff.open_questions`.
4. Ordene por dependências: contrato/dados, domínio, integrações, UI e release.
5. Uma task deve caber em uma sessão e, normalmente, em até 10 arquivos. Divida
   apenas quando houver resultado independente; nunca para simular paralelismo.
6. Leia `project.governance_profile` e os mínimos correspondentes em
   `framework/framework.yaml`. Gates preliminares nunca podem ficar abaixo da
   união entre perfil e risco; perfil `micro` não dispensa fileset explícito.
7. Detecte filesets provavelmente concorrentes e não proponha execução paralela.
8. Rode `python3 ${CLAUDE_PLUGIN_ROOT}/framework/validate.py --tasks-dir tasks`.
9. Apresente ordem, dependências, riscos e perguntas. Aguarde aprovação antes do
   planejamento detalhado.

`issues/*.md` é legado: não crie novas issues salvo solicitação explícita para
um projeto ainda não migrado.
