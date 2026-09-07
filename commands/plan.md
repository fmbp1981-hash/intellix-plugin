---
description: Pesquisa em 3 frentes e preenche as 7 seções técnicas de uma issue antes de qualquer código ser escrito. Terceiro dos 4 comandos do Epic Workflow. Uso: /plan [issue]
argument-hint: [issue]
model: opus
disable-model-invocation: false
---

Use `references/four-commands.md §/plan` como fonte de verdade para este comando.

Issue alvo: $ARGUMENTS

Execute agora, nesta ordem obrigatória:

0. **Phase gate (bloqueante):** rode
   `bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/phase-gate.sh plan`
   Se sair com código 1, PARE e apresente os itens faltantes ao usuário — não
   planeje sem os artefatos das fases anteriores. Só prossiga se o usuário
   explicitamente dispensar um pré-requisito.
1. Leia a issue especificada em `issues/`.
2. **Pesquisa em 3 frentes (nunca pule):**
   - Frente 1 — Codebase interna: glob/grep por componentes, hooks, actions e utilities já existentes. Nunca duplicar o que já existe.
   - Frente 2 — Documentação oficial (Context7 / Perplexity conforme `modules/context7.md` e `modules/perplexity.md`): confirmar API/versão atual antes de planejar.
   - Frente 3 — Repos de referência: se a issue envolve padrão complexo (auth, pagamentos, realtime), considerar clonar repo aberto similar para `.temp/`, absorver o padrão, deletar `.temp/` depois.
3. Consulte `MASTER-ARCHITECTURE.md` e `references/DESIGN.md`.
4. Preencha as 7 seções obrigatórias na issue (Functional Specification, Database Schema, Files to Create/Modify/NOT Touch, External Dependencies, Notes, Tasks) — template completo em `references/four-commands.md`.
5. Se o plano ultrapassar 10 arquivos, sinalize ao usuário que a issue precisa ser quebrada novamente via `/break`.
6. Apresente o plano completo e **aguarde aprovação explícita**. Não escreva código nesta etapa.
7. Após aprovação, lembre o usuário: rode `/clear` antes de `/execute` — a pesquisa poluiu a janela de contexto, o plano aprovado já contém o que importa.

> Este comando roda em Opus por padrão (`model: opus`) — é aqui que decisões de arquitetura, edge cases e escopo de arquivos são travados. Um erro de julgamento aqui custa retrabalho em todo o `/execute`. Para planejamento estratégico de nível mais alto (arquitetura de projeto/epic, não uma issue tática), use `/opus-plan`.
