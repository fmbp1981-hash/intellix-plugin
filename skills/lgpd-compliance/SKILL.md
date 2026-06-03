---
name: lgpd-compliance
description: >
  Compliance LGPD e Privacy by Design para projetos IntelliX.
  Use SEMPRE que o projeto processar dados pessoais de pessoas físicas brasileiras —
  qualquer projeto com auth, CRM, formulários, agentes de IA ou logs de usuário.
  Invocada automaticamente pela Fase 06 (security-observability) em paralelo.
  Também ativa quando o usuário mencionar: LGPD, privacidade, dados pessoais,
  consentimento, titular, ANPD, proteção de dados, DPA, PII, CPF.
user-invocable: true
---

# LGPD Compliance & Privacy by Design — Padrão IntelliX

Lei 13.709/2018 | Res. CD/ANPD nº 2/2022 | Res. CD/ANPD nº 15/2024

> **Filosofia IntelliX:** "Pavimentar antes de proibir." O caminho conforme deve ser o
> caminho fácil — não mais uma checklist a ser pulada sob pressão de prazo.

---

## 0. Auto-Detecção — Aplicabilidade

```
O projeto coleta, armazena ou processa dados de pessoas físicas?
  → Nome, email, telefone, CPF, endereço, IP = dados pessoais
  → Saúde, biometria, religião, origem racial = dados SENSÍVEIS (regime duplo)
  → Comportamento, preferências, histórico de uso = dados pessoais indiretamente

SE NÃO: projeto fora do escopo LGPD — apenas Nível BÁSICO de security-observability
SE SIM (dados comuns): executar seções 1–7 abaixo
SE SIM (dados sensíveis): executar seções 1–7 + Seção 8 (regime reforçado)
```

---

## 1. Mapa de Dados — Fazer Antes de Qualquer Implementação

Para cada tabela com dados pessoais, responder:

| Pergunta | Resposta obrigatória |
|----------|---------------------|
| Quais dados pessoais são coletados? | [listar: nome, email, CPF, etc.] |
| Para qual finalidade específica? | [finalidade determinada e legítima] |
| Qual a base legal (Art. 7 LGPD)? | [V-Contrato / I-Consentimento / IX-Legítimo Interesse] |
| Por quanto tempo ficam retidos? | [definir em dias/anos] |
| Quem é o controlador? | [cliente ou IntelliX?] |
| IntelliX atua como operadora? | [Sim/Não — se Sim: DPA necessário] |

**Bases legais mais usadas nos projetos IntelliX:**

| Base Legal | Art. 7 | Quando usar |
|-----------|--------|-------------|
| Execução de contrato | V | CRM, sistemas de gestão, dados do cliente para prestar o serviço |
| Legítimo interesse | IX | Analytics, prevenção de fraude, melhoria do sistema |
| Consentimento | I | Newsletter, cookies não-essenciais, marketing |
| Cumprimento de obrigação legal | II | NFe, eSocial, dados fiscais |

> **Atenção — Dados Sensíveis (Art. 11):** saúde, biometria, origem racial/étnica,
> convicção religiosa, dado genético, vida sexual.
> Exigem CONSENTIMENTO ESPECÍFICO E DESTACADO ou hipóteses do Art. 11, II.
> Se o sistema processar dado sensível: Seção 8 obrigatória.

---

## 2. Tabelas Obrigatórias — Schema Supabase

Adicionar ao schema de qualquer projeto que processa dados pessoais:

