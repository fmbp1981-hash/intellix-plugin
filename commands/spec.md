---
description: Cria ou atualiza SPEC.md — especificação formal de uma feature/módulo (o QUÊ, nunca o COMO). Primeiro dos 4 comandos do Epic Workflow.
model: opus
disable-model-invocation: false
---

Use `references/four-commands.md §/spec` como fonte de verdade para este comando.

Execute agora:
1. Se `SPEC.md` já existe na raiz, leia-o antes de propor mudanças — nunca sobrescreva sem mostrar o diff ao usuário.
2. Para cada rota/módulo novo, produza uma seção com:
   - `## [/rota-da-pagina]` — propósito da rota
   - `### Components` — nomes em `PascalCase`, uma responsabilidade única cada
   - `### Behaviors` — nomes em `kebab-case`, atômicos o bastante para virar uma issue isolada em `/break`
3. Descreva o QUÊ, nunca o COMO implementar — zero menção a bibliotecas, hooks ou queries aqui.
4. Apresente o `SPEC.md` completo ao usuário e **aguarde aprovação explícita** antes de qualquer outra ação.

Não prossiga para `/break` nesta mesma resposta — pare no gate de aprovação.

> Este comando roda em Opus por padrão (`model: opus`) porque a qualidade da especificação define o teto de qualidade de tudo que vem depois. Rotear para Sonnet/Haiku aqui é falsa economia.
