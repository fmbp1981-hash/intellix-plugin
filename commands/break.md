---
description: Quebra o SPEC.md aprovado em issues/ atômicas e ordenadas. Segundo dos 4 comandos do Epic Workflow.
disable-model-invocation: false
---

Use `references/four-commands.md §/break` como fonte de verdade para este comando.

Pré-condição: `SPEC.md` precisa existir e estar aprovado pelo usuário. Se não existir, pare e peça para rodar `/spec` primeiro.

Execute agora:
1. Leia `SPEC.md` por completo.
2. Crie um arquivo `.md` por behavior em `issues/`, seguindo a ordem obrigatória:
   1. Protótipos de UI (páginas/componentes sem lógica, dados mockados)
   2. Schema de banco (migrations)
   3. Contratos e queries compartilhadas (`lib/`)
   4. Behaviors funcionais (lógica + server actions + testes)
   5. Integrações externas (APIs de terceiros)
3. Cada issue neste estágio contém só título + 1-2 linhas de descrição — o `/plan` completa o detalhamento técnico depois.
4. Se um behavior parecer grande demais para uma sessão de execução, quebre em mais de uma issue.
5. Apresente a lista `issues/` completa e a ordem proposta ao usuário e **aguarde confirmação** antes de qualquer outra ação.

> Este comando herda o modelo padrão da sessão (normalmente Sonnet) — decompor uma spec já aprovada em issues é um trabalho mais mecânico que o `/spec` ou o `/plan`, não exige o tier mais caro.