```sql
-- supabase/migrations/[timestamp]_lgpd_tables.sql

-- Registro de consentimentos (quando base legal = consentimento)
CREATE TABLE consent_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  purpose TEXT NOT NULL,          -- 'marketing_email', 'analytics', 'cookies_tracking'
  granted BOOLEAN NOT NULL,
  granted_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  ip_address TEXT,
  user_agent TEXT,
  version TEXT NOT NULL DEFAULT '1.0', -- versão da política de privacidade
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Solicitações de direitos dos titulares (Art. 18)
CREATE TABLE titular_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  email TEXT NOT NULL,            -- para titular não autenticado também poder solicitar
  request_type TEXT NOT NULL CHECK (request_type IN (
    'access',           -- Art. 18, I-II: acesso aos dados
    'correction',       -- Art. 18, III: correção
    'deletion',         -- Art. 18, VI: eliminação
    'portability',      -- Art. 18, V: portabilidade
    'consent_revoke',   -- Art. 18, IX: revogação de consentimento
    'anonymization',    -- Art. 18, IV: anonimização/bloqueio
    'opposition',       -- Art. 18, II: oposição ao tratamento
    'automated_review'  -- Art. 20: revisão de decisão automatizada
  )),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
    'pending', 'in_progress', 'completed', 'rejected'
  )),
  description TEXT,
  response TEXT,
  deadline TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '15 days'), -- prazo LGPD
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Log de tratamento de dados (registro de operações sensíveis)
CREATE TABLE data_processing_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  operation TEXT NOT NULL,        -- 'read', 'write', 'delete', 'export', 'ai_processing'
  data_categories TEXT[] NOT NULL, -- ['name', 'email', 'cpf', 'health']
  purpose TEXT NOT NULL,
  legal_basis TEXT NOT NULL,
  automated BOOLEAN DEFAULT false, -- se foi decisão automatizada (Art. 20)
  ai_model TEXT,                  -- qual LLM processou estes dados
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS em todas
ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE titular_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_processing_log ENABLE ROW LEVEL SECURITY;

-- Titulares veem apenas seus dados
CREATE POLICY "titular_own_consents" ON consent_records
  FOR ALL USING (user_id = auth.uid());

CREATE POLICY "titular_own_requests" ON titular_requests
  FOR SELECT USING (user_id = auth.uid() OR email = auth.email());

CREATE POLICY "admin_read_requests" ON titular_requests
  FOR ALL USING (
    EXISTS (SELECT 1 FROM user_roles WHERE user_id = auth.uid() AND role = 'admin')
  );

-- Log: apenas admin lê, sistema escreve via service_role
CREATE POLICY "admin_read_processing_log" ON data_processing_log
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM user_roles WHERE user_id = auth.uid() AND role = 'admin')
  );
```

---

## 3. Os 9 Direitos dos Titulares — Implementação

Prazo de resposta: **15 dias corridos** (Art. 18, §3).

| Direito | Art. | Implementação mínima |
|---------|------|---------------------|
| Confirmação de existência | 18, I | Endpoint `GET /api/user/data-summary` |
| Acesso aos dados | 18, II | Export de todos os dados do usuário |
| Correção | 18, III | Formulário de edição de perfil |
| Anonimização/bloqueio | 18, IV | Função de anonimização (ver abaixo) |
| Portabilidade | 18, V | Export em JSON/CSV |
| Eliminação (consentimento) | 18, VI | Soft delete + purge agendado |
| Informação sobre compartilhamento | 18, VII | Página de política de privacidade |
| Informação sobre não-consentimento | 18, VIII | Página de política |
| Revogação do consentimento | 18, IX | Toggle por finalidade no perfil |
| Revisão de decisão automatizada | 20 | Log de decisões + canal de contestação |

