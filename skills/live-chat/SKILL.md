---
name: live-chat
description: >
  Cria um sistema completo de chat de atendimento omnichannel ao vivo com agente de IA e handoff
  para humano. Suporta Webchat, WhatsApp (API oficial, Evolution API, Z-API, ou qualquer provider),
  Instagram DM, Telegram, e extensível para qualquer canal. Use esta skill SEMPRE que o usuário
  mencionar: chat de atendimento, live chat, inbox de suporte, sistema de conversas, atendimento
  ao cliente, handoff humano, transferência para atendente, painel de atendimento, helpdesk,
  suporte ao vivo, chat widget, webchat de suporte, atendimento com IA e humano, caixa de entrada
  omnichannel, CRM de atendimento, inbox unificado, atendimento multicanal, atendimento via
  Instagram, atendimento via Telegram, atendimento via WhatsApp, ou qualquer variação desses termos.
  Também ative quando o usuário quiser criar um painel onde agentes humanos e IA trabalham juntos
  em conversas com clientes de múltiplos canais, mesmo que não use o termo "chat" explicitamente.
compatibility:
  tools: [bash, python]
  dependencies: [next, react, typescript, tailwindcss, supabase-js, framer-motion, lucide-react, zod]
  external_services: [supabase, openai]
---

# Live Chat Support — Sistema Omnichannel de Atendimento com IA + Handoff Humano

Gera um sistema completo de atendimento omnichannel dentro de qualquer projeto Next.js + Supabase.
Inbox unificado que recebe conversas de Webchat, WhatsApp, Instagram DM, Telegram e qualquer canal
adicional. Combina agente de IA para atendimento automático com handoff inteligente para humanos,
notificação configurável via canal preferido, retorno automático por inatividade, e histórico
completo de contexto entre transições — tudo em uma interface unificada para o atendente.

## Quando usar

**USE quando o usuário quiser:**
- Um sistema de chat omnichannel para atender leads/clientes
- Painel de atendimento unificado com IA e humano trabalhando juntos
- Inbox de suporte com múltiplos canais (WhatsApp, IG, Telegram, Webchat)
- Widget de chat para integrar em sites
- Sistema de handoff IA → Humano → IA com contexto preservado
- Integrar atendimento de WhatsApp com qualquer provider

**NÃO USE quando:**
- O usuário quer apenas um chatbot sem painel de atendimento humano
- É apenas um FAQ estático sem conversa em tempo real

## Credenciais e configuração

Esta skill requer acesso a **Supabase** e **OpenAI/Anthropic** como base.
Os canais de mensageria são **opcionais e modulares** — configure apenas os que usar.

```bash
cp .env.example .env
# Preencha .env com suas credenciais reais
```

**Onde encontrar credenciais base:**
- **Supabase**: Dashboard → Settings → API → URL e Keys
- **OpenAI**: platform.openai.com → API Keys
- **Anthropic**: console.anthropic.com → API Keys

**Canais de mensageria (configure apenas os que usar):**
- **WhatsApp Cloud API (oficial)**: Meta Business Suite → WhatsApp → API Setup
- **Evolution API**: Painel da instância → Settings → API Key
- **Z-API**: Painel Z-API → Instâncias → Token
- **Instagram**: Meta Business Suite → Instagram → Messenger API
- **Telegram**: @BotFather no Telegram → /newbot → Token

## Setup

```bash
npm install @supabase/supabase-js @supabase/ssr framer-motion lucide-react zod react-hook-form date-fns
npm install -D tailwindcss @tailwindcss/typography
```

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     CANAIS DE ENTRADA                       │
│  ┌────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ │
│  │Webchat │ │WhatsApp  │ │Instagram │ │Telegram│ │ ...  │ │
│  │Widget  │ │(qualquer)│ │   DM     │ │  Bot   │ │      │ │
│  └───┬────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ └──┬───┘ │
│      └───────────┴────────┬───┴────────────┴─────────┘     │
│                           │                                │
│              ┌────────────▼─────────────┐                  │
│              │   CHANNEL ADAPTER LAYER  │                  │
│              │  (Normaliza msg de/para  │                  │
│              │   qualquer canal)        │                  │
│              └────────────┬─────────────┘                  │
│                           │                                │
├───────────────────────────┼────────────────────────────────┤
│                  INBOX UNIFICADO                           │
│  ┌────────────────────────▼────────────────────────────┐   │
│  │  conversations │ messages │ channels │ presence     │   │
│  │                SUPABASE REALTIME                    │   │
│  └────────────────────────┬────────────────────────────┘   │
│                           │                                │
├───────────────────────────┼────────────────────────────────┤
│  ┌──────────┐  ┌──────────┴───┐  ┌──────────────┐         │
│  │  AI      │  │  Handoff     │  │  Timeout     │         │
│  │  Agent   │  │  Manager     │  │  Watcher     │         │
│  │  (LLM)   │  │  (Notif.)    │  │  (Cron)      │         │
│  └──────────┘  └──────────────┘  └──────────────┘         │
├────────────────────────────────────────────────────────────┤
│                   FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Widget   │  │  Painel do   │  │  Painel do   │         │
│  │  Chat     │  │  Atendente   │  │  Admin       │         │
│  └──────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────────────────────────────────────┘
```

## Workflow Principal

### Passo 0: Verificar credenciais

Verifique as variáveis **obrigatórias** e as **de canais configurados**:

```typescript
// SEMPRE obrigatórias
const requiredAlways = [
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  'SUPABASE_SERVICE_ROLE_KEY',
  'LLM_PROVIDER',        // 'openai' ou 'anthropic'
  'LLM_API_KEY',
  'LLM_MODEL',
];

