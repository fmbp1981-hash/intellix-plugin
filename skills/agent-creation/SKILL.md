---
name: agent-creation
description: >
  Use esta skill SEMPRE que o projeto precisar de agentes de IA, bots, chatbots,
  assistentes virtuais, automação de atendimento, WhatsApp bot, multi-agent, ou
  qualquer sistema de atendimento automatizado. Esta é a Fase 03 do fluxo IntelliX —
  executada após architecture (Fase 01) quando o sistema inclui agentes.
  Delega para a skill unificada intellix-agent-creation que suporta GPT Maker,
  n8n e IntelliX Blueprint nativo.
user-invocable: false
---

# Fase 03 — Agent Creation

Orquestrador de criação de agentes. Delega para a skill `intellix-agent-creation`
que é a **plataforma unificada** com suporte a 3 plataformas: GPT Maker, n8n e
IntelliX Blueprint.

> **PRÉ-REQUISITO:** Fase 01 (architecture) concluída — schema DB e rotas definidos.

---

## Quando executar esta fase

```
Sistema tem agentes, bots ou automação de atendimento? → SEMPRE executar
Sistema é UI-only sem IA? → PULAR (ir para Fase 04)
```

---

## Execução

**Invoke imediatamente:**

```
Skill("intellix-agent-creation")
```

A skill `intellix-agent-creation` irá:
1. Perguntar qual plataforma: **GPT Maker** | **n8n** | **IntelliX Blueprint**
2. Executar o módulo correto para a plataforma escolhida
3. Gerar blueprint completo v2 com 15+ seções estruturadas
4. Produzir arquivos de configuração prontos para implementação

---

## Roteamento de Plataforma (resumo)

| Plataforma | Quando usar | O que gera |
|---|---|---|
| **GPT Maker** | Atendimento WhatsApp/Instagram com interface visual | Configuração via MCP diretamente no GPT Maker |
| **n8n** | Automações complexas com múltiplas integrações | Workflow n8n completo com nodes configurados |
| **IntelliX Blueprint** | Documentar e implementar em qualquer plataforma | Blueprint v2 JSON + 20 seções estruturadas |

---

## Integração com o Sistema Principal

Após gerar o blueprint/configuração do agente, integre ao sistema Next.js via:

```
src/agents/
  [nome-do-agente]/
    index.ts         ← ponto de entrada
    prompt.ts        ← system prompt e templates
    tools.ts         ← tool calls disponíveis para o agente
```

Para webhooks de entrada (Evolution API, GPT Maker, n8n):
```
src/app/api/
  webhooks/
    evolution/route.ts    ← mensagens WhatsApp
    gptmaker/route.ts     ← eventos do GPT Maker
    n8n/route.ts          ← triggers do n8n
```

---

## Handover para Fase 04

Ao concluir, informe:
> "Fase 03 concluída. Agente configurado. Próxima fase: **intellix:dev-standards** para padrões de implementação do código."

Atualize `.intellix-phase` para `dev`.

---

## Skills Relacionadas

| Quando usar | Skill |
|---|---|
| Criar/configurar agente GPT Maker via MCP | `intellix-agent-creation` (módulo GPT Maker) |
| Criar workflow de agente no n8n | `intellix-agent-creation` (módulo n8n) |
| Gerar blueprint documentado | `intellix-agent-creation` (módulo Blueprint) |
| Chat omnichannel com handoff humano | `intellix:live-chat` |
| Patterns de workflow n8n | `n8n-workflow-patterns` |
