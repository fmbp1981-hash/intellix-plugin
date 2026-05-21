# Handoff Flow Spec — Live Chat Support

Especificação detalhada de todas as transições de estado e fluxos de handoff do sistema.

## Tabela de conteúdos

1. [Máquina de estados](#máquina-de-estados)
2. [Fluxo 1: IA → Aguardando Humano](#fluxo-1-ia--aguardando-humano)
3. [Fluxo 2: Aguardando → Humano assume](#fluxo-2-aguardando--humano-assume)
4. [Fluxo 3: Humano → IA (manual)](#fluxo-3-humano--ia-manual)
5. [Fluxo 4: Humano → IA (timeout)](#fluxo-4-humano--ia-timeout)
6. [Fluxo 5: Aguardando → IA retoma (expiração)](#fluxo-5-aguardando--ia-retoma-expiração)
7. [Fluxo 6: Fechamento](#fluxo-6-fechamento)
8. [Geração de resumo contextual](#geração-de-resumo-contextual)
9. [Notificações WhatsApp](#notificações-whatsapp)
10. [Configurações de timeout](#configurações-de-timeout)

---

## Máquina de estados

```
                    ┌──────────────┐
          ┌────────>│  ai_active   │<────────┐
          │         └──────┬───────┘         │
          │                │                 │
          │    IA detecta handoff            │
          │                │                 │
          │         ┌──────▼───────┐         │
          │         │waiting_human │─────────┤
          │         └──────┬───────┘         │
          │                │                 │
          │    Humano assume                 │
          │                │                 │
          │         ┌──────▼───────┐         │
          │         │human_active  │─────────┘
          │         └──────┬───────┘
          │                │          ▲ Timeout (10 min)
          │                │          │ Manual "Devolver"
          │                │          │ Expiração (15 min)
          │         ┌──────▼───────┐
          └─────────│   closed     │
                    └──────────────┘
```

**Transições válidas:**
- `ai_active` → `waiting_human` (IA solicita handoff)
- `ai_active` → `closed` (lead encerra ou inatividade do lead)
- `waiting_human` → `human_active` (agente assume)
- `waiting_human` → `ai_active` (expiração: ninguém assumiu)
- `human_active` → `ai_active` (manual ou timeout)
- `human_active` → `closed` (agente encerra definitivamente)
- `closed` → `ai_active` (lead reabre conversa)

---

## Fluxo 1: IA → Aguardando Humano

**Gatilhos (qualquer um):**

| Gatilho | Detecção | Exemplo |
|---------|----------|---------|
| Solicitação explícita | Regex + NLU | "quero falar com alguém", "me transfere" |
| Baixa confiança | confidence < 0.5 em 2+ respostas | IA não sabe responder repetidamente |
| Sentimento negativo | Análise de sentimento via LLM | "isso é ridículo", "vocês não ajudam" |
| Palavra-chave | Lista configurável | "cancelar", "gerente", "processo", "advogado" |
| Tópico sensível | Classificação via LLM | Financeiro, jurídico, reclamação formal |

**Implementação:**

```typescript
async function initiateHandoff(
  conversationId: string,
  reason: string,
  triggerDetails: Record<string, any>
) {
  // 1. Gerar resumo da conversa via LLM
  const messages = await getConversationMessages(conversationId, 50);
  const summary = await generateSummary(messages);
  
  // 2. Atualizar status da conversa
  await supabase
    .from('conversations')
    .update({ status: 'waiting_human' })
    .eq('id', conversationId);
  
  // 3. Criar handoff request
  const { data: handoff } = await supabase
    .from('handoff_requests')
    .insert({
      conversation_id: conversationId,
      reason,
      ai_summary: summary,
      trigger_details: triggerDetails,
      target_agent_id: await findBestAgent(conversationId) // Round-robin ou por skill
    })
    .select()
    .single();
  
  // 4. Enviar mensagem de sistema ao lead
  await sendSystemMessage(conversationId, 
    'Estou transferindo você para um de nossos atendentes. Aguarde um momento.'
  );
  
  // 5. Salvar contexto da IA
  await upsertAiContext(conversationId, { running_summary: summary });
  
  // 6. Notificar agente(s) via canal(is) configurado(s) no perfil
  await notifyAvailableAgents(handoff);
  
  // 7. Registrar assignment
  await endCurrentAssignment(conversationId);
  
  return handoff;
}
```

**Seleção do agente (`findBestAgent`):**
1. Verificar se há agente online com capacidade disponível (`concurrent_chats < max`)
2. Priorizar agente que já atendeu este lead antes
3. Round-robin entre agentes disponíveis
4. Se nenhum disponível, `target_agent_id = null` (qualquer um pode assumir)

---

## Fluxo 2: Aguardando → Humano assume

**Ação do agente:** Clica "Assumir Atendimento" no painel.

```typescript
async function acceptHandoff(conversationId: string, agentId: string) {
  // 1. Verificar se conversa ainda está waiting
  const { data: conv } = await supabase
    .from('conversations')
    .select('status')
    .eq('id', conversationId)
    .single();
    
  if (conv.status !== 'waiting_human') {
    throw new Error('Conversa já foi assumida por outro agente');
  }
  
  // 2. Atualizar conversa
  await supabase
    .from('conversations')
    .update({ 
      status: 'human_active',
      current_agent_id: agentId
    })
    .eq('id', conversationId);
  
  // 3. Atualizar handoff request
  await supabase
    .from('handoff_requests')
    .update({ status: 'accepted', accepted_by: agentId, accepted_at: new Date() })
    .eq('conversation_id', conversationId)
    .eq('status', 'pending');
  
  // 4. Buscar nome do agente
  const agent = await getAgent(agentId);
  
  // 5. Enviar mensagem de sistema ao lead
  await sendSystemMessage(conversationId, 
    `O atendente **${agent.name}** entrou na conversa.`,
    { event: 'agent_joined', agent_name: agent.name, agent_id: agentId }
  );
  
  // 6. Registrar novo assignment
  await createAssignment(conversationId, agentId, 'human_handoff');
}
```

---

## Fluxo 3: Humano → IA (manual)

**Ação do agente:** Clica "Devolver para IA" no painel.

```typescript
async function returnToAi(conversationId: string, agentId: string) {
  // 1. Gerar resumo do atendimento humano
  const humanMessages = await getMessagesSinceLastHandoff(conversationId);
  const summary = await generateHandoffSummary(humanMessages);
  
  // 2. Atualizar conversa
  await supabase
    .from('conversations')
    .update({ 
      status: 'ai_active',
      current_agent_id: null,
      human_inactive_since: null
    })
    .eq('id', conversationId);
  
  // 3. Salvar resumo no contexto da IA
  await upsertAiContext(conversationId, { 
    last_handoff_summary: summary,
    running_summary: await mergeWithExistingSummary(conversationId, summary)
  });
  
  // 4. Buscar dados para mensagem de retomada
  const agent = await getAgent(agentId);
  const conv = await getConversation(conversationId);
  const context = await getAiContext(conversationId);
  
  // 5. Enviar mensagem de sistema
  await sendSystemMessage(conversationId, 
    `O atendente **${agent.name}** encerrou o atendimento.`,
    { event: 'agent_left', agent_name: agent.name }
  );
  
  // 6. IA retoma com contexto
  const resumptionMessage = await generateResumptionMessage(
    conv.lead_name,
    agent.name,
    context.last_handoff_summary
  );
  await sendAiMessage(conversationId, resumptionMessage);
  
  // 7. Encerrar assignment atual e iniciar novo (IA)
  await endCurrentAssignment(conversationId, summary);
  await createAssignment(conversationId, null, 'ai');
}
```

**Template da mensagem de retomada da IA:**
```
Olá, {lead_name}! Sou o assistente virtual. O atendente {agent_name} finalizou 
o atendimento. Vi que vocês conversaram sobre {resumo_do_atendimento}. 
Posso ajudar com mais alguma coisa?
```

---

## Fluxo 4: Humano → IA (timeout)

**Fluxo escalonado de inatividade do agente humano:**

| Tempo | % do timeout | Ação |
|-------|-------------|------|
| 0 min | 0% | Agente envia última mensagem. Timer inicia/reseta. |
| 8 min | 80% | Alerta visual pulsante no painel + som |
| 9 min | 90% | Notificação via canal preferido do agente (WhatsApp, Telegram, etc.) |
| 10 min | 100% | Handoff automático para IA |

**Implementação do Timeout Watcher (Edge Function):**

```typescript
// supabase/functions/timeout-watcher/index.ts
// Executar via cron a cada 1 minuto

import { createClient } from '@supabase/supabase-js';

const TIMEOUT_MINUTES = parseInt(Deno.env.get('HUMAN_INACTIVITY_TIMEOUT_MINUTES') || '10');
const WARNING_THRESHOLD = 0.8; // 80%
const CRITICAL_THRESHOLD = 0.9; // 90%

Deno.serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  );

  // Buscar conversas human_active com timer
  const { data: conversations } = await supabase
    .from('conversations')
    .select('*, agents!current_agent_id(*)')
    .eq('status', 'human_active')
    .not('human_inactive_since', 'is', null);

  for (const conv of conversations || []) {
    const inactiveSince = new Date(conv.human_inactive_since);
    const minutesInactive = (Date.now() - inactiveSince.getTime()) / 60000;
    const percentage = minutesInactive / TIMEOUT_MINUTES;

    if (percentage >= 1.0) {
      // TIMEOUT: devolver para IA
      await autoReturnToAi(supabase, conv);
    } else if (percentage >= CRITICAL_THRESHOLD) {
      // CRÍTICO: notificar via canal preferido do agente
      await sendTimeoutWarning(conv, TIMEOUT_MINUTES - minutesInactive);
    }
    // WARNING (80%): tratado no frontend via realtime
  }

  return new Response(JSON.stringify({ processed: conversations?.length || 0 }));
});
```

**Timer no frontend (complementar):**

```typescript
// hooks/useInactivityTimer.ts
function useInactivityTimer(conversation: Conversation) {
  const [minutesRemaining, setMinutesRemaining] = useState<number | null>(null);
  const [warningLevel, setWarningLevel] = useState<'none' | 'warning' | 'critical'>('none');

  useEffect(() => {
    if (conversation.status !== 'human_active' || !conversation.human_inactive_since) {
      setMinutesRemaining(null);
      setWarningLevel('none');
      return;
    }

    const interval = setInterval(() => {
      const elapsed = (Date.now() - new Date(conversation.human_inactive_since).getTime()) / 60000;
      const remaining = TIMEOUT_MINUTES - elapsed;
      setMinutesRemaining(Math.max(0, remaining));
      
      const pct = elapsed / TIMEOUT_MINUTES;
      if (pct >= 0.9) setWarningLevel('critical');
      else if (pct >= 0.8) setWarningLevel('warning');
      else setWarningLevel('none');
    }, 1000);

    return () => clearInterval(interval);
  }, [conversation.human_inactive_since, conversation.status]);

  return { minutesRemaining, warningLevel };
}
```

---

## Fluxo 5: Aguardando → IA retoma (expiração)

Quando ninguém assume o handoff dentro do tempo limite.

**Escalonamento:**

| Tempo | Ação |
|-------|------|
| 0 min | Handoff criado, primeira notificação enviada (canal do agente) |
| 5 min | Reenviar notificação (renotify) |
| 10 min | Segundo reenvio |
| 15 min | Expirar handoff, IA retoma |

```typescript
async function expireHandoff(conversationId: string) {
  // 1. Marcar handoff como expirado
  await supabase
    .from('handoff_requests')
    .update({ status: 'expired', expired_at: new Date() })
    .eq('conversation_id', conversationId)
    .eq('status', 'pending');
  
  // 2. Retornar para IA
  await supabase
    .from('conversations')
    .update({ status: 'ai_active' })
    .eq('id', conversationId);
  
  // 3. Informar o lead
  await sendSystemMessage(conversationId,
    'No momento todos os nossos atendentes estão ocupados. Vou continuar te ajudando!'
  );
  
  // 4. IA retoma normalmente
  await sendAiMessage(conversationId,
    'Desculpe pela espera! Enquanto nosso time não está disponível, posso continuar te ajudando. Em que posso ser útil?'
  );
}
```

---

## Fluxo 6: Fechamento

**Pelo agente humano:**
- Clica "Encerrar conversa"
- Status → `closed`
- Mensagem de sistema: "Atendimento encerrado por [Nome]. Obrigado pelo contato!"
- Se lead enviar nova mensagem, conversa reabre como `ai_active`

**Pelo lead:**
- Lead digita "encerrar" ou fecha o widget sem interação por 24h
- Edge Function fecha conversas inativas há 24h

**Pela IA:**
- Se lead confirma que não precisa de mais nada após 2 confirmações
- Envia pesquisa de satisfação (NPS/CSAT)

---

## Geração de resumo contextual

Toda transição entre IA e humano (e vice-versa) gera um resumo via LLM.

**Prompt para gerar resumo:**

```
Analise as mensagens abaixo e gere um resumo conciso (máx 3 frases) do que foi 
tratado, incluindo: (1) o que o lead quer/precisa, (2) o que já foi resolvido, 
(3) o que ainda está pendente.

Mensagens:
{messages}

Resumo:
```

**Prompt para mensagem de retomada da IA:**

```
Você é o assistente virtual de atendimento. O atendente humano {agent_name} 
acabou de encerrar o atendimento com o lead {lead_name}. 

Resumo do que foi tratado durante o atendimento humano:
{handoff_summary}

Contexto geral acumulado da conversa:
{running_summary}

Gere uma mensagem curta e natural retomando a conversa. Mencione brevemente 
o que foi tratado e pergunte se pode ajudar com mais alguma coisa. 
Seja cordial mas direto. Máximo 2 frases.
```

---

## Notificações para agentes

**Canal de notificação é configurável por agente.** O sistema usa a Channel Adapter Layer
para enviar notificações — o agente escolhe como quer ser notificado no perfil:

- `notification_channels: ['whatsapp']` → recebe via WhatsApp (qualquer provider configurado)
- `notification_channels: ['telegram']` → recebe via Telegram
- `notification_channels: ['browser']` → push notification no painel
- `notification_channels: ['whatsapp', 'browser']` → ambos

O sistema usa o `agent-notifier.ts` que consulta `agent.notification_channels` e
envia por cada canal usando o adapter correspondente. Ver `omnichannel-spec.md` seção
"Notificação de agentes via canal" para implementação completa.

**Throttle obrigatório:** Máximo 1 notificação por conversa a cada 5 minutos.

**Templates de notificação:**

### Novo handoff
```
🔔 *Novo atendimento aguardando*

Lead: {lead_name}
Motivo: {reason}
Assunto: {summary_excerpt}
Tempo esperando: {waiting_time}

📱 Acesse o painel: {panel_url}
```

### Renotificação
```
⏰ *Atendimento ainda aguardando*

Lead: {lead_name} está esperando há {waiting_time} minutos.
Motivo: {reason}

📱 Acesse: {panel_url}
```

### Warning de timeout
```
⚠️ *Atendimento inativo*

Seu atendimento com {lead_name} está inativo há {inactive_minutes} min.
Será devolvido à IA em {remaining_minutes} min.

📱 Acesse: {panel_url}
```

---

## Configurações de timeout

Todas configuráveis pelo admin no painel:

| Config | Padrão | Faixa | Descrição |
|--------|--------|-------|-----------|
| `HUMAN_INACTIVITY_TIMEOUT_MINUTES` | 10 | 5-30 | Tempo de inatividade para auto-retorno à IA |
| `HANDOFF_RENOTIFY_MINUTES` | 5 | 2-15 | Intervalo entre renotificações WhatsApp |
| `HANDOFF_EXPIRE_MINUTES` | 15 | 5-60 | Tempo para expirar handoff não aceito |
| `LEAD_INACTIVITY_CLOSE_HOURS` | 24 | 1-72 | Horas de inatividade do lead para fechar conversa |
| `WHATSAPP_THROTTLE_MINUTES` | 5 | 1-15 | Intervalo mínimo entre notificações WhatsApp |
| `WARNING_THRESHOLD_PCT` | 80 | 50-95 | % do timeout para alerta visual |
| `CRITICAL_THRESHOLD_PCT` | 90 | 80-99 | % do timeout para notificação WhatsApp |
