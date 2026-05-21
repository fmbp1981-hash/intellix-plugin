# Painel do Atendente — Especificação

Interface completa para agentes humanos gerenciarem atendimentos.

## Tabela de conteúdos

1. [Layout geral](#layout-geral)
2. [Sidebar esquerda: Lista de conversas](#sidebar-esquerda)
3. [Área central: Chat](#área-central)
4. [Sidebar direita: Perfil do lead](#sidebar-direita)
5. [Timer de inatividade](#timer-de-inatividade)
6. [Notificações e alertas](#notificações-e-alertas)
7. [Respostas rápidas](#respostas-rápidas)
8. [Notas internas](#notas-internas)
9. [Ações do agente](#ações-do-agente)
10. [Dashboard do admin](#dashboard-do-admin)

---

## Layout geral

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: Logo + Nome do agente + Status (online/offline)     │
├────────────┬──────────────────────────┬─────────────────────┤
│  SIDEBAR   │      CHAT AREA           │   LEAD PROFILE      │
│  ESQUERDA  │                          │                     │
│            │  [Header da conversa]    │  Nome, email, tel   │
│  Filtros:  │                          │  Origem, tags       │
│  - Minhas  │  [Mensagens]             │                     │
│  - Espera  │                          │  [Histórico]        │
│  - Todas   │                          │  Conversas anteriores│
│  - Fechadas│                          │                     │
│            │  [Timer inatividade]     │  [Notas internas]   │
│  [Lista de │                          │                     │
│  conversas]│  [Input + ações]         │  [Dados coletados]  │
│            │                          │                     │
├────────────┴──────────────────────────┴─────────────────────┤
│ FOOTER: Respostas rápidas / Atalhos                         │
└─────────────────────────────────────────────────────────────┘
```

**Proporções:** Sidebar esquerda 280px | Chat flexível | Sidebar direita 320px
**Mobile:** Apenas uma view por vez (lista OU chat OU perfil)

## Sidebar esquerda

### Filtros (tabs superiores)
- **Minhas** — Conversas onde `current_agent_id = meu_id` e `status = human_active`
- **Aguardando** — Conversas com `status = waiting_human` (badge com contagem)
- **Todas** — Todas as conversas ativas (qualquer status exceto closed)
- **Fechadas** — Últimas 50 conversas com `status = closed`

### Filtro por canal (dropdown ou pills abaixo das tabs)
- **Todos** (padrão) — Mostra todas as conversas independente do canal
- 🌐 **Webchat** — Apenas conversas do widget do site
- 📱 **WhatsApp** — Apenas conversas de WhatsApp (qualquer provider)
- 📸 **Instagram** — Apenas conversas de Instagram DM
- ✈️ **Telegram** — Apenas conversas de Telegram
- Filtros combinam: pode estar em "Minhas" + "WhatsApp" simultaneamente

### Card de conversa
```
┌──────────────────────────────────┐
│ 📱 🔴 Maria Silva        14:32  │  ← Ícone canal + Badge status + Hora
│ "Quero saber sobre desconto..." │  ← Última mensagem (truncada)
│ 🤖 IA ativa │ 5 min             │  ← Status │ Tempo esperando
└──────────────────────────────────┘
```

**Ícones de canal:**
- 🌐 Webchat (chat do site)
- 📱 WhatsApp (qualquer provider)
- 📸 Instagram DM
- ✈️ Telegram
- 🔌 Canal customizado

**Indicadores visuais:**
- 🔴 Vermelho pulsante: `waiting_human` (aguardando ser assumida)
- 🟢 Verde: `human_active` com agente interagindo
- 🟡 Amarelo: `human_active` com timer > 80% (inatividade)
- ⚪ Cinza: `ai_active` (IA atendendo)
- Negrito: mensagens não lidas

**Ordenação:** Conversas `waiting_human` sempre no topo, depois por `last_message_at` DESC.

**Busca:** Campo de busca para filtrar por nome do lead, email, conteúdo de mensagens.

## Área central

### Header da conversa
```
┌───────────────────────────────────────────────────┐
│ 📱 Maria Silva │ maria@email.com │ +5511999...    │
│ Canal: WhatsApp (Cloud API) │ Criada há 25 min    │
│ Status: 🤖 IA ativa                               │
│ [Assumir Atendimento] [Devolver p/ IA] [Encerrar] │
└───────────────────────────────────────────────────┘
```

**Indicador de limitações do canal:** Quando o agente está atendendo um canal com limitações,
mostrar um tooltip ou banner sutil informando:
- Instagram DM: "Este canal não suporta botões ou formatação rica"
- Telegram: "Este canal suporta Markdown"
- WhatsApp: "Use *asteriscos* para negrito"

### Área de mensagens
Mesma lógica do widget, porém:
- Mensagens do lead à esquerda
- Mensagens da IA em bolha com ícone de bot (cor neutra)
- Mensagens do humano à direita (cor do agente)
- Notas internas com fundo amarelo claro e ícone de cadeado 🔒
- Mensagens de sistema centralizadas
- **Preview do contexto IA:** Ao assumir, exibir card especial no topo:

```
┌──────────────────────────────────────────┐
│ 📋 Resumo do atendimento IA             │
│                                          │
│ O lead Maria perguntou sobre planos      │
│ empresariais e manifestou interesse no   │
│ plano Pro. Solicitou desconto especial.  │
│ Dados coletados: empresa TechCorp,       │
│ orçamento ~R$500/mês.                    │
│                                          │
│ [Ver todas as mensagens anteriores ↓]    │
└──────────────────────────────────────────┘
```

### Input do agente
- Textarea igual ao widget
- Atalho `/` para abrir respostas rápidas
- Atalho `@` para mencionar outro agente (nota interna)
- Toggle "Nota interna" (ícone de cadeado) para enviar como nota interna
- Botão de upload de arquivos
- Indicador "Você está digitando..." enviado via Presence

## Sidebar direita

### Perfil do lead
```
┌────────────────────────────┐
│ 👤 Maria Silva             │
│ maria@techcorp.com         │
│ +55 11 99999-9999          │
│                            │
│ Origem: Website (/pricing) │
│ Primeira visita: 12/03     │
│ Conversas: 3               │
│                            │
│ Tags: [VIP] [Empresa]      │
│ Prioridade: ⭐ Alta         │
└────────────────────────────┘
```

### Dados coletados pela IA
```
┌────────────────────────────┐
│ 📊 Dados coletados         │
│                            │
│ Empresa: TechCorp          │
│ Interesse: Plano Pro       │
│ Orçamento: R$500/mês       │
│ Cargo: Gerente de TI       │
│ Tamanho: 50 funcionários   │
└────────────────────────────┘
```

### Histórico de atendimentos
Lista de todas as conversas anteriores deste lead com resumo de cada.

### Notas internas
Timeline de notas dos agentes sobre este lead (persistente entre conversas).

## Timer de inatividade

Componente visual que aparece quando o agente está em `human_active`.

```
┌──────────────────────────────────────┐
│ ⏱️ Inatividade: 7:23 / 10:00        │
│ ████████████░░░░░░ 73%               │
│                                      │
│ ⚠️ Em 2:37 o atendimento será       │
│    devolvido à IA automaticamente     │
└──────────────────────────────────────┘
```

**Comportamento visual:**
- 0-79%: Barra verde, texto normal
- 80-89%: Barra amarela PULSANTE, texto amarelo, som de alerta suave
- 90-99%: Barra vermelha PULSANTE, texto vermelho, som de alerta urgente
- 100%: Handoff executado, mensagem "Atendimento devolvido à IA"

**Posição:** Fixo acima do input do agente na área central.

Cada mensagem enviada pelo agente reseta o timer para 0.

## Notificações e alertas

### Tipos de notificação no painel

| Evento | Visual | Som |
|--------|--------|-----|
| Nova conversa `waiting_human` | Badge vermelho pulsante na sidebar | Notificação sonora |
| Mensagem do lead em conversa do agente | Badge no card da conversa | Som curto |
| Timer 80% | Barra amarela + toast warning | Alerta suave |
| Timer 90% | Barra vermelha + toast urgente | Alerta urgente |
| Timer 100% (handoff auto) | Toast "Conversa devolvida à IA" | Som de transição |
| Menção @agente em nota interna | Notificação no header | Som de menção |

### Notificação do browser
Solicitar permissão de notificação do browser para alertar mesmo com aba em background.

```typescript
// Solicitar permissão ao primeiro login
if (Notification.permission === 'default') {
  Notification.requestPermission();
}

// Enviar notificação quando nova conversa waiting_human
if (Notification.permission === 'granted') {
  new Notification('Novo atendimento aguardando', {
    body: `${lead.name} precisa de atendimento humano`,
    icon: '/notification-icon.png'
  });
}
```

## Respostas rápidas

### Ativação
- Digitar `/` no input abre modal de busca
- Digitar `/horario` filtra e seleciona a resposta
- Enter para inserir o texto no input

### Interface
```
┌──────────────────────────────────┐
│ 🔍 Buscar resposta rápida...    │
│                                  │
│ /obrigado — Agradecimento final  │
│ /horario  — Horário de funciona. │
│ /preco    — Tabela de preços     │
│ /desconto — Política de desconto │
│ /contrato — Envio de contrato    │
│                                  │
│ [+ Criar nova resposta rápida]   │
└──────────────────────────────────┘
```

### Variáveis suportadas
Respostas podem usar variáveis dinâmicas:
- `{lead_name}` → Nome do lead
- `{agent_name}` → Nome do agente
- `{company}` → Nome da empresa (se coletado)

## Notas internas

### Criação
- Toggle "Nota interna" no input (ícone 🔒)
- Ou prefixar com `@` para menção + nota
- Notas NÃO são visíveis ao lead

### Visualização
- Fundo amarelo claro com bordas tracejadas
- Ícone de cadeado 🔒
- Prefixo: "[Nota interna]"
- @menções destacadas em azul

### Persistência
- Notas são salvas como mensagens com `is_internal_note = true`
- Filtradas pelo RLS: lead nunca vê
- Visíveis por todos os agentes da equipe

## Ações do agente

### Assumir atendimento
- Botão verde "Assumir Atendimento"
- Visível apenas em conversas `waiting_human`
- Ao clicar: executa Fluxo 2 (ver handoff-flow-spec)

### Devolver para IA
- Botão amarelo "Devolver para IA"
- Visível apenas em conversas `human_active` onde sou o agente
- Ao clicar: modal de confirmação + campo opcional "Motivo"
- Executa Fluxo 3 (ver handoff-flow-spec)

### Encerrar conversa
- Botão vermelho "Encerrar"
- Visível em `human_active` ou `ai_active`
- Ao clicar: modal de confirmação
- Executa Fluxo 6 (ver handoff-flow-spec)

### Transferir para outro agente
- Botão "Transferir" com dropdown de agentes online
- Mensagem de sistema: "Atendimento transferido de [Agente A] para [Agente B]"
- O novo agente recebe notificação

### Alterar prioridade
- Dropdown no header: Normal / Alta / Urgente
- Urgente: aparece no topo da lista com badge vermelho

### Adicionar tags
- Campo de tags no perfil do lead
- Autocomplete com tags existentes + criar nova
- Tags usadas para filtrar na sidebar

## Dashboard do admin

Acessível apenas para agentes com `role = 'admin'` ou `'supervisor'`.

### Métricas em tempo real
- Conversas ativas por status (gráfico de pizza)
- **Conversas ativas por canal** (gráfico de barras: WhatsApp, IG, Telegram, Webchat)
- Tempo médio de espera em `waiting_human`
- Tempo médio de atendimento humano
- Taxa de resolução por IA vs humano
- Agentes online e carga de cada um
- **Health check dos canais** (verde/vermelho por canal configurado)

### Gerenciamento de canais (NOVO)
- **CRUD de canais**: Adicionar/editar/desativar canais
- **Configurar credenciais** por canal (formulário dinâmico por provider)
- **Testar canal**: Botão "Testar conexão" que chama `adapter.healthCheck()`
- **Webhook URL**: Exibir a URL de webhook para cada canal (copiar com 1 clique)
- **Status**: Indicador verde/amarelo/vermelho por canal
- **Provider de WhatsApp**: Dropdown para escolher entre Cloud API, Evolution, Z-API, Custom
- **Canais disponíveis para adicionar**: Lista de adapters registrados no ChannelRegistry

### Configurações
- Timeout de inatividade (slider 5-30 min)
- Mensagens de sistema customizáveis
- Respostas rápidas globais
- Gerenciar agentes e permissões
- **Configurar canal de notificação por agente**
- Knowledge base para IA (CRUD de artigos)
- Configurar palavras-chave de handoff

### Relatórios
- Conversas por período
- CSAT/NPS (se pesquisa de satisfação habilitada)
- Motivos de handoff (gráfico de barras)
- Tempo de resposta por agente
- Conversas por origem (UTM, página)
- **Conversas por canal** (WhatsApp vs Instagram vs Telegram vs Webchat)
- **Taxa de resolução por canal** (% resolvido por IA vs humano por canal)
- **Tempo médio de resposta por canal**
