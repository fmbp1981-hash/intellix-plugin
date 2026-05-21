---
description: >
  Inicia um novo projeto IntelliX com setup zero-touch: coleta inputs, gera references/
  customizadas, compila agentes especializados, instala dependências e entrega estrutura
  SDD pronta para /spec — tudo em ~2 minutos sem nenhum setup manual.
disable-model-invocation: false
---

Use a skill `intellix:projeto-novo` agora para inicializar o projeto.

O comando `/projeto novo` faz o seguinte automaticamente:
1. Coleta até 5 inputs (nome, descrição, cliente, cor, infra opcional)
2. Gera `references/` com 5 arquivos customizados (architecture, design_system, workflow, stack, security)
3. Compila 4 agentes especializados em `agentes/` (model_writer, action_writer, component_writer, test_writer)
4. Cria estrutura SDD completa com pastas canônicas
5. Gera `.env.local` com secrets e `.env.example` commitável
6. Executa `npm install` com stack IntelliX fixada

Ao finalizar, o projeto estará pronto para `/spec`.
