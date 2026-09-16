# Operations — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§13–17](../MASTER-ARCHITECTURE.md).
> Consulte ao definir estratégia de testes, variáveis de ambiente, inicialização de projeto ou checklist de deploy.

## 14. Testes — Estratégia por Camada

| Camada | Framework | O que testar |
|--------|-----------|--------------|
| Funções puras / utils | Vitest | Formatadores, validações, cálculos |
| Services | Vitest | Lógica de negócio com DB real (não mock) |
| Route Handlers | Vitest | Autenticação, validação, respostas HTTP |
| Behaviors completos | Playwright | Happy path + edge cases + error cases |
| Fluxos E2E | Playwright | Jornadas completas do usuário |

**Cobertura mínima por behavior:**
- [ ] Happy path completo
- [ ] Edge case (dados limítrofes, valores nulos)
- [ ] Error case (não autenticado, não autorizado, DB error)

### Cobertura alta não é sinônimo de correta — lição de auditoria real

Uma sprint de testes que levou a cobertura de um projeto de ~37% para ~90% em módulos
críticos revisou o próprio resultado com um segundo modelo e achou 3 categorias de bug
que "cobertura alta" escondia:

1. **Fixture não-representativa do dado real de produção.** Todos os fixtures de teste
   de uma feature usavam `property_id` preenchido — mas em produção essa coluna é
   **sempre `NULL`** para esse fluxo (fato conhecido do domínio, nunca verificado no
   teste). O caminho dominante de produção nunca foi exercitado até a correção.
   **Regra:** ao escrever fixture, pergunte "isso reflete o dado real, ou o dado
   idealizado/completo?" — puxe uma amostra real (anonimizada) quando o schema permitir
   valores `NULL`/vazios que o time "sabe" que não deveriam existir mas existem.
