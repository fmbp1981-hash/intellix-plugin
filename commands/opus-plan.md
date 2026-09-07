---
description: Planejamento estratégico forçado em Opus — arquitetura de projeto/epic, decisões técnicas de alto risco ou requisitos ambíguos. Não substitui o /plan tático por issue.
argument-hint: [tema ou epic a planejar]
model: opus
disable-model-invocation: false
---

Escopo: $ARGUMENTS

Este comando existe para o nível de planejamento **acima** do `/plan` (que é tático, por issue). Use `/opus-plan` quando:
- for decidir arquitetura de um projeto novo ou de um epic inteiro (não uma issue isolada)
- a decisão envolver trade-offs técnicos caros de reverter (escolha de stack, modelagem de dados, estratégia de auth/pagamento)
- o requisito estiver ambíguo o bastante para precisar de exploração antes de virar spec

Execute agora:
1. Se ainda não há PRD/plano aprovado para este escopo, use `superpowers:writing-plans` como base metodológica.
2. Consulte `MASTER-ARCHITECTURE.md` (fonte única de verdade de arquitetura) e, se o projeto já existe, rode gap analysis equivalente ao `intellix:code-audit` antes de propor mudanças.
3. Para qualquer versão de lib, preço de API ou comportamento de serviço externo citado no plano, verifique com Perplexity (`modules/perplexity.md`) — nunca assuma.
4. Para qualquer API de biblioteca usada no plano, verifique com Context7 (`modules/context7.md`) antes de recomendar uma abordagem.
5. Produza o plano com trade-offs explícitos (não só a opção escolhida — também a rejeitada e por quê).
6. Apresente ao usuário e **aguarde aprovação explícita** antes de descer para `/spec` → `/break` → `/plan` → `/execute`.

> `model: opus` é fixo neste comando — é o ponto de maior alavancagem do fluxo inteiro (o handoff pós-`writing-plans` documentado em `modules/claude-md-rules.md` depende da qualidade dessa decisão). Depois que o plano estratégico está aprovado, todo o resto do Epic Workflow já roteia sozinho para modelos mais baratos: `/break` herda o padrão da sessão, os agentes de `/execute` já saem fixados em Sonnet/Haiku nos templates de `intellix-templates/agents-template/`.
