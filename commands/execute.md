---
description: Executa uma issue com plano aprovado, arquivo por arquivo, com ciclo de 3 estágios (agente tipado → spec review → quality review). Quarto dos 4 comandos do Epic Workflow. Uso: /execute [issue]
argument-hint: [issue]
disable-model-invocation: false
---

Use `references/four-commands.md §/execute` e `MASTER-ARCHITECTURE.md §4` como fonte de verdade para este comando.

Issue alvo: $ARGUMENTS

Pré-condição — não prossiga se algum item falhar.

**Verificação automática (bloqueante), rode primeiro:**
`bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/phase-gate.sh execute`
Se sair com código 1, PARE e mostre os itens faltantes. Só prossiga se o usuário
dispensar explicitamente um pré-requisito.

**Verificação de julgamento (o script não consegue checar estas):**
```
[ ] issue tem plano aprovado com as 7 seções preenchidas
[ ] references/architecture.md e DESIGN.md (raiz, se houver UI) lidos
[ ] context window abaixo de 50%
```

Pré-execução (uma vez por issue):
1. Extraia todos os arquivos de "Files to Create" e "Files to Modify".
2. Para cada arquivo, identifique o agente correto pela tabela de `MASTER-ARCHITECTURE.md §4`.
3. Registre uma task no TodoWrite por arquivo.

Ciclo por arquivo (3 estágios obrigatórios, nunca pule etapas; Estágio 4 condicional em `references/four-commands.md`):
1. **Implementação** — despache o agente tipado correto (`intellix:component-writer`, `intellix:action-writer`, `intellix:model-writer` ou `intellix:test-writer`) com a spec da issue + as listas "Files". Ele implementa, testa e faz self-review.
2. **Spec review** — `intellix:spec-reviewer` valida Happy Path + Edge Cases + Error Cases contra o diff. ❌ GAPS → agente corrige → repete.
3. **Quality review** — `intellix:code-quality-reviewer` valida TypeScript strict, zero `any`, Zod, naming e limites de paths. Critical/Important bloqueiam → agente corrige → repete. Minor → nota, não bloqueia.

Pós-execução (checklist de conclusão da issue):
```
[ ] Todos os arquivos com ✅ nos dois reviews
[ ] tsc --noEmit limpo
[ ] Nenhum arquivo fora de "Files to NOT Touch" foi modificado
[ ] Testes da issue passando
[ ] Issue marcada como concluída no TodoWrite
```

> Este comando herda o modelo padrão da sessão para a orquestração (dispatch + leitura de reviews). Os agentes do plugin fixam o próprio modelo no frontmatter de `agents/*.md` — Sonnet para escrita de código sensível (component, action, model) e para os revisores, Haiku para testes. Isso é o roteamento planejamento-caro / execução-barata: `/spec` e `/plan` em Opus, execução em Sonnet/Haiku.