2. **Asserção que testa a tabela errada.** Um teste de isolamento multi-tenant (client
   service-role, que ignora RLS) parecia provar que a escrita filtrava por `user_id` —
   mas a asserção verificava a tabela errada. Passou na primeira revisão; só uma segunda
   revisão adversarial (fresh context, checklist específico de "o que essa asserção
   realmente prova") encontrou o gap.
3. **God-files de UI precisam de ferramenta diferente de god-files de service.** Testar
   `service`/`repository` usa mock de cliente Supabase; testar componente React grande
   (`.tsx` com centenas de linhas, múltiplos composers/handlers) exige React Testing
   Library com queries por `role`, não o mesmo harness de mock de banco. Planeje isso
   como duas frentes de trabalho diferentes, não uma extensão da mesma sprint.

**Prática recomendada:** para módulos com lógica de negócio sensível a estado real do
banco (não CRUD trivial), inclua no critério de aceite da tarefa de teste: "revisão
adversarial por um segundo agente/pessoa com checklist semântico, não só % de
cobertura". Cobertura mede execução de linha, não corretude de asserção.

---

### Idempotência ao empurrar dados para APIs externas não-idempotentes (crons)

Cron que faz `POST` para uma API externa que **não aceita chave de idempotência** (comum
em integrações de terceiros) tem um risco real de duplicar o efeito colateral (criar o
mesmo registro 2x) se o cron rodar 2x no mesmo intervalo ou se duas instâncias
concorrerem. Padrão *claim-before-POST*: reivindique atomicamente a linha antes de
chamar a API externa; se a chamada falhar, reverta o claim para tentar de novo depois.

```typescript
// Reivindica atomicamente — só um processo consegue marcar; quem perde a corrida
// não faz o POST duplicado.
const { data: claimed } = await supabase
  .from('bookings')
  .update({ pushed_at: new Date().toISOString() })
  .eq('id', bookingId)
  .eq('user_id', userId)
  .is('pushed_at', null)          // ← condição que garante exclusividade
  .select('id');

if (claimed?.length !== 1) return; // outro processo já reivindicou, pula sem duplicar

try {
  await externalApi.post('/bookings', payload);
} catch (err) {
  // Reverte o claim — vira candidato a retry no próximo run, em vez de "perdido".
  await supabase.from('bookings').update({ pushed_at: null, push_error: String(err) }).eq('id', bookingId);
  throw err;
}
```

**Regra:** o pior cenário deve ser "linha pulada, tenta de novo no próximo run" — nunca
"efeito colateral externo duplicado". Se a API externa não tem endpoint de idempotência,
a garantia tem que vir do seu lado (claim atômico + rollback em falha).

### CI que aplica todas as migrations do zero — pega drift antes de produção

Rodar `tsc`/lint num CI comum não pega migrations não-reproduzíveis: função ou trigger
criado direto em produção via console e nunca capturado numa migration, coluna que só
existe em produção "fora de banda", dois arquivos de migration com o mesmo prefixo
numérico colidindo na PK de `schema_migrations`. Nenhum desses aparece rodando as
migrations *incrementalmente* sobre um banco que já tem o estado acumulado — só aparece
recriando o banco do zero.

```yaml
# .github/workflows/security.yml (job adicional)
db-migration-reproducibility:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: supabase/setup-cli@v1
    - run: supabase start        # banco local vazio
    - run: supabase db reset     # aplica TODAS as migrations do repo, do zero
    # se qualquer migration referenciar algo que só existe em produção, falha aqui —
    # não em produção, semanas depois.
```

**Regra:** rodar este job bloqueante no CI é a única forma confiável de garantir que
"o repositório de migrations reconstrói o banco real" — sem ele, migrations podem
divergir silenciosamente de produção por meses até alguém tentar reconstruir do zero
(disaster recovery, ambiente novo, staging) e descobrir que não funciona.

---

## 15. Variáveis de Ambiente

```bash
# .env.example — template obrigatório no repo

# Supabase (todo projeto)
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=      # NUNCA expor no cliente

# App
NEXT_PUBLIC_APP_URL=            # URL de produção

# IA (se usar agentes)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# WhatsApp (se integrar)
EVOLUTION_API_URL=
EVOLUTION_API_KEY=

# Automação (se usar n8n)
N8N_WEBHOOK_URL=
N8N_API_KEY=

# Email
RESEND_API_KEY=

# Cron
CRON_SECRET=
```

---

## 16. Inicialização de Projeto

### CLAUDE.md padrão por projeto

```markdown
# [Nome do Projeto]

## Contexto
[Descrição em 2-3 linhas do que o sistema faz]

## Stack
Next.js 16 App Router | TypeScript strict | Tailwind | Shadcn/UI | Supabase | Cloudflare Workers

## Fase atual
[FASE] — ver .intellix-phase

## Arquitetura
Ler MASTER-ARCHITECTURE.md para todas as regras de arquitetura, padrões e workflow.

## Padrões obrigatórios
- TypeScript strict: NUNCA usar `any`
- Repository pattern: nunca acessar Supabase diretamente de componentes
- Commits: Conventional Commits (feat:, fix:, docs:, refactor:, chore:)
- Testes: toda feature nova precisa de testes cobrindo happy path + edge + error
- RLS: toda tabela Supabase com Row Level Security

## Integrações ativas
[listar: n8n / Evolution API / WhatsApp / Anthropic / etc]
```

### `.claude/settings.json` por projeto

```json
{
  "enabledPlugins": {
    "intellix@intellix-plugin": true
  }
}
```

---

## 17. Deploy Checklist

### Pré-requisitos
- [ ] Testes E2E passando (100%)
- [ ] `tsc --noEmit` limpo
- [ ] Sem `console.log` em produção
- [ ] `.env.example` atualizado
- [ ] `.intellix-phase` = `deploy`

### Variáveis de ambiente (mínimo obrigatório)
```
# não sensíveis → "vars" no wrangler.jsonc
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
NEXT_PUBLIC_APP_URL

# sensíveis → wrangler secret put <NOME>
SUPABASE_SERVICE_ROLE_KEY
```

### Domínio (Cloudflare Custom Domain)
Configurar `routes: [{ "pattern": "seu-dominio.com.br", "custom_domain": true }]` no
`wrangler.jsonc` (ou Dashboard → Worker → Domains & Routes). O certificado é emitido
automaticamente — não há registro A/CNAME manual. Passo a passo: skill `intellix:deploy`.

### Health check pós-deploy
```bash
curl -f https://[dominio]/api/health && echo "OK"
```