// Obrigatórias POR CANAL habilitado (verificar apenas os configurados)
const channelCredentials = {
  whatsapp_cloud: ['WHATSAPP_CLOUD_TOKEN', 'WHATSAPP_CLOUD_PHONE_ID', 'WHATSAPP_VERIFY_TOKEN'],
  whatsapp_evolution: ['EVOLUTION_API_URL', 'EVOLUTION_API_KEY', 'EVOLUTION_INSTANCE_NAME'],
  whatsapp_zapi: ['ZAPI_URL', 'ZAPI_TOKEN', 'ZAPI_INSTANCE_ID'],
  instagram: ['INSTAGRAM_ACCESS_TOKEN', 'INSTAGRAM_PAGE_ID'],
  telegram: ['TELEGRAM_BOT_TOKEN'],
};
```

Canais não configurados simplesmente não ficam disponíveis. NUNCA prossiga sem credenciais base.

### Passo 1: Criar schema do banco de dados (Supabase)

Leia `resources/references/database-schema.md` para o schema completo.

**Tabelas principais:**
- `channels` — Canais configurados (webchat, whatsapp, instagram, telegram)
- `conversations` — Cada conversa, agora com `channel_id` indicando a origem
- `messages` — Todas as mensagens de qualquer canal
- `agents` — Agentes humanos com canal preferido de notificação
- `handoff_requests` — Solicitações de transferência IA → Humano
- `conversation_assignments` — Histórico de quem atendeu o quê
- `ai_context` — Contexto acumulado para o agente de IA

### Passo 2: Implementar a Channel Adapter Layer

**PASSO CRÍTICO.** Leia `resources/references/omnichannel-spec.md` para a spec completa.

A Channel Adapter Layer normaliza mensagens de/para qualquer canal em formato unificado.
Cada canal implementa a interface `ChannelAdapter`:

```typescript
interface ChannelAdapter {
  readonly channelType: ChannelType;
  parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage>;
  sendMessage(conversationId: string, message: OutgoingMessage): Promise<void>;
  validateWebhook(request: Request): Promise<boolean>;
  healthCheck(): Promise<{ ok: boolean; error?: string }>;
}
```

**Adapters incluídos:**
- `WebchatAdapter` — Widget nativo (sem API externa)
- `WhatsAppCloudAdapter` — API Oficial Meta **← PRIORIDADE**
- `WhatsAppEvolutionAdapter` — Evolution API
- `WhatsAppZApiAdapter` — Z-API
- `InstagramAdapter` — Meta Messenger API para Instagram DM
- `TelegramAdapter` — Telegram Bot API
- `CustomAdapter` — Template para novos canais

**Para adicionar novo canal:** implementar `ChannelAdapter` e registrar no `ChannelRegistry`.

### Passo 3: Criar o Widget de Chat (Webchat)

Leia `resources/references/widget-spec.md`. Funcionalidades iguais à versão anterior.

### Passo 4: Criar o Painel do Atendente (Inbox Unificado)

Leia `resources/references/agent-panel-spec.md`.

**Novidades omnichannel:**
- **Filtro por canal** na sidebar (WhatsApp, Instagram, Telegram, Webchat, Todos)
- **Ícone do canal** em cada conversa (🌐 📱 📸 ✈️)
- Agente responde do painel → resposta entregue no canal do lead via adapter
- **Limitações por canal** sinalizadas (ex: Instagram não suporta botões)

### Passo 5: Implementar o Agente de IA

Leia `resources/references/ai-agent-spec.md`.

O agente adapta tom/formato ao canal:
- **Webchat:** Respostas mais longas com formatação rica
- **WhatsApp:** Curtas, negrito com asteriscos, sem parágrafos longos
- **Instagram DM:** Curtas e informais
- **Telegram:** Markdown, respostas médias

### Passo 6: Implementar o Handoff Manager

Leia `resources/references/handoff-flow-spec.md`.

**Notificação ao agente — agnóstica de canal:**
O agente configura seu `notification_channel` no perfil. O sistema usa o adapter correspondente:
- WhatsApp pessoal → envia via adapter de WhatsApp
- Telegram pessoal → envia via adapter de Telegram
- Apenas painel → browser notification + som
- Múltiplos canais → envia em todos

**Timeout automático:** 10 min padrão, alertas escalonados (80%/90%/100%).

### Passo 7: Implementar o Timeout Watcher

Edge Function (cron) como fonte de verdade + timer client-side como complemento.

### Passo 8: Configurar Webhooks dos Canais

```
src/app/api/webhook/
├── whatsapp/route.ts       # WhatsApp (todos os providers)
├── instagram/route.ts      # Instagram DM
├── telegram/route.ts       # Telegram Bot
└── [custom]/route.ts       # Extensível
```

Cada webhook: valida assinatura → adapter normaliza → cria/atualiza conversa → IA responde.

## Padrões e Templates

### Estrutura de pastas

```
src/
├── app/
│   ├── (public)/chat-widget/
│   ├── (dashboard)/
│   │   ├── atendimento/
│   │   └── admin/channels/            # CRUD de canais
│   └── api/webhook/
│       ├── whatsapp/route.ts
│       ├── instagram/route.ts
│       └── telegram/route.ts
├── components/
│   ├── chat/
│   ├── agent-panel/
│   │   ├── ChannelFilter.tsx
│   │   ├── ChannelBadge.tsx
│   │   └── ...
│   └── ui/
├── lib/
│   ├── channels/                      # ← CHANNEL ADAPTER LAYER
│   │   ├── types.ts                   # Interface ChannelAdapter
│   │   ├── registry.ts               # ChannelRegistry
│   │   └── adapters/
│   │       ├── webchat.ts
│   │       ├── whatsapp-cloud.ts      # API oficial (prioridade)
│   │       ├── whatsapp-evolution.ts
│   │       ├── whatsapp-zapi.ts
│   │       ├── instagram.ts
│   │       ├── telegram.ts
│   │       └── custom-template.ts
│   ├── notifications/agent-notifier.ts
│   ├── ai/
│   └── supabase/
├── hooks/
├── types/index.ts
└── supabase/migrations/
```

### Tipos TypeScript obrigatórios

```typescript
type ChannelType = 'webchat' | 'whatsapp' | 'instagram' | 'telegram' | 'custom';
type WhatsAppProvider = 'cloud_api' | 'evolution' | 'zapi' | 'wppconnect' | 'custom';
type ConversationStatus = 'ai_active' | 'waiting_human' | 'human_active' | 'closed';
type MessageSender = 'lead' | 'ai' | 'human_agent' | 'system';

