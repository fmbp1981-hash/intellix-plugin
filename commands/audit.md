---
description: Auditoria de entrada de um sistema existente contra os padrões IntelliX (Fase 00b). Gera gap analysis em 12 dimensões, score e roadmap priorizado (Sprint 0 a 4).
disable-model-invocation: false
---

Use a skill `intellix:code-audit` agora para auditar este sistema existente.

Fluxo (detalhe na skill):
1. Mapeamento do codebase (estrutura, dependências, tamanho).
2. Gap analysis nas **12 dimensões** IntelliX (TypeScript, camadas, banco, frontend, API,
   state, segurança, testes, observabilidade, DevOps, multi-tenancy, LGPD).
3. Relatório com score por dimensão em `docs/intellix-audit-[data].md`.
4. Retrofit DevSecOps do que faltar (Sprint 0) e roadmap de refatoração (Sprints 1 a 4).
5. Guia de execução sprint a sprint com as skills IntelliX.

Fronteiras (normativas em `~/.claude/metodologia.yaml → auditorias`):
- este comando = **auditoria de entrada** ("posso seguir desenvolvendo em cima disto?");
- `intellix:system-scan` = **auditoria de saída** (veredito Classe A/B/C antes de handoff/demo);
- `devsecops:security-gate` = **gate de segurança** antes de deploy; `/devsecops:pentest` = teste ofensivo autorizado.

Seja rigoroso: nível de um Senior Developer com 15+ anos auditando um sistema de produção.
