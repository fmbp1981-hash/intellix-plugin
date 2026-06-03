# Security Rules — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§13–17](../MASTER-ARCHITECTURE.md).
> Consulte ao implementar autenticação, autorização, middleware, headers de segurança ou qualquer rota pública.

## 13. Segurança — Checklist por Nível

### Nível BÁSICO (Landing Pages, Sites Estáticos)
- [ ] Sem variáveis de ambiente sensíveis com `NEXT_PUBLIC_`
- [ ] Headers de segurança básicos no `next.config.ts`
- [ ] Sem `console.log` com dados em produção

### Defense in Depth — 4 Camadas Obrigatórias

As 4 camadas abaixo devem coexistir. **Nenhuma confia na anterior.** Se uma falhar, as outras seguram.

```
1. Middleware Next.js     → bloqueia rotas sem sessão válida
2. Server Action / Route  → valida input com Zod (schema obrigatório)
3. Server Action / Route  → re-valida permissões consultando DB (não confiar no client)
4. Supabase RLS Policy    → última linha de defesa no banco de dados
```

> **Anti-pattern crítico:** `if (user.isAdmin)` no client é contornável com DevTools em 30 segundos.
> Role/permission check SEMPRE no server, consultando o banco — nunca confiando em variável enviada pelo client.

---

### Nível COMPLETO (SaaS, CRM, APIs, Auth)
- [ ] Autenticação validada no servidor em toda operação sensível
- [ ] Rate limiting em todas as rotas públicas
- [ ] Input sanitizado e validado no servidor (Zod) antes de qualquer operação
- [ ] RLS ativo em todas as tabelas Supabase
- [ ] Secrets apenas em variáveis server-side (nunca `NEXT_PUBLIC_` para dados sensíveis)
- [ ] Stack traces nunca expostos para o cliente
- [ ] RBAC validado no servidor, nunca no cliente
- [ ] Headers de segurança completos (CSP, HSTS, X-Frame-Options)
- [ ] Logs sem dados sensíveis (PII, tokens, passwords)

```typescript
// next.config.ts — headers de segurança completos
const nextConfig = {
  async headers() {
    return [{
      source: '/(.*)',
      headers: [
        { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-XSS-Protection', value: '1; mode=block' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        },
      ],
    }]
  },
}
```

---

## 14. DevSecOps IntelliX — Regras 4-9

> Baseado nas Diretrizes DevSecOps IntelliX v2.0 (Junho 2026).
> OWASP LLM Top 10 2025 · OWASP Agentic Top 10 2026 · NIST AI RMF · LGPD.

### Regra 4 — Pipeline CI/CD com Segurança Integrada

Todo repositório IntelliX tem estes três jobs no GitHub Actions (`.github/workflows/security.yml`):
- `secrets-scan` (Gitleaks) — detecta secrets commitados, roda em todo push
- `sast-scan` (Semgrep CE) — análise estática, config: `p/typescript p/owasp-top-ten p/nextjs`
- `sca-scan` (Trivy) — dependências vulneráveis, output SARIF para aba Security do GitHub

**Regra de bloqueio:** CRITICAL bloqueia merge. HIGH exige dispensa documentada.

Custo: zero. Os três são open-source e gratuitos no GitHub Actions.

---

### Regra 5 — Pipeline de Guardrails LLM (5 Camadas)

Todo behavior com LLM em produção implementa obrigatoriamente:

```
INPUT (usuário)
    ↓
[CAMADA 1] Pré-prompt Filter  ← OBRIGATÓRIO
    • Detecção de prompt injection direta (padrões regex + heurística)
    • Redação de PII (CPF/email/telefone → tokens antes do LLM)
    • Validação de formato e comprimento (Zod)
    • Bloqueio de inputs maliciosos
    ↓
[CAMADA 2] Retrieval Check  ← apenas para RAG
    • Filtragem por entitlement (ABAC — usuário só vê o que tem permissão)
    • Validação de relevância dos chunks
    • Prevenção de injeção indireta via documentos
    ↓
[CAMADA 3] LLM
    • System prompt separado do user input por delimitadores explícitos
    • Sempre conta API comercial (OpenAI API ou Anthropic API)
    • Nunca: ChatGPT Free/Plus, Claude.ai Free/Pro/Max com dados de clientes
    ↓
[CAMADA 4] Pós-output Validator  ← OBRIGATÓRIO
    • Sanitização de PII na saída
    • Verificação de conformidade com regras de negócio
    • Bloqueio de vazamento de system prompt
    ↓
[CAMADA 5] Avaliador / LLM-as-Judge  ← recomendado a partir do 2º mês
    • Segundo modelo avalia qualidade em % das respostas (Langfuse)
    • Alerta quando taxa de reprovação > 5%
    ↓
OUTPUT (usuário)
```

