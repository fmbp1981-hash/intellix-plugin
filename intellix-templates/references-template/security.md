# Segurança & DevSecOps — {{PROJECT_NAME}}

> Validar ANTES de cada PR/merge. Zero exceções.
> Gerado em: {{CREATED_AT}} | Framework: IntelliX DevSecOps v2.0

## As 5 Regras de Ouro IntelliX (inegociáveis)

| # | Regra |
|---|-------|
| 1 | Se não há base legal LGPD documentada, o tratamento de dados não começa |
| 2 | Credencial no código é infração interna — zero tolerância |
| 3 | Dado de produção jamais entra em ambiente de desenvolvimento |
| 4 | Nenhum agente vai a produção sem validador de output implementado |
| 5 | Incidente: 2h interno · 24h cliente · 3 dias úteis ANPD (Res. CD/ANPD nº 15/2024) |

---

## Defense in Depth — 4 Camadas Obrigatórias

```
1. Middleware Next.js     → bloqueia rotas sem sessão válida
2. Server Action / Route  → valida input com Zod (schema obrigatório)
3. Server Action / Route  → re-valida permissões consultando DB (não confiar no client)
4. Supabase RLS Policy    → última linha de defesa no banco de dados
```

> **Anti-pattern crítico:** `if (user.isAdmin)` no client é contornável com DevTools em 30 segundos.
> Role/permission check SEMPRE no server — nunca confiando em variável enviada pelo client.

---

## Pré-PR Checklist

### Segurança Base (100% dos PRs)
- [ ] Nenhuma API key em código client ou arquivo commitado
- [ ] Toda server action valida sessão no início (`await supabase.auth.getUser()`)
- [ ] RLS habilitado em toda tabela Supabase nova
- [ ] Rate limiting em endpoints públicos (Upstash ou in-memory)
- [ ] Inputs sanitizados com Zod antes de qualquer operação
- [ ] Erros não expõem stack trace ao client
- [ ] CORS configurado restritivamente (nunca `*`)
- [ ] Secrets apenas em variáveis server-side (nunca `NEXT_PUBLIC_` para dados sensíveis)
- [ ] Nenhuma lógica de role/permissão no client

### Segurança LLM (PRs com chamadas a LLMs)
- [ ] `prePromptFilter()` ativo — input sanitizado antes de enviar ao modelo
- [ ] `postOutputValidator()` ativo — output sanitizado antes de exibir
- [ ] `redactPII()` aplicado no input — CPF/email/telefone removidos antes do LLM
- [ ] Conta API comercial em uso (não ChatGPT Free/Plus nem Claude.ai Free/Pro)
- [ ] Rate limiting por usuário/tenant em chamadas LLM
- [ ] Limite de tokens por request definido (previne Denial of Wallet)

### LGPD (PRs com dados pessoais de pessoas físicas)
- [ ] Base legal documentada para os dados tratados neste PR
- [ ] Apenas dados mínimos necessários coletados (minimização — Art. 6, III)
- [ ] Fluxo de exclusão previsto para estes dados
- [ ] Decisões automatizadas por IA logadas com `automated: true` (Art. 20)

### CI/CD (por release)
- [ ] Gitleaks: zero secrets detectados
- [ ] Semgrep: zero vulnerabilidades CRITICAL/HIGH
- [ ] Trivy: zero CVEs CRITICAL em dependências
- [ ] `npm audit`: zero high/critical

---

## Anti-patterns Críticos

```typescript
// ❌ NUNCA — validação de role no client
if (user.isAdmin) { /* hacker muda em 30s no DevTools */ }

// ✅ SEMPRE — buscar no banco no server action
const { data: profile } = await supabase
  .from('profiles').select('role').eq('id', user.id).single()
if (profile.role !== 'admin') return unauthorized()
```

```typescript
// ❌ NUNCA — service role key no client
const supabase = createClient(url, process.env.NEXT_PUBLIC_SERVICE_ROLE_KEY!)

// ✅ SEMPRE — service role apenas em server (sem NEXT_PUBLIC_)
const supabase = createClient(url, process.env.SUPABASE_SERVICE_ROLE_KEY!)
```

```typescript
// ❌ NUNCA — PII direto no LLM
const response = await llm.complete({ prompt: `Analise o CPF ${user.cpf}` })

// ✅ SEMPRE — redação antes do LLM
import { redactPII } from '@/lib/lgpd/pii-redactor'
const response = await llm.complete({ prompt: redactPII(`Analise o CPF ${user.cpf}`) })
// Envia ao LLM: "Analise o CPF [CPF]"
```
