---
description: Audita um sistema existente contra os padrões IntelliX de arquitetura clean. Gera gap analysis, score por dimensão e roadmap priorizado de refatoração.
disable-model-invocation: false
---

Use a skill `intellix:code-audit` agora para auditar este sistema existente.

Execute o workflow completo de 5 fases:
1. Mapeamento do codebase (estrutura, dependências, tamanho)
2. Gap analysis nas 10 dimensões IntelliX (TypeScript, arquitetura, banco, frontend, API, state, segurança, testes, observabilidade, DevOps)
3. Relatório com score por dimensão salvo em `docs/intellix-audit-[data].md`
4. Roadmap de refatoração em 4 sprints priorizados
5. Guia de execução sprint a sprint usando as skills IntelliX

Seja rigoroso: este audit deve ter o nível de qualidade de um Senior Developer com 15+ anos auditando um sistema de produção.