interface Channel {
  id: string;
  type: ChannelType;
  provider: string;
  name: string;
  config: Record<string, any>;
  is_active: boolean;
}

interface Conversation {
  id: string;
  channel_id: string;
  channel_conversation_id: string;
  status: ConversationStatus;
  current_agent_id: string | null;
  human_inactive_since: string | null;
  lead_name: string;
  lead_email: string | null;
  lead_phone: string | null;
  metadata: Record<string, any>;
}

interface NormalizedMessage {
  externalId: string;
  channelType: ChannelType;
  senderExternalId: string;
  senderName: string;
  content: string;
  contentType: 'text' | 'image' | 'file' | 'audio' | 'video' | 'location';
  attachments?: Attachment[];
  timestamp: Date;
  rawPayload: any;
}
```

## Exemplos

**Exemplo 1: Lead via WhatsApp (API oficial) com handoff**
Input: Lead envia "Oi, quero saber sobre o plano Pro" via WhatsApp
Output: Webhook → WhatsAppCloudAdapter normaliza → IA responde no WhatsApp → Lead pede humano → Handoff → Consultor recebe notificação → Assume pelo painel → Responde (entregue no WhatsApp do lead)

**Exemplo 2: Atendimento simultâneo multicanal**
Input: Lead A no Instagram, Lead B no WhatsApp, Lead C no Webchat
Output: Inbox unificado mostra 3 conversas com ícones de canal. Respostas são roteadas pelo adapter correto.

**Exemplo 3: Troca de provider de WhatsApp**
Input: Migrar de Evolution API para WhatsApp Cloud API oficial
Output: Criar novo channel com provider `cloud_api`, configurar credenciais, desativar channel antigo. Conversas existentes mantidas. Zero mudança de código.

## Armadilhas comuns

- ❌ NUNCA hardcode o provider de WhatsApp → ✅ Use ChannelAdapter; o provider é config, não código
- ❌ NUNCA envie mensagem sem adaptar ao canal → ✅ Cada adapter formata para o canal correto
- ❌ NUNCA ignore rate limits dos canais → ✅ WhatsApp Cloud: 80 msgs/s; Telegram: 30/s; IG: 200/h
- ❌ NUNCA trate webhooks sem validar assinatura → ✅ Valide HMAC/token antes de processar
- ❌ NUNCA perca contexto entre transições → ✅ Resumo via LLM antes de toda transição
- ❌ NUNCA confie apenas no timer client-side → ✅ Edge Function é fonte de verdade
- ❌ NUNCA exponha credenciais de canais → ✅ Campo `config` criptografado na tabela channels
- ❌ NUNCA mostre notas internas ao lead → ✅ Filtre `is_internal_note = true` em TODAS as queries
- ❌ NUNCA assuma recursos iguais em todos os canais → ✅ Consulte `adapter.capabilities`
- ❌ NUNCA deixe RLS desabilitado → ✅ RLS em todas as tabelas

## Checklist de qualidade

- [ ] Variáveis de ambiente base configuradas
- [ ] Pelo menos 1 canal configurado e testado (webchat funciona sem credenciais externas)
- [ ] RLS habilitado em TODAS as tabelas
- [ ] Webhooks respondendo para canais configurados
- [ ] ChannelAdapter envia/recebe corretamente por canal
- [ ] Handoff funciona igual independente do canal
- [ ] Timeout de inatividade funciona via Edge Function
- [ ] Mensagens de sistema entregues no canal do lead
- [ ] Painel mostra ícone do canal em cada conversa
- [ ] Respostas formatadas para o canal específico
- [ ] Nenhuma credencial exposta

## Resources

- `database-schema.md` — Schema SQL com tabela de channels, RLS, triggers
- `omnichannel-spec.md` — Arquitetura omnichannel, interface ChannelAdapter, todos os adapters
- `widget-spec.md` — Especificação do widget Webchat
- `agent-panel-spec.md` — Especificação do painel do atendente (inbox unificado)
- `ai-agent-spec.md` — Lógica do agente de IA (multi-canal)
- `handoff-flow-spec.md` — Fluxos de transição detalhados

---

## Integração com o Fluxo IntelliX (Fase 08)

Esta skill é a **Fase 08** do fluxo IntelliX Engineering Plugin — fase complementar,
acionada quando o projeto inclui atendimento omnichannel com IA + humano.

**Posição no fluxo:**
```
agent-creation → [live-chat] → dev-standards → test-e2e → deploy
```

**Quando usar em combinação com agent-creation:**
- Se a Fase 02 gerou um blueprint de agente de atendimento → use esta skill para o painel
- O `ai-agent-spec.md` desta skill deve ser alimentado com o blueprint da Fase 02
- Canais definidos no blueprint (WhatsApp, Instagram, Telegram) mapeiam diretamente para os adapters desta skill

**Ao concluir esta fase:**
1. Confirme que pelo menos 1 canal está funcionando (webchat não precisa de credenciais externas)
2. Confirme que handoff IA → Humano está operacional
3. Atualize `.intellix-phase` para `dev` (ou retome se veio de agent-creation)
4. Oriente: *"Sistema de chat configurado. Próxima fase: **intellix:dev-standards** para implementação dos demais módulos."*

**Resources desta skill (carregar sob demanda):**
| Arquivo | Quando ler |
|---------|-----------|
| `resources/database-schema.md` | Ao criar as tabelas no Supabase |
| `resources/omnichannel-spec.md` | Ao implementar a Channel Adapter Layer |
| `resources/widget-spec.md` | Ao criar o widget de chat Webchat |
| `resources/agent-panel-spec.md` | Ao criar o painel do atendente |
| `resources/ai-agent-spec.md` | Ao implementar o agente de IA |
| `resources/handoff-flow-spec.md` | Ao implementar o handoff IA → Humano |
| `resources/.env.example` | Ao configurar variáveis de ambiente |

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Sistema de chat standalone já existente que precisa de IA + handoff | `SKILL-chat-inteligente` |
| UI do painel de atendimento com design profissional | `frontend-design-pro` |
| Styling dos componentes de chat com shadcn/ui | `ckm-ui-styling` |
| Integração WhatsApp/n8n para roteamento de canais | `intellix:integration` |
| Schema Supabase do chat com boas práticas de performance | `supabase-postgres-best-practices` |