```typescript
// src/lib/lgpd/user-data-export.ts
export async function exportUserData(userId: string) {
  const supabase = createServiceClient() // service_role para acesso completo
  
  const [profile, consents, requests, logs] = await Promise.all([
    supabase.from('profiles').select('*').eq('user_id', userId).single(),
    supabase.from('consent_records').select('*').eq('user_id', userId),
    supabase.from('titular_requests').select('*').eq('user_id', userId),
    supabase.from('data_processing_log').select('*').eq('user_id', userId),
    // Adicionar outras tabelas do projeto conforme o mapa de dados
  ])

  return {
    exported_at: new Date().toISOString(),
    user_id: userId,
    data: { profile: profile.data, consents: consents.data, requests: requests.data },
    processing_history: logs.data,
  }
}

// src/lib/lgpd/user-deletion.ts
export async function requestUserDeletion(userId: string) {
  const supabase = createServiceClient()
  
  // Soft delete: marcar como excluído, dados físicos excluídos após 30 dias
  await supabase.from('profiles').update({
    deleted_at: new Date().toISOString(),
    name: '[DADOS EXCLUÍDOS]',
    email: `deleted_${userId}@removed.local`,
    // Preservar: user_id (chave), audit_log (obrigação legal)
  }).eq('user_id', userId)

  // Revogar consentimentos ativos
  await supabase.from('consent_records')
    .update({ granted: false, revoked_at: new Date().toISOString() })
    .eq('user_id', userId)
    .eq('granted', true)

  // Registrar no log
  await supabase.from('titular_requests').insert({
    user_id: userId,
    email: 'requested_via_app',
    request_type: 'deletion',
    status: 'completed',
    completed_at: new Date().toISOString(),
    description: 'Solicitação de eliminação via aplicativo',
  })
}
```

---

## 4. Privacy by Design — Checklist Operacional

### Minimização (antes de coletar qualquer dado)
- [ ] Este campo é realmente necessário para a funcionalidade? Se não: não colete
- [ ] Pode ser derivado de outro dado já coletado? Se sim: não duplique
- [ ] Tem prazo de retenção definido? Se não: definir antes de implementar

### Dados para LLMs — Regra Absoluta
- [ ] Dados de produção NUNCA em ambiente de desenvolvimento (usar sintéticos ou anonimizados)
- [ ] Antes de enviar ao LLM: anonimizar/pseudonimizar CPF, nome, email, telefone
- [ ] Provedor LLM: sempre conta API comercial — NUNCA ChatGPT Free/Plus ou Claude.ai Free/Pro

```typescript
// src/lib/lgpd/pii-redactor.ts
// Pré-prompt filter obrigatório antes de enviar dados ao LLM

const PII_PATTERNS = [
  { regex: /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, token: '[CPF]' },
  { regex: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, token: '[EMAIL]' },
  { regex: /\b(\+55\s?)?(\(?\d{2}\)?\s?)?[\d\s\-]{8,}\b/g, token: '[PHONE]' },
  { regex: /\b\d{5}-?\d{3}\b/g, token: '[CEP]' },
]

export function redactPII(text: string): string {
  return PII_PATTERNS.reduce((acc, { regex, token }) => {
    return acc.replace(regex, token)
  }, text)
}

// Uso no pré-prompt filter:
// const safeInput = redactPII(userMessage)
// const response = await llm.complete({ prompt: safeInput })
```

---

## 5. Decisões Automatizadas — Art. 20

Todo behavior que usa IA para tomar decisões que afetam o usuário:
- [ ] Log do `data_processing_log` com `automated: true` e `ai_model`
- [ ] Canal de contestação visível ao usuário (link na UI ou email)
- [ ] Explicação da decisão armazenada (mesmo que simplificada)

```typescript
// Exemplo: aprovação de crédito, scoring de leads, triagem automática
await supabase.from('data_processing_log').insert({
  user_id: affectedUserId,
  operation: 'automated_decision',
  data_categories: ['behavior', 'profile'],
  purpose: 'lead_scoring',
  legal_basis: 'IX-legítimo_interesse',
  automated: true,
  ai_model: 'gpt-4o-mini',
})
```

---

## 6. Política de Dados dos Provedores LLM

