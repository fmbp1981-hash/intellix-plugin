# Omnichannel Spec — Channel Adapter Layer

Arquitetura completa do sistema omnichannel com adapters para cada canal de mensageria.

## Tabela de conteúdos

1. [Princípios de design](#princípios-de-design)
2. [Interface ChannelAdapter](#interface-channeladapter)
3. [ChannelRegistry](#channelregistry)
4. [Normalização de mensagens](#normalização-de-mensagens)
5. [Adapter: Webchat](#adapter-webchat)
6. [Adapter: WhatsApp Cloud API (oficial)](#adapter-whatsapp-cloud-api)
7. [Adapter: WhatsApp Evolution API](#adapter-whatsapp-evolution-api)
8. [Adapter: WhatsApp Z-API](#adapter-whatsapp-z-api)
9. [Adapter: Instagram DM](#adapter-instagram-dm)
10. [Adapter: Telegram](#adapter-telegram)
11. [Como criar um adapter customizado](#como-criar-adapter-customizado)
12. [Tabela channels no banco](#tabela-channels)
13. [Formatação por canal](#formatação-por-canal)
14. [Rate limits por canal](#rate-limits-por-canal)
15. [Notificação de agentes via canal](#notificação-de-agentes)
16. [Webhook routing](#webhook-routing)

---

## Princípios de design

1. **Provider é configuração, não código.** Trocar de Evolution API para Cloud API é mudar uma
   row no banco, não reescrever lógica.
2. **Formato interno unificado.** Todas as mensagens — de qualquer canal — viram `NormalizedMessage`
   antes de serem processadas. O resto do sistema nunca fala direto com APIs de canais.
3. **Adapter Pattern.** Cada canal implementa `ChannelAdapter`. Para adicionar Messenger, SMS,
   ou qualquer canal futuro: crie um adapter e registre no `ChannelRegistry`.
4. **Graceful degradation.** Se um canal não suporta botões (ex: SMS), o adapter converte para
   texto. Se não suporta imagens (ex: limitação temporária), envia link.
5. **API oficial do WhatsApp como prioridade.** Quando o usuário não especificar provider,
   sugerir WhatsApp Cloud API (Meta) por ser a mais estável e oficial.

---

## Interface ChannelAdapter

```typescript
// lib/channels/types.ts

type ChannelType = 'webchat' | 'whatsapp' | 'instagram' | 'telegram' | 'custom';

interface ChannelCapabilities {
  supportsImages: boolean;
  supportsFiles: boolean;
  supportsAudio: boolean;
  supportsVideo: boolean;
  supportsButtons: boolean;
  supportsLocation: boolean;
  supportsTypingIndicator: boolean;
  supportsReadReceipts: boolean;
  maxMessageLength: number;         // Caracteres por mensagem
  maxFileSize: number;              // Bytes
  supportedFileTypes: string[];     // MIME types
}

interface ChannelAdapter {
  readonly channelType: ChannelType;
  readonly provider: string;         // Ex: 'cloud_api', 'evolution', 'native'
  readonly capabilities: ChannelCapabilities;

  // RECEBER: converte payload do webhook para formato interno
  parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage>;

  // ENVIAR: converte formato interno para API do canal e envia
  sendMessage(
    channelConversationId: string,  // ID externo (phone, chat_id, etc.)
    message: OutgoingMessage,
    channelConfig: Record<string, any>  // Credenciais do canal
  ): Promise<SendResult>;

  // WEBHOOK: valida assinatura/token do webhook
  validateWebhook(request: Request, channelConfig: Record<string, any>): Promise<boolean>;

  // HEALTH: verifica se canal está operacional
  healthCheck(channelConfig: Record<string, any>): Promise<HealthCheckResult>;

  // FORMATO: adapta texto para o formato do canal
  formatText(text: string): string;
}

interface NormalizedMessage {
  externalId: string;
  channelType: ChannelType;
  senderExternalId: string;       // Phone number, username, chat_id
  senderName: string;
  content: string;
  contentType: 'text' | 'image' | 'file' | 'audio' | 'video' | 'location';
  attachments?: Array<{
    type: string;
    url: string;
    mimeType?: string;
    fileName?: string;
    caption?: string;
  }>;
  timestamp: Date;
  rawPayload: any;                // Preservar original para debugging
}

interface OutgoingMessage {
  content: string;
  contentType: 'text' | 'image' | 'file' | 'audio';
  attachmentUrl?: string;
  buttons?: Array<{ label: string; value: string }>;
  metadata?: Record<string, any>;
}

interface SendResult {
  success: boolean;
  externalMessageId?: string;
  error?: string;
}

interface HealthCheckResult {
  ok: boolean;
  latency?: number;
  error?: string;
}
```

---

## ChannelRegistry

```typescript
// lib/channels/registry.ts

import { WebchatAdapter } from './adapters/webchat';
import { WhatsAppCloudAdapter } from './adapters/whatsapp-cloud';
import { WhatsAppEvolutionAdapter } from './adapters/whatsapp-evolution';
import { WhatsAppZApiAdapter } from './adapters/whatsapp-zapi';
import { InstagramAdapter } from './adapters/instagram';
import { TelegramAdapter } from './adapters/telegram';

class ChannelRegistry {
  private adapters: Map<string, ChannelAdapter> = new Map();

  constructor() {
    // Registrar adapters built-in
    this.register('webchat:native', new WebchatAdapter());
    this.register('whatsapp:cloud_api', new WhatsAppCloudAdapter());
    this.register('whatsapp:evolution', new WhatsAppEvolutionAdapter());
    this.register('whatsapp:zapi', new WhatsAppZApiAdapter());
    this.register('instagram:meta', new InstagramAdapter());
    this.register('telegram:bot_api', new TelegramAdapter());
  }

  // Chave: "channelType:provider"
  register(key: string, adapter: ChannelAdapter): void {
    this.adapters.set(key, adapter);
  }

  // Buscar adapter por canal do banco de dados
  getAdapter(channel: { type: ChannelType; provider: string }): ChannelAdapter {
    const key = `${channel.type}:${channel.provider}`;
    const adapter = this.adapters.get(key);
    if (!adapter) {
      throw new Error(`Adapter não encontrado para canal: ${key}. ` +
        `Adapters disponíveis: ${Array.from(this.adapters.keys()).join(', ')}`);
    }
    return adapter;
  }

  // Listar adapters disponíveis
  listAvailable(): string[] {
    return Array.from(this.adapters.keys());
  }
}

// Singleton
export const channelRegistry = new ChannelRegistry();
```

**Uso no sistema:**
```typescript
// Em qualquer lugar que precise enviar mensagem
const channel = await getChannelById(conversation.channel_id);
const adapter = channelRegistry.getAdapter(channel);
await adapter.sendMessage(
  conversation.channel_conversation_id,
  { content: 'Olá!', contentType: 'text' },
  channel.config  // Credenciais
);
```

---

## Normalização de mensagens

```typescript
// lib/channels/normalizer.ts

// Recebe webhook raw → normaliza → salva no banco
async function processIncomingWebhook(
  channelId: string,
  rawPayload: any
): Promise<void> {
  const channel = await getChannelById(channelId);
  const adapter = channelRegistry.getAdapter(channel);

  // 1. Validar (já feito no webhook route, mas double-check)
  // 2. Normalizar
  const normalized = await adapter.parseIncomingMessage(rawPayload);

  // 3. Encontrar ou criar conversa
  let conversation = await findConversationByExternalId(
    channelId, normalized.senderExternalId
  );

  if (!conversation) {
    conversation = await createConversation({
      channel_id: channelId,
      channel_conversation_id: normalized.senderExternalId,
      lead_name: normalized.senderName,
      lead_phone: normalized.channelType === 'whatsapp' ? normalized.senderExternalId : null,
      status: 'ai_active',
      metadata: { channel_type: normalized.channelType, source: channel.name }
    });
  }

  // 4. Salvar mensagem normalizada
  await saveMessage({
    conversation_id: conversation.id,
    sender_type: 'lead',
    sender_name: normalized.senderName,
    content: normalized.content,
    content_type: normalized.contentType,
    metadata: {
      external_id: normalized.externalId,
      channel_type: normalized.channelType,
      attachments: normalized.attachments,
      raw_payload: normalized.rawPayload
    }
  });

  // 5. Se IA ativa, gerar resposta
  if (conversation.status === 'ai_active') {
    const aiResponse = await generateAiResponse(conversation.id);
    // Enviar de volta pelo mesmo canal
    await adapter.sendMessage(
      conversation.channel_conversation_id,
      { content: adapter.formatText(aiResponse), contentType: 'text' },
      channel.config
    );
  }
}
```

---

## Adapter: Webchat

O canal nativo. Não usa API externa — funciona via Supabase Realtime.

```typescript
// lib/channels/adapters/webchat.ts

export class WebchatAdapter implements ChannelAdapter {
  readonly channelType = 'webchat' as const;
  readonly provider = 'native';
  readonly capabilities: ChannelCapabilities = {
    supportsImages: true,
    supportsFiles: true,
    supportsAudio: true,
    supportsVideo: false,
    supportsButtons: true,
    supportsLocation: false,
    supportsTypingIndicator: true,
    supportsReadReceipts: true,
    maxMessageLength: 10000,
    maxFileSize: 10 * 1024 * 1024, // 10MB
    supportedFileTypes: ['image/*', 'application/pdf', '.doc', '.docx', '.xls', '.xlsx'],
  };

  async parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage> {
    // Webchat já envia no formato interno via Supabase
    return {
      externalId: rawPayload.id,
      channelType: 'webchat',
      senderExternalId: rawPayload.session_id,
      senderName: rawPayload.sender_name,
      content: rawPayload.content,
      contentType: rawPayload.content_type || 'text',
      attachments: rawPayload.attachments,
      timestamp: new Date(rawPayload.created_at),
      rawPayload
    };
  }

  async sendMessage(conversationId: string, message: OutgoingMessage): Promise<SendResult> {
    // Webchat: salvar no banco + Supabase Realtime entrega automaticamente
    // Não precisa chamar API externa
    return { success: true };
  }

  async validateWebhook(): Promise<boolean> {
    return true; // Webchat não usa webhook externo
  }

  async healthCheck(): Promise<HealthCheckResult> {
    return { ok: true }; // Sempre disponível
  }

  formatText(text: string): string {
    return text; // Webchat suporta HTML/Markdown, sem adaptação necessária
  }
}
```

---

## Adapter: WhatsApp Cloud API

**API oficial do Meta.** Prioridade quando o usuário não especifica provider.

```typescript
// lib/channels/adapters/whatsapp-cloud.ts

export class WhatsAppCloudAdapter implements ChannelAdapter {
  readonly channelType = 'whatsapp' as const;
  readonly provider = 'cloud_api';
  readonly capabilities: ChannelCapabilities = {
    supportsImages: true,
    supportsFiles: true,
    supportsAudio: true,
    supportsVideo: true,
    supportsButtons: true,        // Interactive messages
    supportsLocation: true,
    supportsTypingIndicator: false, // Cloud API não suporta typing nativo
    supportsReadReceipts: true,
    maxMessageLength: 4096,
    maxFileSize: 16 * 1024 * 1024, // 16MB
    supportedFileTypes: ['image/jpeg', 'image/png', 'application/pdf', 'audio/ogg', 'video/mp4'],
  };

  private baseUrl = 'https://graph.facebook.com/v21.0';

  async parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage> {
    // Payload do WhatsApp Cloud API webhook
    const entry = rawPayload.entry?.[0];
    const change = entry?.changes?.[0];
    const message = change?.value?.messages?.[0];
    const contact = change?.value?.contacts?.[0];

    if (!message) throw new Error('No message in webhook payload');

    return {
      externalId: message.id,
      channelType: 'whatsapp',
      senderExternalId: message.from,     // Phone number
      senderName: contact?.profile?.name || message.from,
      content: this.extractContent(message),
      contentType: this.mapContentType(message.type),
      attachments: this.extractAttachments(message),
      timestamp: new Date(parseInt(message.timestamp) * 1000),
      rawPayload
    };
  }

  async sendMessage(
    phoneNumber: string,
    message: OutgoingMessage,
    config: { token: string; phoneId: string }
  ): Promise<SendResult> {
    const url = `${this.baseUrl}/${config.phoneId}/messages`;

    const body: any = {
      messaging_product: 'whatsapp',
      to: phoneNumber,
      type: message.contentType === 'text' ? 'text' : message.contentType,
    };

    if (message.contentType === 'text') {
      body.text = { body: message.content };
    } else if (message.contentType === 'image') {
      body.image = { link: message.attachmentUrl, caption: message.content };
    }

    // Botões interativos (se suportado)
    if (message.buttons?.length) {
      body.type = 'interactive';
      body.interactive = {
        type: 'button',
        body: { text: message.content },
        action: {
          buttons: message.buttons.map((btn, i) => ({
            type: 'reply',
            reply: { id: `btn_${i}`, title: btn.label.slice(0, 20) }
          }))
        }
      };
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${config.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: JSON.stringify(error) };
      }

      const data = await response.json();
      return { success: true, externalMessageId: data.messages?.[0]?.id };
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  async validateWebhook(
    request: Request,
    config: { verifyToken: string }
  ): Promise<boolean> {
    // GET = verificação do webhook (challenge)
    const url = new URL(request.url);
    if (request.method === 'GET') {
      return url.searchParams.get('hub.verify_token') === config.verifyToken;
    }
    // POST = validar assinatura HMAC-SHA256
    // Implementar validação do X-Hub-Signature-256
    return true; // Simplificado — implementar HMAC em produção
  }

  async healthCheck(config: { token: string; phoneId: string }): Promise<HealthCheckResult> {
    try {
      const start = Date.now();
      const res = await fetch(`${this.baseUrl}/${config.phoneId}`, {
        headers: { 'Authorization': `Bearer ${config.token}` }
      });
      return { ok: res.ok, latency: Date.now() - start };
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  }

  formatText(text: string): string {
    // WhatsApp: converter **bold** para *bold*, manter curto
    return text
      .replace(/\*\*(.*?)\*\*/g, '*$1*')  // Markdown bold → WhatsApp bold
      .replace(/#{1,3}\s/g, '*')            // Headers → bold
      .slice(0, 4096);                      // Respeitar limite
  }

  private extractContent(message: any): string {
    switch (message.type) {
      case 'text': return message.text.body;
      case 'image': return message.image?.caption || '[Imagem]';
      case 'document': return message.document?.caption || `[Documento: ${message.document?.filename}]`;
      case 'audio': return '[Áudio]';
      case 'video': return message.video?.caption || '[Vídeo]';
      case 'location': return `[Localização: ${message.location.latitude}, ${message.location.longitude}]`;
      case 'interactive':
        return message.interactive?.button_reply?.title ||
               message.interactive?.list_reply?.title || '[Resposta interativa]';
      default: return `[${message.type}]`;
    }
  }

  private mapContentType(type: string): NormalizedMessage['contentType'] {
    const map: Record<string, NormalizedMessage['contentType']> = {
      text: 'text', image: 'image', document: 'file',
      audio: 'audio', video: 'video', location: 'location'
    };
    return map[type] || 'text';
  }

  private extractAttachments(message: any): NormalizedMessage['attachments'] {
    if (message.type === 'text') return undefined;
    // Attachments precisam ser baixados via Graph API usando o media ID
    const mediaId = message[message.type]?.id;
    if (!mediaId) return undefined;
    return [{ type: message.type, url: `media://${mediaId}`, mimeType: message[message.type]?.mime_type }];
  }
}
```

---

## Adapter: WhatsApp Evolution API

```typescript
// lib/channels/adapters/whatsapp-evolution.ts

export class WhatsAppEvolutionAdapter implements ChannelAdapter {
  readonly channelType = 'whatsapp' as const;
  readonly provider = 'evolution';
  readonly capabilities: ChannelCapabilities = {
    supportsImages: true, supportsFiles: true, supportsAudio: true,
    supportsVideo: true, supportsButtons: true, supportsLocation: true,
    supportsTypingIndicator: true, supportsReadReceipts: true,
    maxMessageLength: 4096, maxFileSize: 16 * 1024 * 1024,
    supportedFileTypes: ['image/jpeg', 'image/png', 'application/pdf', 'audio/ogg'],
  };

  async parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage> {
    const msg = rawPayload.data;
    return {
      externalId: msg.key?.id || msg.messageId,
      channelType: 'whatsapp',
      senderExternalId: msg.key?.remoteJid?.replace('@s.whatsapp.net', '') || msg.from,
      senderName: msg.pushName || msg.from,
      content: msg.message?.conversation || msg.message?.extendedTextMessage?.text || '[Mídia]',
      contentType: this.detectContentType(msg),
      timestamp: new Date(msg.messageTimestamp * 1000),
      rawPayload
    };
  }

  async sendMessage(
    phone: string,
    message: OutgoingMessage,
    config: { url: string; apiKey: string; instanceName: string }
  ): Promise<SendResult> {
    const endpoint = message.contentType === 'text'
      ? `${config.url}/message/sendText/${config.instanceName}`
      : `${config.url}/message/sendMedia/${config.instanceName}`;

    const body: any = { number: phone };

    if (message.contentType === 'text') {
      body.text = message.content;
    } else {
      body.mediatype = message.contentType;
      body.media = message.attachmentUrl;
      body.caption = message.content;
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'apikey': config.apiKey },
      body: JSON.stringify(body)
    });

    if (!res.ok) return { success: false, error: await res.text() };
    return { success: true };
  }

  async validateWebhook(request: Request, config: { apiKey: string }): Promise<boolean> {
    // Evolution API usa apikey no header do webhook
    const apiKey = request.headers.get('apikey');
    return apiKey === config.apiKey;
  }

  async healthCheck(config: { url: string; apiKey: string; instanceName: string }): Promise<HealthCheckResult> {
    try {
      const start = Date.now();
      const res = await fetch(`${config.url}/instance/connectionState/${config.instanceName}`, {
        headers: { 'apikey': config.apiKey }
      });
      const data = await res.json();
      return { ok: data.state === 'open', latency: Date.now() - start };
    } catch (error) {
      return { ok: false, error: String(error) };
    }
  }

  formatText(text: string): string {
    return text.replace(/\*\*(.*?)\*\*/g, '*$1*').slice(0, 4096);
  }

  private detectContentType(msg: any): NormalizedMessage['contentType'] {
    if (msg.message?.imageMessage) return 'image';
    if (msg.message?.documentMessage) return 'file';
    if (msg.message?.audioMessage) return 'audio';
    if (msg.message?.videoMessage) return 'video';
    return 'text';
  }
}
```

---

## Adapter: WhatsApp Z-API

```typescript
// lib/channels/adapters/whatsapp-zapi.ts

export class WhatsAppZApiAdapter implements ChannelAdapter {
  readonly channelType = 'whatsapp' as const;
  readonly provider = 'zapi';
  // capabilities similar ao Evolution

  async sendMessage(
    phone: string,
    message: OutgoingMessage,
    config: { url: string; token: string; instanceId: string }
  ): Promise<SendResult> {
    const endpoint = `${config.url}/instances/${config.instanceId}/token/${config.token}/send-text`;

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, message: message.content })
    });

    if (!res.ok) return { success: false, error: await res.text() };
    return { success: true };
  }

  // parseIncomingMessage, validateWebhook, healthCheck, formatText: similares ao Evolution
  // Adaptar para o formato de payload da Z-API
}
```

---

## Adapter: Instagram DM

```typescript
// lib/channels/adapters/instagram.ts

export class InstagramAdapter implements ChannelAdapter {
  readonly channelType = 'instagram' as const;
  readonly provider = 'meta';
  readonly capabilities: ChannelCapabilities = {
    supportsImages: true, supportsFiles: false, supportsAudio: false,
    supportsVideo: false, supportsButtons: false,  // Instagram DM não suporta botões
    supportsLocation: false, supportsTypingIndicator: false,
    supportsReadReceipts: true,
    maxMessageLength: 1000,
    maxFileSize: 8 * 1024 * 1024,
    supportedFileTypes: ['image/jpeg', 'image/png'],
  };

  private baseUrl = 'https://graph.facebook.com/v21.0';

  async parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage> {
    // Instagram usa o mesmo formato de webhook do Messenger
    const entry = rawPayload.entry?.[0];
    const messaging = entry?.messaging?.[0];

    return {
      externalId: messaging.message.mid,
      channelType: 'instagram',
      senderExternalId: messaging.sender.id,
      senderName: messaging.sender.id, // Buscar nome via Graph API se necessário
      content: messaging.message.text || '[Mídia]',
      contentType: messaging.message.attachments ? 'image' : 'text',
      attachments: messaging.message.attachments?.map((a: any) => ({
        type: a.type, url: a.payload.url
      })),
      timestamp: new Date(messaging.timestamp),
      rawPayload
    };
  }

  async sendMessage(
    recipientId: string,
    message: OutgoingMessage,
    config: { accessToken: string; pageId: string }
  ): Promise<SendResult> {
    const url = `${this.baseUrl}/${config.pageId}/messages`;

    const body: any = {
      recipient: { id: recipientId },
      message: {}
    };

    if (message.contentType === 'text') {
      body.message.text = message.content.slice(0, 1000); // Limite IG
    } else if (message.contentType === 'image') {
      body.message.attachment = {
        type: 'image',
        payload: { url: message.attachmentUrl }
      };
    }

    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) return { success: false, error: await res.text() };
    const data = await res.json();
    return { success: true, externalMessageId: data.message_id };
  }

  async validateWebhook(request: Request, config: { verifyToken: string }): Promise<boolean> {
    // Mesmo padrão do WhatsApp Cloud (Meta platform)
    if (request.method === 'GET') {
      const url = new URL(request.url);
      return url.searchParams.get('hub.verify_token') === config.verifyToken;
    }
    return true;
  }

  async healthCheck(config: { accessToken: string; pageId: string }): Promise<HealthCheckResult> {
    try {
      const res = await fetch(`${this.baseUrl}/${config.pageId}?access_token=${config.accessToken}`);
      return { ok: res.ok };
    } catch (e) { return { ok: false, error: String(e) }; }
  }

  formatText(text: string): string {
    // Instagram DM: sem formatação rica, manter informal e curto
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1')  // Remover bold (IG não suporta)
      .replace(/#{1,3}\s/g, '')           // Remover headers
      .slice(0, 1000);
  }
}
```

---

## Adapter: Telegram

```typescript
// lib/channels/adapters/telegram.ts

export class TelegramAdapter implements ChannelAdapter {
  readonly channelType = 'telegram' as const;
  readonly provider = 'bot_api';
  readonly capabilities: ChannelCapabilities = {
    supportsImages: true, supportsFiles: true, supportsAudio: true,
    supportsVideo: true, supportsButtons: true,   // Inline keyboards
    supportsLocation: true, supportsTypingIndicator: true,
    supportsReadReceipts: false,
    maxMessageLength: 4096,
    maxFileSize: 50 * 1024 * 1024,  // 50MB
    supportedFileTypes: ['*/*'],     // Telegram aceita quase tudo
  };

  private baseUrl = 'https://api.telegram.org';

  async parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage> {
    const message = rawPayload.message || rawPayload.edited_message;
    const from = message.from;

    return {
      externalId: String(message.message_id),
      channelType: 'telegram',
      senderExternalId: String(message.chat.id),
      senderName: [from.first_name, from.last_name].filter(Boolean).join(' ') || from.username,
      content: message.text || message.caption || '[Mídia]',
      contentType: this.detectContentType(message),
      attachments: this.extractAttachments(message),
      timestamp: new Date(message.date * 1000),
      rawPayload
    };
  }

  async sendMessage(
    chatId: string,
    message: OutgoingMessage,
    config: { botToken: string }
  ): Promise<SendResult> {
    let endpoint = `${this.baseUrl}/bot${config.botToken}`;
    let body: any = { chat_id: chatId };

    if (message.contentType === 'text') {
      endpoint += '/sendMessage';
      body.text = message.content;
      body.parse_mode = 'Markdown';

      // Botões inline
      if (message.buttons?.length) {
        body.reply_markup = {
          inline_keyboard: [message.buttons.map(btn => ({
            text: btn.label,
            callback_data: btn.value
          }))]
        };
      }
    } else if (message.contentType === 'image') {
      endpoint += '/sendPhoto';
      body.photo = message.attachmentUrl;
      body.caption = message.content;
    } else if (message.contentType === 'file') {
      endpoint += '/sendDocument';
      body.document = message.attachmentUrl;
      body.caption = message.content;
    }

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (!res.ok) return { success: false, error: await res.text() };
    const data = await res.json();
    return { success: true, externalMessageId: String(data.result?.message_id) };
  }

  async validateWebhook(request: Request, config: { secretToken?: string }): Promise<boolean> {
    if (config.secretToken) {
      return request.headers.get('X-Telegram-Bot-Api-Secret-Token') === config.secretToken;
    }
    return true;
  }

  async healthCheck(config: { botToken: string }): Promise<HealthCheckResult> {
    try {
      const start = Date.now();
      const res = await fetch(`${this.baseUrl}/bot${config.botToken}/getMe`);
      return { ok: res.ok, latency: Date.now() - start };
    } catch (e) { return { ok: false, error: String(e) }; }
  }

  formatText(text: string): string {
    // Telegram: suporta Markdown nativo
    return text.slice(0, 4096);
  }

  private detectContentType(msg: any): NormalizedMessage['contentType'] {
    if (msg.photo) return 'image';
    if (msg.document) return 'file';
    if (msg.voice || msg.audio) return 'audio';
    if (msg.video) return 'video';
    if (msg.location) return 'location';
    return 'text';
  }

  private extractAttachments(msg: any): NormalizedMessage['attachments'] {
    if (msg.photo) {
      const largest = msg.photo[msg.photo.length - 1];
      return [{ type: 'image', url: `telegram://file/${largest.file_id}` }];
    }
    if (msg.document) {
      return [{ type: 'file', url: `telegram://file/${msg.document.file_id}`, fileName: msg.document.file_name }];
    }
    return undefined;
  }
}
```

---

## Como criar adapter customizado

```typescript
// lib/channels/adapters/custom-template.ts

import type { ChannelAdapter, ChannelCapabilities, NormalizedMessage, OutgoingMessage, SendResult, HealthCheckResult } from '../types';

export class MyCustomAdapter implements ChannelAdapter {
  readonly channelType = 'custom' as const;
  readonly provider = 'my_service';
  readonly capabilities: ChannelCapabilities = {
    supportsImages: true,
    supportsFiles: false,
    // ... definir capacidades do seu canal
  };

  async parseIncomingMessage(rawPayload: any): Promise<NormalizedMessage> {
    // Adaptar o payload do webhook do seu serviço para NormalizedMessage
    throw new Error('Implementar parseIncomingMessage');
  }

  async sendMessage(recipientId: string, message: OutgoingMessage, config: any): Promise<SendResult> {
    // Chamar API do seu serviço para enviar mensagem
    throw new Error('Implementar sendMessage');
  }

  async validateWebhook(request: Request, config: any): Promise<boolean> {
    // Validar assinatura/token do webhook
    throw new Error('Implementar validateWebhook');
  }

  async healthCheck(config: any): Promise<HealthCheckResult> {
    // Verificar se o serviço está operacional
    throw new Error('Implementar healthCheck');
  }

  formatText(text: string): string {
    return text;
  }
}

// REGISTRAR no ChannelRegistry:
// channelRegistry.register('custom:my_service', new MyCustomAdapter());
```

---

## Tabela channels

```sql
CREATE TABLE channels (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT NOT NULL,          -- 'webchat', 'whatsapp', 'instagram', 'telegram', 'custom'
  provider TEXT NOT NULL,      -- 'native', 'cloud_api', 'evolution', 'zapi', 'meta', 'bot_api'
  name TEXT NOT NULL,          -- Nome amigável: "WhatsApp Comercial", "Instagram @loja"
  config JSONB NOT NULL DEFAULT '{}',  -- Credenciais e configurações (criptografar em produção)
  is_active BOOLEAN DEFAULT true,
  webhook_url TEXT,            -- URL do webhook configurado
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(type, provider, name)
);

-- Exemplo de rows:
-- INSERT INTO channels (type, provider, name, config) VALUES
--   ('webchat', 'native', 'Chat do Site', '{}'),
--   ('whatsapp', 'cloud_api', 'WhatsApp Comercial', '{"token":"...","phoneId":"...","verifyToken":"..."}'),
--   ('instagram', 'meta', 'Instagram @minhaloja', '{"accessToken":"...","pageId":"..."}'),
--   ('telegram', 'bot_api', 'Bot Telegram', '{"botToken":"..."}');
```

---

## Formatação por canal

| Canal | Bold | Itálico | Links | Máx chars | Notas |
|-------|------|---------|-------|-----------|-------|
| Webchat | `**bold**` | `*italic*` | Clicáveis | 10000 | Suporta HTML/Markdown |
| WhatsApp | `*bold*` | `_italic_` | Auto-link | 4096 | Sem headers, sem listas |
| Instagram | Nenhum | Nenhum | Auto-link | 1000 | Zero formatação rica |
| Telegram | `*bold*` | `_italic_` | `[texto](url)` | 4096 | Markdown nativo |

---

## Rate limits por canal

| Canal | Limite | Janela | Ação ao exceder |
|-------|--------|--------|-----------------|
| WhatsApp Cloud API | 80 msgs/s (business) | Por segundo | Enfileirar |
| WhatsApp Evolution | Sem limite oficial | - | Respeitar delays de 1-2s |
| WhatsApp Z-API | Varia por plano | - | Consultar docs |
| Instagram DM | 200 msgs/h | Por hora | Enfileirar + alertar admin |
| Telegram Bot | 30 msgs/s | Por segundo | Enfileirar |
| Webchat | Sem limite | - | Throttle no client (1 msg/s) |

---

## Notificação de agentes

O sistema de notificação dos agentes também usa adapters, tornando-o agnóstico:

```typescript
// lib/notifications/agent-notifier.ts

async function notifyAgent(agent: Agent, notification: AgentNotification) {
  const channels = agent.notification_channels; // Ex: ['whatsapp', 'browser']

  for (const channelType of channels) {
    if (channelType === 'browser') {
      // Push notification via Supabase Realtime
      await sendBrowserNotification(agent.id, notification);
      continue;
    }

    if (channelType === 'email') {
      await sendEmailNotification(agent.email, notification);
      continue;
    }

    // Para WhatsApp, Telegram, etc: usar o adapter configurado
    const channel = await findNotificationChannel(channelType);
    if (!channel) continue;

    const adapter = channelRegistry.getAdapter(channel);
    await adapter.sendMessage(
      agent.phone || agent.telegram_id, // Depende do canal
      { content: adapter.formatText(notification.message), contentType: 'text' },
      channel.config
    );
  }
}
```

O agente configura no perfil: `notification_channels: ['whatsapp', 'browser']`
O campo `phone` é usado para WhatsApp, `telegram_id` para Telegram, etc.

---

## Webhook routing

```typescript
// src/app/api/webhook/whatsapp/route.ts

import { channelRegistry } from '@/lib/channels/registry';
import { processIncomingWebhook } from '@/lib/channels/normalizer';

export async function POST(request: Request) {
  const body = await request.json();

  // Identificar qual channel (pode ter múltiplos WhatsApp configurados)
  const channelId = identifyChannelFromPayload(body);
  const channel = await getChannelById(channelId);
  const adapter = channelRegistry.getAdapter(channel);

  // Validar webhook
  if (!await adapter.validateWebhook(request, channel.config)) {
    return new Response('Unauthorized', { status: 401 });
  }

  // Processar
  await processIncomingWebhook(channelId, body);

  return new Response('OK', { status: 200 });
}

// GET para verificação de webhook (WhatsApp Cloud API e Instagram)
export async function GET(request: Request) {
  const url = new URL(request.url);
  const verifyToken = url.searchParams.get('hub.verify_token');
  const challenge = url.searchParams.get('hub.challenge');

  // Verificar token contra channels configurados
  const channels = await getActiveChannelsByType('whatsapp');
  for (const ch of channels) {
    if (ch.config.verifyToken === verifyToken) {
      return new Response(challenge, { status: 200 });
    }
  }

  return new Response('Forbidden', { status: 403 });
}
```
