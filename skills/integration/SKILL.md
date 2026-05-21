---
name: integration
description: >
  Use esta skill sempre que o projeto precisar de integrações externas — APIs de terceiros,
  WhatsApp, envio de emails, pagamentos, webhooks recebidos, SDKs de IA, ou comunicação
  entre serviços. Esta é a Fase 05 do fluxo IntelliX. A abordagem padrão é integração
  nativa dentro do sistema (Next.js + TypeScript + Supabase) — n8n é usado apenas como
  camada de orquestração opcional para fluxos complexos de automação. Também ativa quando
  o usuário mencionar: n8n, Evolution API, WhatsApp, webhook, integração, API externa,
  Anthropic SDK, OpenAI SDK, pagamento, email, Supabase Edge Function, conectar com.
user-invocable: false
---

# Fase 05 — Integration Playbook

Receitas prontas para integrações do stack IntelliX. **Arquitetura nativa primeiro** —
o sistema deve ser capaz de operar integralmente sem dependências externas de automação.
n8n e outras ferramentas de orquestração são camadas complementares, não obrigatórias.

---

## Princípio: Nativo vs Orquestrado

```
PADRÃO (preferir sempre):
  Next.js → SDK/REST nativo → Serviço externo
  Vantagens: sem SPOF, latência menor, debug mais fácil, menos custo

COMPLEMENTAR (usar quando fluxo é complexo):
  Next.js → evento/webhook → n8n → múltiplos serviços
  Quando usar: automações com 5+ passos, retry complexo, múltiplos canais, agendamentos
```

---

## Seção 1 — SDK de IA Nativo (Anthropic / OpenAI)

### Anthropic SDK (recomendado para IntelliX)

```bash
npm install @anthropic-ai/sdk
```

```typescript
// src/lib/ai/anthropic.ts
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY!,
})

// Completions simples
export async function generateResponse(
  prompt: string,
  systemPrompt?: string
): Promise<string> {
  const message = await anthropic.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    system: systemPrompt,
    messages: [{ role: 'user', content: prompt }],
  })

  const content = message.content[0]
  if (content.type !== 'text') throw new Error('Unexpected response type')
  return content.text
}

// Streaming para UX responsiva
export async function* streamResponse(
  prompt: string,
  systemPrompt?: string
): AsyncGenerator<string> {
  const stream = anthropic.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    system: systemPrompt,
    messages: [{ role: 'user', content: prompt }],
  })

  for await (const chunk of stream) {
    if (
      chunk.type === 'content_block_delta' &&
      chunk.delta.type === 'text_delta'
    ) {
      yield chunk.delta.text
    }
  }
}
```

```typescript
// src/app/api/ai/chat/route.ts — Streaming response para UI
import { streamResponse } from '@/lib/ai/anthropic'
import { createClient } from '@/lib/supabase/server'
import type { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  const supabase = createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return new Response('Unauthorized', { status: 401 })

  const { message, systemPrompt } = await req.json()

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of streamResponse(message, systemPrompt)) {
          controller.enqueue(encoder.encode(chunk))
        }
      } finally {
        controller.close()
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
      'Transfer-Encoding': 'chunked',
    },
  })
}
```

---

## Seção 2 — WhatsApp via Evolution API (Nativo)

### Receber mensagem (webhook)

```typescript
// src/app/api/webhook/whatsapp/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { normalizePhone } from '@/lib/utils/phone'
import { contactsService } from '@/services/contacts.service'

export async function POST(req: NextRequest) {
  const payload = await req.json()

  // Ignorar mensagens próprias e grupos
  if (payload.data?.key?.fromMe) return NextResponse.json({ ok: true })
  if (payload.data?.key?.remoteJid?.includes('@g.us')) return NextResponse.json({ ok: true })

  const phone = normalizePhone(payload.data.key.remoteJid)
  const message = payload.data.message?.conversation
    ?? payload.data.message?.extendedTextMessage?.text
    ?? ''

  if (!message) return NextResponse.json({ ok: true })

  // Processar mensagem nativamente
  // Ex: salvar no DB, acionar agente, etc.
  return NextResponse.json({ ok: true })
}
```

### Enviar mensagem

```typescript
// src/lib/whatsapp/evolution.ts
interface SendMessageParams {
  phone: string        // formato: 5581999990001 (sem + e sem espaços)
  text: string
  instanceName?: string
}

export async function sendWhatsAppMessage({ phone, text, instanceName }: SendMessageParams) {
  const instance = instanceName ?? process.env.EVOLUTION_INSTANCE_NAME!

  const response = await fetch(
    `${process.env.EVOLUTION_API_URL}/message/sendText/${instance}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': process.env.EVOLUTION_API_KEY!,
      },
      body: JSON.stringify({ number: phone, text }),
    }
  )

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Evolution API error ${response.status}: ${error}`)
  }

  return response.json()
}

// Normalizar telefone
// src/lib/utils/phone.ts
export function normalizePhone(raw: string): string {
  return raw
    .replace('@s.whatsapp.net', '')
    .replace(/\D/g, '')
}
```