| Provedor | Produto correto | Treina com dados? | ZDR |
|----------|----------------|------------------|-----|
| OpenAI | API com chave (platform.openai.com) | Não (desde 03/2023) | Enterprise |
| Anthropic | API (console.anthropic.com) | Não por padrão | Enterprise |
| Azure OpenAI | Qualquer tier | Não — tenant isolado | N/A |
| **ChatGPT Free/Plus/Pro** | **❌ PROIBIDO** | **Treina por padrão** | ❌ |
| **Claude.ai Free/Pro/Max** | **❌ PROIBIDO** | **Retenção 5 anos** | ❌ |

> **Ação obrigatória antes de cada deploy com dados regulados:**
> Verificar e documentar a política atual do provedor no DPA do projeto.
> Políticas mudam — data da última verificação deve estar no documento.

---

## 7. Resposta a Incidentes de Dados

**Prazos inegociáveis (Res. CD/ANPD nº 15/2024):**

| Destinatário | Prazo | Canal |
|-------------|-------|-------|
| Equipe interna | 2 horas | Slack/WhatsApp |
| Cliente (controlador) | 24 horas | Email formal |
| ANPD | 3 dias úteis | Portal gov.br/anpd |
| Titulares afetados | Quando necessário | Email + banner in-app |

**Template de comunicação ao cliente (24h):**
```
Assunto: [INCIDENTE] Notificação de Violação de Dados — [Nome do Sistema]

Identificamos em [data/hora] uma ocorrência de [tipo de incidente].
Dados afetados: [categorias].
Titulares potencialmente afetados: [N aproximado].
Ação imediata tomada: [o que foi feito nas primeiras horas].
Próximos passos: [mitigação + comunicação ANPD].

IntelliX.AI — [contato responsável]
```

---

## 8. Regime Reforçado — Dados Sensíveis

Se o sistema processar saúde, biometria, religião, origem racial/étnica ou dado genético:

- [ ] Base legal: consentimento específico e destacado (formulário separado, não bundled)
- [ ] Criptografia AES-256-GCM para dados em repouso (Supabase Vault / pgcrypto)
- [ ] Acesso restrito: apenas roles com necessidade documentada
- [ ] Auditoria de acesso (toda leitura logada)
- [ ] Processamento local ou ZDR contratual com provedor LLM

```sql
-- Supabase Vault para dados sensíveis
-- Nunca armazenar CPF/dado de saúde em texto plano
INSERT INTO vault.secrets (secret, name, description)
VALUES (encrypt_sensitive_value, 'cpf_user_123', 'CPF do usuário 123');

-- Leitura:
SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = 'cpf_user_123';
```

---

## 9. Checklist de Conclusão LGPD

**Obrigatório antes de declarar compliance:**

- [ ] Mapa de dados preenchido (Seção 1) para cada tabela com PII
- [ ] Base legal documentada para cada operação de tratamento
- [ ] Tabelas `consent_records`, `titular_requests`, `data_processing_log` no schema
- [ ] Endpoint de exportação de dados implementado (Art. 18, V)
- [ ] Fluxo de exclusão implementado (soft delete + purge)
- [ ] Formulário/toggle de revogação de consentimento funcional
- [ ] PII redactor ativo no pré-prompt filter (se projeto usa LLM)
- [ ] Provedor LLM: conta API comercial verificada (não conta de consumo)
- [ ] Política de privacidade publicada e acessível
- [ ] Canal de contestação de decisão automatizada visível (se Art. 20)
- [ ] Prazo de resposta a incidentes documentado no projeto

---

## Integração com security-observability

Esta skill é executada **em paralelo** com `intellix:security-observability` na Fase 06.
Não são substitutas — são complementares:

- `security-observability` → segurança técnica (OWASP, rate limiting, headers, LLM security)
- `lgpd-compliance` → proteção de dados (bases legais, direitos, minimização, incidentes)

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Segurança técnica OWASP + rate limiting | `intellix:security-observability` |
| Auditoria antes de deploy em produção | `superpowers:verification-before-completion` |
| Schema Supabase e RLS avançado | `supabase-postgres-best-practices` |