**Camadas obrigatórias:** 1 e 4 em qualquer LLM com dados de clientes.
**Camada 2:** apenas para RAG.
**Camada 5:** recomendada a partir do segundo mês de operação.

---

### Regra 6 — Gestão de Credenciais por Ambiente

| Ambiente | Onde guardar | O que nunca fazer |
|----------|-------------|-------------------|
| Local | `.env.local` (no .gitignore) | Commitar qualquer `.env` |
| CI/CD | GitHub Encrypted Secrets | Printar secrets em logs |
| Produção (Vercel) | Vercel Environment Variables | Prefixar com `NEXT_PUBLIC_` |
| n8n self-hosted | n8n Credentials (criptografadas) | Deixar `N8N_ENCRYPTION_KEY` vazio |
| Dados sensíveis por tenant | Supabase Vault (pgcrypto) | Armazenar em tabela sem criptografia |

**Regra absoluta:** `SUPABASE_SERVICE_ROLE_KEY` nunca em variável `NEXT_PUBLIC_` e nunca no frontend. Expõe o banco inteiro, bypassando RLS.

---

### Regra 7 — Política de Dados de LLMs

**Regra absoluta:** NUNCA usar contas de consumo com dados de clientes brasileiros (LGPD).

| Provedor | Produto correto | Proibido |
|----------|----------------|---------|
| OpenAI | API (platform.openai.com) | ChatGPT Free/Plus/Pro |
| Anthropic | API (console.anthropic.com) | Claude.ai Free/Pro/Max |
| Azure OpenAI | Qualquer tier | — |

Verificar e documentar data da última consulta às políticas do provedor no DPA do projeto.
Políticas mudam — reconfirmar antes de cada deploy com dados regulados.

---

### Regra 8 — LGPD em Todo Feature com Dados Pessoais

Antes de implementar qualquer feature que toca dados pessoais, responder:

1. **QUAIS dados** pessoais esta feature coleta ou processa?
2. **BASE LEGAL** (Art. 7 LGPD): qual hipótese? Documentar.
3. **MINIMIZAÇÃO**: dá para processar com menos dados? Se sim: fazer.
4. **RETENÇÃO**: por quanto tempo? Quem exclui e quando?
5. **TITULAR**: como o usuário acessa, corrige e exclui?

Se qualquer resposta for "não sei" → invocar `lgpd-compliance` antes de continuar.

**Prazos inegociáveis:**
- Resposta ao titular: 15 dias corridos (Art. 18, §3)
- Comunicação interna de incidente: 2 horas
- Comunicação ao cliente (controlador): 24 horas
- Notificação ANPD: 3 dias úteis (Res. CD/ANPD nº 15/2024)
- Multa máxima: 2% do faturamento no Brasil / R$ 50 milhões por infração

---

### Regra 9 — Shadow AI — Dever de Orientação ao Cliente

Ao entregar sistema de IA para cliente PME, incluir obrigatoriamente:

- [ ] Cláusula contratual sobre uso de ferramentas de IA não sancionadas
- [ ] Orientação de 1 página sobre política de uso de IA segura
- [ ] Lista das ferramentas sancionadas e seguras para o cliente usar
- [ ] Alerta sobre riscos: Shadow AI pode adicionar US$ 670K ao custo de violação (IBM 2025)

**Por que:** 97% das organizações violadas via IA não tinham controles de acesso adequados.
A IntelliX, como operadora, pode ser corresponsabilizada por danos causados por sistemas que desenvolveu.

---

## 15. As 5 Regras de Ouro IntelliX DevSecOps

Baseadas nas Diretrizes v2.0 — aplicam a 100% dos projetos, sem exceção.

| # | Regra | O que significa na prática |
|---|-------|---------------------------|
| 1 | Se não há base legal documentada, o tratamento não começa | Mapa de dados antes de qualquer tabela com PII |
| 2 | Credencial no código é infração interna. Zero tolerância | Gitleaks no CI, `.env.local` no gitignore, Vault para dados sensíveis |
| 3 | Dado de produção jamais entra em ambiente de desenvolvimento | Dados sintéticos ou anonimizados em dev/test sempre |
| 4 | Nenhum agente vai a produção sem validador de output implementado | Camada 4 (pós-output validator) é pré-requisito de deploy |
| 5 | Incidente: 2h interno · 24h cliente · 3 dias úteis ANPD | Plano de resposta documentado antes do deploy em produção |
