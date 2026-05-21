# Agente de IA — Especificação

Lógica completa do agente de IA que faz o primeiro atendimento e retoma após handoff.

## Tabela de conteúdos

1. [Arquitetura](#arquitetura)
2. [System prompt](#system-prompt)
3. [Construção de contexto](#construção-de-contexto)
4. [Detecção de handoff](#detecção-de-handoff)
5. [Coleta de dados](#coleta-de-dados)
6. [RAG com knowledge base](#rag-com-knowledge-base)
7. [Retomada pós-handoff](#retomada-pós-handoff)
8. [Fallback entre LLMs](#fallback-entre-llms)
9. [Rate limiting e custos](#rate-limiting-e-custos)

---

## Arquitetura

```
Lead envia mensagem
       │
       ▼
┌──────────────┐
│ Verificar    │ → Se conversation.status != 'ai_active' → não processar
│ status       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Construir    │ → System prompt + contexto + últimas N mensagens
│ contexto     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Buscar RAG   │ → Se knowledge_base configurada, buscar docs relevantes
│ (opcional)   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Chamar LLM   │ → OpenAI ou Anthropic via API
│              │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Analisar     │ → Verificar se precisa de handoff
│ resposta     │ → Extrair dados do lead
└──────┬───────┘
       │
       ├─── Handoff necessário? → Iniciar Fluxo 1
       │
       ▼
┌──────────────┐
│ Enviar       │ → Salvar mensagem + adapter.formatText() + adapter.sendMessage()
│ resposta     │   (resposta formatada e enviada pelo canal de origem)
└──────────────┘
```

## System prompt

O system prompt é composto por camadas:

### Camada 1: Base (configurável no .env)
```
Você é o assistente virtual de atendimento da {EMPRESA}. 

Regras fundamentais:
1. Seja cordial, objetivo e helpful. Use um tom profissional mas acessível.
2. SEMPRE tente ajudar antes de transferir para um humano.
3. Se não souber a resposta, admita e ofereça transferir para um atendente.
4. Colete dados do lead naturalmente durante a conversa (nome, email, telefone, empresa, interesse).
5. NUNCA invente informações sobre produtos, preços ou políticas.
6. Use a base de conhecimento fornecida como fonte primária de informação.
7. Responda SEMPRE em português brasileiro.
8. Mantenha respostas concisas (máx 3 parágrafos por mensagem).
```

### Camada 2: Contexto da conversa (dinâmico)
```
Contexto atual da conversa:
- Lead: {lead_name} ({lead_email})
- Conversa iniciada há: {tempo}
- Resumo do que já foi tratado: {running_summary}
- Dados coletados: {collected_data}

{Se houver last_handoff_summary:}
Nota: O lead acabou de ser atendido pelo humano {agent_name}. 
Resumo do atendimento humano: {last_handoff_summary}
Retome a conversa de forma natural, mencionando brevemente o que foi tratado.
```

### Camada 3: Knowledge base (dinâmico)
```
Informações relevantes da base de conhecimento:
---
{rag_results}
---
Use essas informações para responder. Se a pergunta não for coberta pela base, 
informe que vai verificar e ofereça transferir para um atendente.
```

### Camada 4: Instruções de handoff
```
Gatilhos para transferir para atendente humano — execute o handoff quando:
1. O lead pedir EXPLICITAMENTE para falar com humano
2. Você não souber responder após 2 tentativas
3. O lead demonstrar frustração ou insatisfação
4. O assunto envolver: financeiro, jurídico, reclamação, cancelamento
5. As seguintes palavras-chave aparecerem: {configured_keywords}

Quando precisar transferir, responda EXATAMENTE no formato:
[HANDOFF_REQUIRED]
Motivo: {motivo}
Resumo: {resumo da conversa até aqui}

IMPORTANTE: A tag [HANDOFF_REQUIRED] deve estar na sua resposta para 
que o sistema detecte e execute a transferência.
```

### Camada 5: Formatação por canal (dinâmico)
```
CANAL ATUAL: {channel_type}

Adapte suas respostas ao canal:
- Se WEBCHAT: pode usar respostas mais longas (até 3 parágrafos), formatação rica (negrito, listas).
- Se WHATSAPP: respostas CURTAS (máx 2 parágrafos). Use *asteriscos* para negrito. Evite listas longas. Quebre em mensagens menores se necessário.
- Se INSTAGRAM: respostas MUITO CURTAS (máx 1 parágrafo). Tom informal e direto. Sem formatação especial (Instagram não renderiza markdown).
- Se TELEGRAM: respostas médias. Pode usar *negrito*, _itálico_ e [links](url) em Markdown.

LIMITE DE CARACTERES: {max_message_length} caracteres. Se sua resposta exceder, quebre em partes lógicas.
```

## Construção de contexto

```typescript
async function buildContext(conversationId: string): Promise<LLMMessage[]> {
  // 1. Buscar contexto salvo
  const aiContext = await getAiContext(conversationId);
  
  // 2. Buscar últimas N mensagens
  const messages = await supabase
    .from('messages')
    .select('*')
    .eq('conversation_id', conversationId)
    .eq('is_internal_note', false) // Nunca incluir notas internas
    .order('created_at', { ascending: true })
    .limit(parseInt(process.env.AI_MAX_CONTEXT_MESSAGES || '50'));
  
  // 3. Buscar dados da conversa + canal
  const conversation = await getConversation(conversationId);
  const channel = await getChannelById(conversation.channel_id);
  const adapter = channelRegistry.getAdapter(channel);
  
  // 4. Se necessário, buscar RAG
  const lastUserMessage = messages.data?.filter(m => m.sender_type === 'lead').pop();
  let ragContext = '';
  if (lastUserMessage) {
    ragContext = await searchKnowledgeBase(lastUserMessage.content);
  }
  
  // 5. Montar system prompt completo (incluindo canal)
  const systemPrompt = buildSystemPrompt({
    basePrompt: process.env.AI_SYSTEM_PROMPT,
    leadName: conversation.lead_name,
    leadEmail: conversation.lead_email,
    runningSummary: aiContext?.running_summary,
    lastHandoffSummary: aiContext?.last_handoff_summary,
    collectedData: aiContext?.collected_data,
    ragResults: ragContext,
    handoffKeywords: await getConfiguredKeywords(),
    // Omnichannel: informações do canal
    channelType: channel.type,
    maxMessageLength: adapter.capabilities.maxMessageLength,
  });
  
  // 6. Converter mensagens para formato LLM
  const llmMessages: LLMMessage[] = [
    { role: 'system', content: systemPrompt },
    ...messages.data.map(m => ({
      role: m.sender_type === 'lead' ? 'user' : 'assistant',
      content: m.sender_type === 'system' 
        ? `[Sistema: ${m.content}]` 
        : m.content
    }))
  ];
  
  return llmMessages;
}
```

**Importante sobre notas internas:** NUNCA incluir mensagens com `is_internal_note = true` no contexto do LLM. Essas notas são entre agentes humanos e contêm informações confidenciais que o lead não deve saber que existem, nem indiretamente.

## Detecção de handoff

### Método 1: Tag na resposta do LLM
O system prompt instrui o LLM a incluir `[HANDOFF_REQUIRED]` quando necessário.

```typescript
function detectHandoffInResponse(response: string): HandoffDetection | null {
  if (response.includes('[HANDOFF_REQUIRED]')) {
    const reasonMatch = response.match(/Motivo: (.+)/);
    const summaryMatch = response.match(/Resumo: (.+)/);
    
    // Remover a tag e metadados da resposta visível ao lead
    const cleanResponse = response
      .replace(/\[HANDOFF_REQUIRED\][\s\S]*$/, '')
      .trim();
    
    return {
      needed: true,
      reason: reasonMatch?.[1] || 'ai_detected',
      summary: summaryMatch?.[1] || '',
      cleanResponse
    };
  }
  return null;
}
```

### Método 2: Análise pós-resposta
Após a resposta, analisar a confiança:

```typescript
// Se o LLM responder com hedging/incerteza, contar como baixa confiança
const LOW_CONFIDENCE_PATTERNS = [
  /não tenho certeza/i,
  /não posso confirmar/i,
  /sugiro que (fale|converse) com/i,
  /seria melhor (falar|conversar) com/i,
  /preciso verificar/i,
  /não tenho acesso a essa informação/i,
];

function analyzeConfidence(response: string): number {
  const matches = LOW_CONFIDENCE_PATTERNS.filter(p => p.test(response));
  return matches.length > 0 ? 0.3 : 0.9;
}
```

### Método 3: Solicitação explícita do lead
```typescript
const HANDOFF_KEYWORDS = [
  /falar com (alguém|humano|atendente|pessoa)/i,
  /me transfere/i,
  /quero um atendente/i,
  /cadê o (atendente|humano)/i,
  /chama (alguém|gerente|supervisor)/i,
];

function detectExplicitHandoffRequest(message: string): boolean {
  return HANDOFF_KEYWORDS.some(pattern => pattern.test(message));
}
```

**Prioridade de detecção:**
1. Solicitação explícita do lead → handoff imediato
2. Tag do LLM na resposta → handoff após enviar msg de transição
3. Baixa confiança em 2+ respostas consecutivas → handoff
4. Palavras-chave configuráveis → handoff

## Coleta de dados

A IA deve extrair dados do lead naturalmente durante a conversa.

```typescript
async function extractLeadData(
  messages: Message[], 
  currentData: Record<string, any>
): Promise<Record<string, any>> {
  const extractionPrompt = `
    Analise as mensagens abaixo e extraia dados do lead.
    Dados já coletados: ${JSON.stringify(currentData)}
    
    Extraia APENAS o que o lead mencionou explicitamente:
    - nome, email, telefone, empresa, cargo, interesse, orçamento
    
    Retorne APENAS JSON válido. Se não encontrar novos dados, retorne {}.
    
    Mensagens:
    ${messages.map(m => `${m.sender_name}: ${m.content}`).join('\n')}
  `;
  
  const result = await callLLM(extractionPrompt, { json_mode: true });
  return { ...currentData, ...JSON.parse(result) };
}
```

Executar extração a cada 5 mensagens (não a cada mensagem para economia de tokens).
Salvar em `ai_context.collected_data` e `conversations.metadata`.

## RAG com knowledge base

### Busca semântica (com pgvector)
```typescript
async function searchKnowledgeBase(query: string): Promise<string> {
  // 1. Gerar embedding da query
  const embedding = await generateEmbedding(query);
  
  // 2. Buscar documentos similares
  const { data } = await supabase.rpc('match_knowledge_base', {
    query_embedding: embedding,
    match_threshold: 0.7,
    match_count: 3
  });
  
  if (!data?.length) return '';
  
  return data.map(d => `[${d.title}]\n${d.content}`).join('\n\n---\n\n');
}
```

### Busca por texto (sem pgvector)
```typescript
async function searchKnowledgeBaseText(query: string): Promise<string> {
  const { data } = await supabase
    .from('knowledge_base')
    .select('title, content')
    .textSearch('content', query, { type: 'websearch', config: 'portuguese' })
    .eq('is_active', true)
    .limit(3);
  
  if (!data?.length) return '';
  
  return data.map(d => `[${d.title}]\n${d.content}`).join('\n\n---\n\n');
}
```

## Retomada pós-handoff

Quando a IA retoma após atendimento humano:

```typescript
async function resumeAfterHandoff(conversationId: string) {
  const context = await getAiContext(conversationId);
  const conversation = await getConversation(conversationId);
  
  // Gerar mensagem de retomada personalizada
  const resumptionPrompt = `
    Você é o assistente virtual. O atendente humano acabou de encerrar o atendimento.
    
    Lead: ${conversation.lead_name}
    Resumo do atendimento humano: ${context.last_handoff_summary}
    Contexto geral: ${context.running_summary}
    
    Gere uma mensagem CURTA (máx 2 frases) retomando a conversa:
    1. Cumprimente o lead pelo nome
    2. Mencione brevemente o que foi tratado com o humano
    3. Pergunte se pode ajudar com mais alguma coisa
    
    Seja natural e cordial. NÃO repita informações já discutidas.
  `;
  
  const message = await callLLM(resumptionPrompt);
  
  // Enviar como mensagem da IA
  await sendAiMessage(conversationId, message);
}
```

## Fallback entre LLMs

```typescript
async function callLLM(
  messages: LLMMessage[], 
  options?: { json_mode?: boolean }
): Promise<string> {
  const provider = process.env.LLM_PROVIDER;
  
  try {
    if (provider === 'openai') {
      return await callOpenAI(messages, options);
    } else if (provider === 'anthropic') {
      return await callAnthropic(messages, options);
    }
  } catch (error) {
    // Fallback: tentar o outro provider se o principal falhar
    console.error(`Primary LLM (${provider}) failed:`, error);
    
    try {
      if (provider === 'openai') {
        return await callAnthropic(messages, options);
      } else {
        return await callOpenAI(messages, options);
      }
    } catch (fallbackError) {
      // Ambos falharam: resposta de emergência
      console.error('Both LLMs failed:', fallbackError);
      return 'Desculpe, estou com uma dificuldade técnica no momento. ' +
             'Vou transferir você para um de nossos atendentes.';
      // + iniciar handoff automático
    }
  }
}
```

**Importante:** Se ambos os LLMs falharem, SEMPRE iniciar handoff automático para humano.
Nunca deixar o lead sem resposta.

## Rate limiting e custos

**Throttle de chamadas LLM:**
- Máximo 1 chamada por segundo por conversa
- Se lead envia múltiplas mensagens rápidas, aguardar 2s e processar batch
- Debounce de 1s no input do lead antes de processar

**Estimativa de custos (GPT-4o como referência):**
- Média de 50 mensagens de contexto = ~2000 tokens input
- Resposta média = ~200 tokens output
- System prompt + RAG = ~1500 tokens
- **Total por resposta: ~3700 tokens ≈ $0.02 USD**
- Para 1000 conversas/mês com 10 msgs cada: **~$200 USD/mês**

**Otimizações:**
- Usar modelo menor (gpt-4o-mini) para tarefas simples (extração de dados, classificação)
- Cachear respostas do RAG para perguntas frequentes
- Comprimir contexto: usar resumo em vez de todas as mensagens quando > 30 msgs
- Executar extração de dados a cada 5 msgs, não a cada msg