---

## Seção 3 — Supabase Realtime (Notificações em Tempo Real)

```typescript
// src/hooks/use-realtime-contacts.ts
'use client'
import { useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useQueryClient } from '@tanstack/react-query'

export function useRealtimeContacts(userId: string) {
  const queryClient = useQueryClient()
  const supabase = createClient()

  useEffect(() => {
    const channel = supabase
      .channel('contacts-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'contacts',
          filter: `user_id=eq.${userId}`,
        },
        () => {
          // Invalidar cache TanStack Query para refetch automático
          queryClient.invalidateQueries({ queryKey: ['contacts'] })
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [userId, queryClient, supabase])
}
```

---

## Seção 4 — REST API Client Tipado (Genérico)

Para qualquer API externa que não tenha SDK oficial:

```typescript
// src/lib/http/client.ts
import { z } from 'zod'

interface FetchOptions extends RequestInit {
  timeout?: number
}

export async function typedFetch<T>(
  url: string,
  schema: z.ZodType<T>,
  options: FetchOptions = {}
): Promise<T> {
  const { timeout = 10000, ...fetchOptions } = options

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data = await response.json()
    return schema.parse(data)  // Valida e tipifica a resposta
  } finally {
    clearTimeout(timeoutId)
  }
}

// Uso:
// const contactSchema = z.object({ id: z.string(), name: z.string() })
// const contact = await typedFetch('https://api.example.com/contact/1', contactSchema)
```

---

## Seção 5 — Supabase Edge Functions

Para lógica que precisa rodar próxima ao banco ou em cron:

```typescript
// supabase/functions/send-notification/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const { userId, message } = await req.json()

  // Lógica da function...
  const { error } = await supabase
    .from('notifications')
    .insert({ user_id: userId, message })

  if (error) return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  return new Response(JSON.stringify({ ok: true }), { status: 200 })
})
```

```bash
# Deploy da edge function
supabase functions deploy send-notification --project-ref [ref]
```

---

## Seção 6 — n8n como Camada de Orquestração (Opcional)

Use n8n apenas quando o fluxo tem 3+ serviços encadeados, retry complexo,
agendamentos ou lógica que não faz sentido no código do sistema.

### Disparar workflow n8n a partir do Next.js

```typescript
// src/lib/n8n/trigger.ts
export async function triggerN8nWorkflow(
  workflowPath: string,
  payload: Record<string, unknown>
): Promise<void> {
  if (!process.env.N8N_WEBHOOK_URL) {
    // n8n é opcional — não quebrar se não configurado
    console.warn(`n8n not configured, skipping workflow: ${workflowPath}`)
    return
  }

  const url = `${process.env.N8N_WEBHOOK_URL}/${workflowPath}`
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    // Log mas não quebrar o fluxo principal
    console.error(`n8n trigger failed: ${workflowPath}`, response.status)
  }
}
```

### Quando usar n8n vs código nativo

| Cenário | Recomendação |
|---------|-------------|
| Enviar 1 mensagem WhatsApp | Código nativo (Seção 2) |
| Fluxo de onboarding: email + WhatsApp + CRM + aguardar 2 dias + follow-up | n8n |
| Buscar dados de uma API externa | Código nativo (Seção 4) |
| Sincronização diária com 5 sistemas externos | n8n |
| Notificação em tempo real | Supabase Realtime (Seção 3) |
| Pipeline de dados com transformações complexas | n8n |

---

## Variáveis de Ambiente

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...             # Se usar OpenAI

# WhatsApp
EVOLUTION_API_URL=https://api.sua-instancia.com
EVOLUTION_API_KEY=sua-chave-aqui
EVOLUTION_INSTANCE_NAME=nome-da-instancia

# n8n (opcional)
N8N_WEBHOOK_URL=https://n8n.sua-instancia.com/webhook

# Supabase (já configurado na Fase 01)
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # NUNCA expor no client
```

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Construir workflows n8n complexos | `n8n-workflow-patterns` |
| Código JavaScript em nodes n8n | `n8n-code-javascript` |
| Configurar nodes específicos do n8n | `n8n-node-configuration` |
| Validar expressões n8n | `n8n-expression-syntax` |
| Resolver erros de validação n8n | `n8n-validation-expert` |
| Agente nativo com Anthropic SDK | `SKILL_AI Agent Creator` |

---

## Armadilhas comuns
- ❌ `SUPABASE_SERVICE_ROLE_KEY` no client-side → vaza permissão total do banco
- ❌ Chamar Evolution API diretamente do componente → expõe API key no browser
- ❌ n8n como dependência obrigatória → sistema para se n8n cair
- ❌ Sem timeout em chamadas externas → request hanging por minutos
- ❌ Resposta de API externa sem validação Zod → crashes em produção por schema inesperado
