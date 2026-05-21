# Widget de Chat — Especificação

Componente público embedável que o lead/cliente usa para conversar.

## Tabela de conteúdos

1. [Visão geral](#visão-geral)
2. [Identificação do lead](#identificação-do-lead)
3. [Interface de chat](#interface-de-chat)
4. [Indicadores de estado](#indicadores-de-estado)
5. [Mensagens de sistema](#mensagens-de-sistema)
6. [Uploads e mídia](#uploads-e-mídia)
7. [Persistência e sessão](#persistência-e-sessão)
8. [Responsividade](#responsividade)
9. [Embed e configuração](#embed-e-configuração)

---

## Visão geral

O widget é um componente React independente que pode ser:
1. Renderizado dentro da própria aplicação Next.js em `/chat-widget`
2. Embedado em sites externos via iframe ou script tag

**Estados visuais:**
- **Minimizado:** Bolha flutuante no canto inferior direito com badge de não lidas
- **Aberto:** Janela de chat com header, área de mensagens e input
- **Formulário:** Tela de identificação antes de iniciar (primeira vez)

## Identificação do lead

Antes da primeira mensagem, exibir formulário:

```typescript
interface LeadIdentification {
  name: string;        // Obrigatório
  email?: string;      // Opcional (configurável como obrigatório)
  phone?: string;      // Opcional (configurável como obrigatório)
}
```

**Fluxo:**
1. Lead clica na bolha → widget abre
2. Se não há sessão existente → exibir formulário
3. Lead preenche e clica "Iniciar conversa"
4. Sistema cria `conversation` e `lead_session_id` (salvo em localStorage)
5. IA envia saudação personalizada usando o nome

**Session ID:** UUID gerado no primeiro acesso, persistido em localStorage.
Permite que o lead reabra a conversa ao voltar ao site.

## Interface de chat

### Header
- Nome do atendente atual: "Assistente Virtual" ou "Atendente [Nome]"
- Avatar do atendente (IA = ícone de bot, humano = foto)
- Indicador de status: "Online" (verde) ou "Digitando..." (animação)
- Botão minimizar (X)

### Área de mensagens
- Scroll infinito para cima (carregar mensagens antigas)
- Auto-scroll para baixo em novas mensagens
- Bolhas de mensagem com:
  - Alinhamento: lead à direita (cor primária), atendente à esquerda (cinza claro)
  - Timestamp abaixo de cada mensagem (formato relativo: "há 2 min")
  - Status de envio: ✓ enviada, ✓✓ lida (para mensagens do lead)
- Mensagens de sistema centralizadas em texto menor e cor neutra
- Separadores de data ("Hoje", "Ontem", "12 de março")

### Input
- Textarea com auto-resize (min 1 linha, max 5 linhas)
- Botão de envio (desabilitado quando vazio)
- Botão de upload (ícone de clip) para imagens e arquivos
- Placeholder contextual: "Digite sua mensagem..." ou "Aguardando atendente..."
- Enter para enviar, Shift+Enter para nova linha
- Desabilitado durante `waiting_human` com mensagem "Aguardando atendente..."

### Botão "Falar com humano"
- Sempre visível no header ou acima do input
- Ao clicar: IA inicia fluxo de handoff (Fluxo 1)
- Durante `waiting_human`: botão muda para "Aguardando atendente..." (desabilitado)
- Durante `human_active`: botão oculto (já está com humano)

## Indicadores de estado

| Estado da conversa | O que o lead vê |
|---|---|
| `ai_active` | Header: "Assistente Virtual 🤖" / Input habilitado |
| `waiting_human` | Header: "Conectando com atendente..." / Input desabilitado / Spinner |
| `human_active` | Header: "Atendente [Nome] 👤" / Input habilitado |
| `closed` | Header: "Atendimento encerrado" / Botão "Iniciar nova conversa" |

### Typing indicator
- Mostrar "digitando..." com animação de 3 pontos
- Para IA: enquanto aguarda resposta do LLM
- Para humano: via Supabase Realtime Presence (agente está digitando)

## Mensagens de sistema

Mensagens automáticas que aparecem centralizadas:

```typescript
const SYSTEM_MESSAGES = {
  agent_joined: (name: string) => `O atendente ${name} entrou na conversa`,
  agent_left: (name: string) => `O atendente ${name} encerrou o atendimento`,
  transferring: 'Transferindo para um atendente humano...',
  ai_resumed: 'O assistente virtual retomou o atendimento',
  conversation_closed: 'Atendimento encerrado. Obrigado pelo contato!',
  waiting_expired: 'Nossos atendentes estão ocupados. O assistente virtual vai continuar te ajudando.',
};
```

## Uploads e mídia

**Tipos aceitos:**
- Imagens: jpg, png, gif, webp (max 5MB)
- Documentos: pdf, doc, docx, xls, xlsx (max 10MB)

**Fluxo de upload:**
1. Lead seleciona arquivo via botão ou drag-and-drop
2. Preview inline (thumbnail para imagens, ícone + nome para docs)
3. Upload para Supabase Storage
4. Mensagem criada com `content_type: 'image'` ou `'file'` e URL no metadata

**Armazenamento:** Bucket `chat-uploads` no Supabase Storage com policy:
- Upload: qualquer um com session_id válido
- Download: qualquer participante da conversa

## Persistência e sessão

- `lead_session_id` salvo em localStorage do browser
- Ao reabrir o widget: carregar última conversa do session_id
- Se conversa `closed`: perguntar se quer iniciar nova
- Se conversa `ai_active` ou `human_active`: retomar de onde parou
- Carregar últimas 30 mensagens inicialmente, scroll para mais

## Responsividade

- **Desktop:** Janela flutuante 380x550px no canto inferior direito
- **Mobile:** Fullscreen overlay com botão de fechar
- **Breakpoint:** 640px (abaixo = mobile mode)

## Embed e configuração

### Via componente React (mesma app)
```tsx
<ChatWidget 
  supabaseUrl={process.env.NEXT_PUBLIC_SUPABASE_URL}
  supabaseKey={process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}
  config={{
    title: 'Atendimento IntelliX',
    subtitle: 'Estamos online!',
    primaryColor: '#6366f1',
    position: 'bottom-right',
    requireEmail: true,
    requirePhone: false,
    welcomeMessage: 'Olá! Como posso ajudar?',
    offlineMessage: 'Estamos offline, mas deixe sua mensagem!',
  }}
/>
```

### Via iframe (site externo)
```html
<iframe 
  src="https://seu-app.vercel.app/chat-widget?config=base64encodedconfig"
  style="position:fixed;bottom:20px;right:20px;width:380px;height:550px;border:none;z-index:9999;"
/>
```

### Via script tag (site externo)
```html
<script 
  src="https://seu-app.vercel.app/widget.js"
  data-supabase-url="..."
  data-supabase-key="..."
  data-primary-color="#6366f1"
  data-title="Atendimento"
></script>
```
