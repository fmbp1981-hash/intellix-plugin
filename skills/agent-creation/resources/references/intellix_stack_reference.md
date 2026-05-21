# IntelliX Stack Reference

Reference document for the common technology stack used in IntelliX.AI agent implementations. This is NOT a mandatory stack — the blueprint schema is stack-agnostic. This reference helps the skill generate more specific blueprints when the user indicates they use these technologies.

---

## Core Stack

| Layer | Default Technology | Alternatives |
|---|---|---|
| Database | Supabase (PostgreSQL 15+) | Firebase, PlanetScale, Neon, custom Postgres |
| Vector Store | Supabase pgvector | Pinecone, Qdrant, Weaviate, ChromaDB |
| Edge Functions | Supabase Edge Functions (Deno) | Vercel Serverless, AWS Lambda, Cloudflare Workers |
| Frontend | Next.js 15+ (App Router) | Remix, Nuxt, SvelteKit |
| Styling | Tailwind CSS + Shadcn/UI | Chakra UI, MUI, custom CSS |
| Animations | Framer Motion | GSAP, CSS animations |
| State | TanStack Query v5 + Zustand | SWR, Redux, Jotai |
| AI SDK | Vercel AI SDK v6 | LangChain, LlamaIndex, custom |
| Deploy | Vercel | Netlify, Railway, Fly.io |
| Automation | n8n (self-hosted) | Make, Zapier, Temporal |
| WhatsApp | Evolution API | Cloud API (Meta), Z-API, WPPConnect |

---

## Supabase Patterns

### Multi-tenancy
All tables include `organization_id` column with RLS policies:
```sql
-- Standard RLS pattern
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation" ON table_name
  USING (organization_id = auth.jwt()->>'org_id');
```

### Real-time
Use Supabase Realtime for live updates (chat messages, status changes):
```sql
-- Enable realtime on a table
ALTER PUBLICATION supabase_realtime ADD TABLE messages;
```

### Edge Functions
Agent engines run as Edge Functions:
- Receive webhook → process → respond
- Direct database access (same infrastructure)
- Deno runtime with TypeScript
- Cold start: ~50ms, execution: depends on LLM call

### pgvector for RAG
```sql
-- Create embedding column
ALTER TABLE knowledge_documents ADD COLUMN embedding vector(1536);

-- Create index for fast similarity search
CREATE INDEX ON knowledge_documents
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Match function
CREATE FUNCTION match_documents(
  query_embedding vector(1536),
  match_threshold float,
  match_count int
) RETURNS TABLE (id uuid, content text, similarity float)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT id, content, 1 - (embedding <=> query_embedding) AS similarity
  FROM knowledge_documents
  WHERE 1 - (embedding <=> query_embedding) > match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

---

## Evolution API Patterns

### Webhook Setup
Evolution API sends one webhook per instance. Configure webhook to receive all events:
```
POST /webhook/set/{instance}
{
  "url": "https://your-domain.com/webhooks/whatsapp/incoming",
  "events": ["messages.upsert", "connection.update", "messages.update"]
}
```

### Send Text Message
```
POST /message/sendText/{instance}
{
  "number": "5511999999999",
  "text": "Hello!"
}
```

### Send Media
```
POST /message/sendMedia/{instance}
{
  "number": "5511999999999",
  "mediatype": "image",
  "media": "https://example.com/photo.jpg",
  "caption": "Property photo"
}
```

### Important Limitations
- One webhook URL per instance (use a router/dispatcher if multiple consumers)
- Rate limit: ~60 messages/minute (varies by WhatsApp number quality)
- Media: max 16MB per file
- Template messages required for first contact (24h window rule)

---

## n8n Patterns

### Webhook Trigger
n8n exposes webhook URLs for external triggers:
```
https://n8n.yourdomain.com/webhook/{webhook-id}
```

### Common Agent-Related Workflows
- **Lead notification**: Agent scores lead → webhook to n8n → Slack/email notification
- **Data enrichment**: n8n receives contact data → enriches via external APIs → updates Supabase
- **Scheduled follow-ups**: n8n cron → queries Supabase for pending follow-ups → triggers agent
- **Multi-channel routing**: n8n receives from multiple sources → normalizes → routes to agent

### MCP Server
n8n can expose an MCP server for AI agent integration:
```
https://n8n.yourdomain.com/mcp-server/http
```

---

## Vercel AI SDK Patterns

### Tool Calling (Agent Pattern)
```typescript
import { generateText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';

const result = await generateText({
  model: anthropic('claude-sonnet-4-20250514'),
  tools: {
    searchPatient: {
      description: 'Search patient by phone number',
      parameters: z.object({ phone: z.string() }),
      execute: async ({ phone }) => {
        // Direct Supabase query
        return await supabase.from('patients').select('*').eq('phone', phone);
      }
    },
    bookAppointment: {
      description: 'Book an appointment',
      parameters: z.object({ slotId: z.string(), patientId: z.string() }),
      execute: async ({ slotId, patientId }) => {
        return await supabase.from('appointments').insert({ slot_id: slotId, patient_id: patientId });
      }
    }
  },
  maxSteps: 5, // max tool-calling iterations
  system: agentSystemPrompt,
  messages: conversationHistory
});
```

### Streaming Response
```typescript
import { streamText } from 'ai';

const result = streamText({
  model: anthropic('claude-sonnet-4-20250514'),
  system: agentSystemPrompt,
  messages: conversationHistory
});

// Stream to client
return result.toDataStreamResponse();
```

---

## Common Database Schemas

### Contacts (CRM-agnostic)
```sql
CREATE TABLE contacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id),
  name text NOT NULL,
  phone text,
  email text,
  source text, -- whatsapp, website, referral, manual
  status text DEFAULT 'active',
  metadata jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);
