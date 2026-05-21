# Database Schema — Live Chat Support

Schema SQL completo para Supabase. Execute como migration.

## Tabela de conteúdos

1. [Extensions](#extensions)
2. [Enums](#enums)
3. [Tabela: channels](#channels) ← **NOVO: canais omnichannel**
4. [Tabela: agents](#agents)
5. [Tabela: conversations](#conversations)
6. [Tabela: messages](#messages)
7. [Tabela: handoff_requests](#handoff-requests)
8. [Tabela: conversation_assignments](#conversation-assignments)
9. [Tabela: ai_context](#ai-context)
10. [Tabela: canned_responses](#canned-responses)
11. [Tabela: knowledge_base](#knowledge-base)
12. [RLS Policies](#rls-policies)
13. [Triggers e Functions](#triggers-e-functions)
14. [Indexes](#indexes)

---

## Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

## Enums

```sql
CREATE TYPE conversation_status AS ENUM (
  'ai_active',
  'waiting_human',
  'human_active',
  'closed'
);

CREATE TYPE message_sender_type AS ENUM (
  'lead',
  'ai',
  'human_agent',
  'system'
);

CREATE TYPE handoff_status AS ENUM (
  'pending',
  'accepted',
  'expired',
  'cancelled'
);

CREATE TYPE agent_role AS ENUM (
  'agent',
  'supervisor',
  'admin'
);

CREATE TYPE channel_type AS ENUM (
  'webchat',
  'whatsapp',
  'instagram',
  'telegram',
  'custom'
);
```

## Channels

Canais omnichannel configurados. Cada row é uma instância de canal (ex: "WhatsApp Comercial", "Instagram @loja").

```sql
CREATE TABLE channels (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type channel_type NOT NULL,
  provider TEXT NOT NULL,          -- 'native', 'cloud_api', 'evolution', 'zapi', 'meta', 'bot_api', 'custom'
  name TEXT NOT NULL,              -- Nome amigável: "WhatsApp Comercial", "Instagram @minhaloja"
  config JSONB NOT NULL DEFAULT '{}',  -- Credenciais e configs específicas do provider
  -- IMPORTANTE: em produção, criptografar este campo com pgcrypto
  is_active BOOLEAN DEFAULT true,
  webhook_url TEXT,                -- URL do webhook configurado neste canal
  metadata JSONB DEFAULT '{}',     -- Dados extras (ex: phone number, username)
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(type, provider, name)
);

-- Seed: canal webchat (sempre disponível, sem credenciais externas)
INSERT INTO channels (type, provider, name, config) VALUES
  ('webchat', 'native', 'Chat do Site', '{}');
```

## Agents

```sql
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT, -- Número WhatsApp para notificações (formato: 5511999999999)
  telegram_id TEXT, -- Chat ID do Telegram pessoal (para notificações)
  role agent_role DEFAULT 'agent',
  avatar_url TEXT,
  is_online BOOLEAN DEFAULT false,
  max_concurrent_chats INTEGER DEFAULT 5,
  notification_channels TEXT[] DEFAULT '{browser}', 
  -- Canais para receber notificações de handoff: 'browser', 'whatsapp', 'telegram', 'email'
  -- Pode ter múltiplos: '{whatsapp,browser}'
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

## Conversations

```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- Canal de origem (omnichannel)
  channel_id UUID NOT NULL REFERENCES channels(id),
  channel_conversation_id TEXT NOT NULL, -- ID externo no canal (phone number, chat_id, session_id)
  
  -- Status e atribuição
  status conversation_status DEFAULT 'ai_active',
  current_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
  
  -- Dados do lead
  lead_name TEXT NOT NULL,
  lead_email TEXT,
  lead_phone TEXT,
  lead_session_id TEXT, -- Apenas para webchat (identificador da sessão do widget)
  
  -- Controle de inatividade
  human_inactive_since TIMESTAMPTZ,
  last_message_at TIMESTAMPTZ DEFAULT now(),
  
  -- Metadados
  metadata JSONB DEFAULT '{}',
  -- Exemplo: { "source": "website", "page": "/pricing", "utm_campaign": "...", "channel_type": "whatsapp" }
  
  -- Tags e organização
  tags TEXT[] DEFAULT '{}',
  priority INTEGER DEFAULT 0, -- 0=normal, 1=alta, 2=urgente
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  closed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_agent ON conversations(current_agent_id);
CREATE INDEX idx_conversations_channel ON conversations(channel_id);
CREATE INDEX idx_conversations_channel_ext ON conversations(channel_id, channel_conversation_id);
CREATE INDEX idx_conversations_lead_session ON conversations(lead_session_id);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at DESC);
```

## Messages

```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  
  -- Remetente
  sender_type message_sender_type NOT NULL,
  sender_id UUID, -- agent_id se human_agent, null se ai/system/lead
  sender_name TEXT NOT NULL,
  
  -- Conteúdo
  content TEXT NOT NULL,
  content_type TEXT DEFAULT 'text', -- 'text', 'image', 'file', 'audio'
  
  -- Metadados
  metadata JSONB DEFAULT '{}',
  -- Para IA: { "confidence": 0.85, "model": "gpt-4o", "tokens_used": 150 }
  -- Para arquivos: { "file_url": "...", "file_name": "...", "file_size": 1024 }
  -- Para sistema: { "event": "agent_joined", "agent_name": "Carlos" }
  
  -- Flags
  is_internal_note BOOLEAN DEFAULT false, -- Notas internas entre agentes
  is_read BOOLEAN DEFAULT false,
  
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_unread ON messages(conversation_id, is_read) WHERE is_read = false;
```

## Handoff Requests

```sql
CREATE TABLE handoff_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  
  -- Motivo e contexto
  reason TEXT NOT NULL,
  -- Ex: "lead_requested", "low_confidence", "negative_sentiment", "keyword_trigger"
  ai_summary TEXT, -- Resumo gerado pela IA do contexto da conversa
  trigger_details JSONB DEFAULT '{}',
  -- Ex: { "keyword": "cancelar", "confidence_score": 0.3 }
  
  -- Atribuição
  target_agent_id UUID REFERENCES agents(id), -- Agente específico ou null para qualquer um
  accepted_by UUID REFERENCES agents(id),
  
  -- Status
  status handoff_status DEFAULT 'pending',
  
  -- Notificações
  whatsapp_notified_at TIMESTAMPTZ,
  renotify_count INTEGER DEFAULT 0,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  accepted_at TIMESTAMPTZ,
  expired_at TIMESTAMPTZ
);

CREATE INDEX idx_handoff_status ON handoff_requests(status);
CREATE INDEX idx_handoff_conversation ON handoff_requests(conversation_id);
```

## Conversation Assignments

Histórico de quem atendeu cada conversa e quando.

```sql
CREATE TABLE conversation_assignments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  agent_id UUID REFERENCES agents(id), -- null se IA
  assignment_type TEXT NOT NULL, -- 'ai', 'human_manual', 'human_handoff', 'timeout_return'
  
  started_at TIMESTAMPTZ DEFAULT now(),
  ended_at TIMESTAMPTZ,
  
  -- Resumo do período
  summary TEXT, -- Resumo gerado pela IA ao encerrar o período
  messages_count INTEGER DEFAULT 0
);

CREATE INDEX idx_assignments_conversation ON conversation_assignments(conversation_id, started_at DESC);
```

## AI Context

Contexto acumulado para o agente de IA. Atualizado a cada transição.

```sql
CREATE TABLE ai_context (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  
  -- Resumo cumulativo
  running_summary TEXT, -- Resumo que vai sendo atualizado a cada interação
  
  -- Dados coletados do lead
  collected_data JSONB DEFAULT '{}',
  -- Ex: { "interesse": "plano empresarial", "orcamento": "R$500/mês", "empresa": "TechCorp" }
  
  -- Handoff context
  last_handoff_summary TEXT, -- Resumo do último atendimento humano
  
  -- Configuração
  system_prompt_override TEXT, -- Override do system prompt para este lead específico
  
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(conversation_id)
);
```

## Canned Responses

Respostas rápidas configuráveis pelos agentes.

```sql
CREATE TABLE canned_responses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  shortcut TEXT NOT NULL UNIQUE, -- Ex: "/obrigado", "/horario", "/preco"
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  category TEXT DEFAULT 'geral',
  created_by UUID REFERENCES agents(id),
  is_global BOOLEAN DEFAULT true, -- true = todos os agentes podem usar
  created_at TIMESTAMPTZ DEFAULT now()
);
```

## Knowledge Base

Base de conhecimento para RAG do agente de IA.

```sql
CREATE TABLE knowledge_base (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  category TEXT DEFAULT 'geral',
  embedding VECTOR(1536), -- Para busca semântica (requer pgvector)
  metadata JSONB DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Habilitar pgvector se usar RAG
-- CREATE EXTENSION IF NOT EXISTS vector;
-- CREATE INDEX idx_kb_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

## RLS Policies

```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE handoff_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_context ENABLE ROW LEVEL SECURITY;
ALTER TABLE canned_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;

-- Channels: leitura para agentes autenticados, escrita apenas admin
CREATE POLICY "channels_select" ON channels FOR SELECT USING (
  EXISTS (SELECT 1 FROM agents WHERE user_id = auth.uid())
);
CREATE POLICY "channels_admin" ON channels FOR ALL USING (
  EXISTS (SELECT 1 FROM agents WHERE user_id = auth.uid() AND role = 'admin')
);

-- Agents: podem ver outros agentes, editar apenas a si mesmos
CREATE POLICY "agents_select" ON agents FOR SELECT USING (true);
CREATE POLICY "agents_update_self" ON agents FOR UPDATE USING (
  auth.uid() = user_id
);

-- Conversations: agentes autenticados podem ver todas; leads só as suas (via session_id)
CREATE POLICY "conversations_agents" ON conversations FOR ALL USING (
  EXISTS (SELECT 1 FROM agents WHERE user_id = auth.uid())
);
CREATE POLICY "conversations_leads" ON conversations FOR SELECT USING (
  lead_session_id = current_setting('app.lead_session_id', true)
);

-- Messages: agentes veem todas; leads veem apenas da sua conversa (exceto notas internas)
CREATE POLICY "messages_agents" ON messages FOR ALL USING (
  EXISTS (SELECT 1 FROM agents WHERE user_id = auth.uid())
);
CREATE POLICY "messages_leads" ON messages FOR SELECT USING (
  conversation_id IN (
    SELECT id FROM conversations 
    WHERE lead_session_id = current_setting('app.lead_session_id', true)
  )
  AND is_internal_note = false
);
CREATE POLICY "messages_leads_insert" ON messages FOR INSERT WITH CHECK (
  sender_type = 'lead'
  AND conversation_id IN (
    SELECT id FROM conversations 
    WHERE lead_session_id = current_setting('app.lead_session_id', true)
  )
);

-- Handoff requests: apenas agentes
CREATE POLICY "handoff_agents" ON handoff_requests FOR ALL USING (
  EXISTS (SELECT 1 FROM agents WHERE user_id = auth.uid())
);

-- Canned responses: agentes podem ler globais ou as suas
CREATE POLICY "canned_select" ON canned_responses FOR SELECT USING (
  is_global = true 
  OR created_by IN (SELECT id FROM agents WHERE user_id = auth.uid())
);

-- Knowledge base: leitura pública (para IA), escrita apenas admin
CREATE POLICY "kb_select" ON knowledge_base FOR SELECT USING (is_active = true);
CREATE POLICY "kb_admin" ON knowledge_base FOR ALL USING (
  EXISTS (SELECT 1 FROM agents WHERE user_id = auth.uid() AND role = 'admin')
);
```

## Triggers e Functions

### Atualizar `updated_at` automaticamente

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversations_updated_at
  BEFORE UPDATE ON conversations
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER agents_updated_at
  BEFORE UPDATE ON agents
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Atualizar `last_message_at` na conversa ao inserir mensagem

```sql
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE conversations 
  SET last_message_at = NEW.created_at,
      updated_at = now()
  WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER messages_update_conversation
  AFTER INSERT ON messages
  FOR EACH ROW EXECUTE FUNCTION update_conversation_last_message();
```

### Resetar timer de inatividade quando humano envia mensagem

```sql
CREATE OR REPLACE FUNCTION reset_human_inactivity()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.sender_type = 'human_agent' THEN
    UPDATE conversations 
    SET human_inactive_since = now()
    WHERE id = NEW.conversation_id 
      AND status = 'human_active';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER messages_reset_inactivity
  AFTER INSERT ON messages
  FOR EACH ROW EXECUTE FUNCTION reset_human_inactivity();
```

### Iniciar timer quando humano assume conversa

```sql
CREATE OR REPLACE FUNCTION on_conversation_status_change()
RETURNS TRIGGER AS $$
BEGIN
  -- Quando humano assume: iniciar timer
  IF NEW.status = 'human_active' AND OLD.status != 'human_active' THEN
    NEW.human_inactive_since = now();
  END IF;
  
  -- Quando sai do human_active: limpar timer
  IF NEW.status != 'human_active' AND OLD.status = 'human_active' THEN
    NEW.human_inactive_since = NULL;
  END IF;
  
  -- Quando fecha: registrar timestamp
  IF NEW.status = 'closed' AND OLD.status != 'closed' THEN
    NEW.closed_at = now();
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversations_status_change
  BEFORE UPDATE OF status ON conversations
  FOR EACH ROW EXECUTE FUNCTION on_conversation_status_change();
```

## Indexes

```sql
-- Performance para o Timeout Watcher
CREATE INDEX idx_conversations_human_active_timeout 
  ON conversations(human_inactive_since) 
  WHERE status = 'human_active' AND human_inactive_since IS NOT NULL;

-- Performance para listagem no painel do agente
CREATE INDEX idx_conversations_status_updated 
  ON conversations(status, updated_at DESC);

-- Performance para busca de mensagens
CREATE INDEX idx_messages_created 
  ON messages(conversation_id, created_at DESC);

-- Full-text search em mensagens (opcional)
CREATE INDEX idx_messages_content_search 
  ON messages USING gin(to_tsvector('portuguese', content));
```