CREATE INDEX idx_contacts_org_phone ON contacts(organization_id, phone);
```

### Conversations
```sql
CREATE TABLE conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL,
  contact_id uuid REFERENCES contacts(id),
  channel text NOT NULL, -- whatsapp, email, system_chat
  status text DEFAULT 'active', -- active, human_active, resolved, abandoned
  assigned_to text DEFAULT 'ai', -- ai, human, agent_name
  summary text,
  intent text,
  sentiment text,
  last_message_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);
```

### Messages
```sql
CREATE TABLE messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id),
  role text NOT NULL, -- user, assistant, system
  content text NOT NULL,
  agent_name text, -- which agent sent this (for multi-agent)
  metadata jsonb DEFAULT '{}', -- tool calls, reasoning, etc.
  created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_messages_conv ON messages(conversation_id, created_at);
```

### Agent Audit Logs
```sql
CREATE TABLE agent_audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL,
  agent_name text NOT NULL,
  session_id text,
  action text NOT NULL, -- tool_call, reasoning, handoff, escalation, error
  details jsonb NOT NULL,
  tokens_used integer,
  cost_usd numeric(10,6),
  duration_ms integer,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_audit_org_agent ON agent_audit_logs(organization_id, agent_name, created_at);
```

---

## Notes on Stack Agnosticism

The blueprint schema uses these abstraction patterns to remain stack-agnostic:

1. **config_ref**: Instead of hardcoding `supabase_url`, tools reference `cfg_supabase` which is a pending_configuration. The implementer fills it with whatever database they use.

2. **source_type**: Context sources use generic types (`database`, `api`, `rag_knowledge_base`) not specific products (`supabase`, `pinecone`).

3. **tool_type**: Tools use generic types (`api_call`, `database_query`) not framework-specific types (`supabase_rpc`, `prisma_query`).

4. **runtime_environment**: A descriptive string, not an enum. Can be any runtime.

5. **provider fields**: Channel providers (WhatsApp, email, voice) are strings, not enums. Any provider works.

When the user indicates their specific stack during agent creation, the skill generates more specific configurations (e.g. Supabase query templates, Evolution API endpoints). When the stack is unknown, the skill generates generic configurations with clear pending_configuration items for the implementer to fill.
