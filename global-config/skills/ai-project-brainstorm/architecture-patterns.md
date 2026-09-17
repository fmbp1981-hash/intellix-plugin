# Referência: Padrões de Arquitetura, Templates e Estimativas

> Carregue este arquivo quando precisar de:
> - Padrões de arquitetura por domínio (Passo 3)
> - Templates do documento de planejamento por complexidade (Passo 4)
> - Perguntas estratégicas por domínio (Passo 2)
> - Estimativas de prazo com vibecoding (Passo 4 — Roadmap)

## Índice

1. [Padrões de arquitetura por domínio](#padrões-de-arquitetura-por-domínio)
2. [Template do documento de planejamento](#template-do-documento-de-planejamento)
3. [Templates de prompt de geração por complexidade](#templates-de-prompt-de-geração-por-complexidade)
4. [Perguntas estratégicas por domínio](#perguntas-estratégicas-por-domínio)
5. [Estimativas de prazo com vibecoding](#estimativas-de-prazo-com-vibecoding)

---

## Padrões de arquitetura por domínio

### SaaS B2B
- **Auth**: Multi-tenant obrigatório. Cada organização com isolamento de dados via RLS ou schema separation.
- **Billing**: Stripe com planos (free/pro/enterprise), trial period, usage-based se aplicável.
- **Padrão comum**: Organization → Members → Resources. A org é sempre o tenant root.
- **Dashboard**: Métricas por organização, não globais.

### Consumer App
- **Auth**: Social login (Google, Apple) como primário. Email/senha como fallback.
- **Onboarding**: Fluxo de primeira experiência é crítico. Incluir no MVP.
- **Push notifications**: Se mobile, considerar desde o dia 1.
- **Analytics**: Event tracking desde o launch (Mixpanel, PostHog, Amplitude).

### Marketplace
- **Dois lados**: Sempre modelar buyer e seller como entidades separadas com permissões distintas.
- **Pagamentos**: Split payment (Stripe Connect ou intermediário brasileiro).
- **Trust & Safety**: Reviews, ratings, dispute resolution — incluir no roadmap mesmo que pós-MVP.
- **Search**: Full-text search robusto é core, não nice-to-have.

### Ferramenta interna
- **Auth**: SSO/LDAP se empresa grande. Auth simples se time pequeno.
- **UX**: Eficiência > beleza. Tabelas densas, bulk actions, keyboard shortcuts.
- **Permissões**: RBAC (Role-Based Access Control) quase sempre necessário.
- **Audit log**: Quem fez o quê, quando. Obrigatório para compliance.

### Plataforma de IA / Agente
- **LLM Gateway**: Nunca acoplar a um único provider. Implementar abstração com fallback (ex: OpenAI → Anthropic → local).
- **RAG**: pgvector no Supabase é suficiente para a maioria. Pinecone/Weaviate só se volume > 1M vetores.
- **Streaming**: Server-Sent Events para respostas de LLM. Nunca esperar resposta completa.
- **Rate limiting**: Obrigatório. Sem isso, um usuário consome toda a quota da API.
- **Cost tracking**: Registrar tokens consumidos por request. Sem isso, a conta explode silenciosamente.

---

## Template do documento de planejamento

Use este template como base estrutural para o documento gerado no Passo 4. Adapte o nível de detalhe à complexidade do projeto.

```markdown
# [Nome do Projeto]

> [Tagline de uma frase descrevendo o que o projeto faz]

## 1. Visão geral

### O que é
[2-3 frases: o que é, que problema resolve, para quem]

### Classificação
- **Domínio:** [SaaS B2B / Consumer App / Ferramenta interna / Marketplace / Plataforma de IA / etc.]
- **Complexidade:** [Micro / Pequeno / Médio / Grande]
- **Tipo:** [Web App / Mobile App / API / Plataforma / etc.]

## 2. Funcionalidades do MVP

### Core (obrigatório no dia 1)
- [ ] [Feature 1 — descrição breve + critério de done]
- [ ] [Feature 2 — descrição breve + critério de done]
- [ ] [Feature 3 — descrição breve + critério de done]

### Nice-to-have (pós-MVP)
- [ ] [Feature 4 — por que não é core]
- [ ] [Feature 5 — por que não é core]

### Fora de escopo (não fazer agora)
- [Feature X — motivo pelo qual ficou fora]

## 3. Arquitetura do sistema

### Visão de alto nível
[Descrição textual dos componentes e fluxo de dados entre eles.
Para projetos Médio+, incluir diagrama ASCII ou Mermaid se possível]

### Componentes principais
| Componente | Responsabilidade | Tecnologia |
|---|---|---|
| Frontend | [o que faz] | [tech] |
| API/Backend | [o que faz] | [tech] |
| Banco de dados | [o que faz] | [tech] |
| Auth | [o que faz] | [tech] |
| [Serviço X] | [o que faz] | [tech] |

### Decisões arquiteturais
[Para cada decisão significativa, explique: o que foi decidido + por quê + alternativas consideradas]

1. **[Decisão]**: [Justificativa vinculada a requisito]
2. **[Decisão]**: [Justificativa vinculada a requisito]

## 4. Banco de dados

### Relacionamentos (definir ANTES das tabelas)
[Liste os relacionamentos principais — isso define a estrutura das tabelas]
- users → [entidade] (1:N)
- [entidade_a] ↔ [entidade_b] (N:N via tabela pivot)
- ...

### Modelo de dados

#### `users`
| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| id | uuid | PK (from auth) | ID do usuário |
| email | text | NOT NULL, UNIQUE | Email |
| name | text | NOT NULL | Nome completo |
| avatar_url | text | | URL do avatar |
| created_at | timestamptz | DEFAULT now() | Data de criação |

#### `[entidade_principal]`
| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | ID único |
| user_id | uuid | FK → users.id, NOT NULL | Dono do registro |
| [campo] | [tipo] | [constraints] | [descrição] |
| created_at | timestamptz | DEFAULT now() | |
| updated_at | timestamptz | DEFAULT now() | |

[Repetir para cada tabela...]

### Políticas de segurança (RLS)
- Ativar RLS em TODAS as tabelas
- users: SELECT/UPDATE onde `auth.uid() = id`
- [entidade]: CRUD onde `user_id = auth.uid()`
- [Para multi-tenant]: filtrar por `organization_id` vinculado ao usuário

### Indexes
- [tabela].[coluna]: btree (filtragem frequente)
- [tabela].[coluna]: gin (busca textual, se aplicável)

## 5. Stack tecnológica

| Camada | Tecnologia | Por quê |
|---|---|---|
| Frontend | [tech + versão] | [justificativa vinculada a requisito] |
| Backend | [tech + versão] | [justificativa] |
| Banco de dados | [tech + provider] | [justificativa] |
| Auth | [tech] | [justificativa] |
| Deploy | [plataforma] | [justificativa] |
| UI/Styling | [tech] | [justificativa] |
| Pagamentos | [tech] | [justificativa — se aplicável] |
| Testes | [tech] | [justificativa] |

## 6. Roadmap de desenvolvimento

### Fase 1 — Fundação (Semana X-Y)
- [ ] Setup do projeto, repositório e CI/CD básico
- [ ] Schema do banco + migrations + RLS
- [ ] Auth (cadastro, login, recuperação de senha)
- [ ] Layout base, navegação e sistema de rotas
- [ ] [Tarefa específica do projeto]

### Fase 2 — Core Features (Semana X-Y)
- [ ] [Feature principal 1 — detalhamento]
- [ ] [Feature principal 2 — detalhamento]
- [ ] [Integrações necessárias]

### Fase 3 — Polish e Launch (Semana X-Y)
- [ ] Testes E2E dos fluxos críticos
- [ ] Performance (Lighthouse >90) e SEO
- [ ] Error handling, loading/empty states em todas as telas
- [ ] Deploy de produção + domínio + SSL

### Fase 4 — Pós-launch (Semana X+)
- [ ] Monitoramento e error tracking
- [ ] Analytics e event tracking
- [ ] Features nice-to-have priorizadas
- [ ] Feedback loop com usuários

## 7. Prompt de geração do sistema

> Cole este prompt no Claude Code ou outro agente de IA para gerar o sistema completo.
> Este prompt é auto-contido — funciona sem o documento acima.

[PROMPT COMPLETO AQUI — deve incluir:
- Stack exata com versões
- Estrutura de pastas esperada
- Todas as features do MVP com descrição técnica
- Schema completo do banco (tabelas, campos, tipos, constraints, RLS)
- Padrões de código obrigatórios
- Integrações necessárias com detalhes de implementação
- Critérios de qualidade mensuráveis
- Anti-padrões (o que NÃO fazer e por quê)]
```

---

## Templates de prompt de geração por complexidade

### Template — Projeto Micro

```
Crie um [TIPO DE APLICAÇÃO] usando:
- [Framework] com TypeScript strict
- [Estilização]
- Deploy em [plataforma]

## Funcionalidades
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

## Estrutura de pastas
src/
├── app/
│   ├── page.tsx
│   └── layout.tsx
├── components/
│   └── [componentes necessários]
└── lib/
    └── utils.ts

## Regras obrigatórias
- TypeScript strict, zero `any`
- Responsivo mobile-first
- Lighthouse Performance >90
- Sem dependências desnecessárias
- Código limpo, sem comentários óbvios

## NÃO fazer
- Não usar `any` no TypeScript
- Não criar abstrações prematuras
- Não instalar pacotes que podem ser feitos com CSS/JS nativo
```

### Template — Projeto Pequeno

```
Crie um [TIPO DE APLICAÇÃO] completo usando:

## Stack
- Frontend: [framework + versão]
- Backend: [framework + versão]
- Banco: [banco + provider]
- Auth: [método]
- UI: [biblioteca de componentes]
- Deploy: [plataforma]

## Funcionalidades do MVP
1. **[Feature 1]**: [descrição técnica detalhada]
2. **[Feature 2]**: [descrição técnica detalhada]
3. **[Feature 3]**: [descrição técnica detalhada]

## Schema do banco de dados

### Tabela: users
- id: uuid PK (gerado por auth)
- email: text NOT NULL UNIQUE
- name: text NOT NULL
- avatar_url: text
- created_at: timestamptz DEFAULT now()

### Tabela: [entidade_principal]
- id: uuid PK DEFAULT gen_random_uuid()
- user_id: uuid FK → users.id NOT NULL
- [campos específicos]
- created_at: timestamptz DEFAULT now()
- updated_at: timestamptz DEFAULT now()

### RLS Policies
- Todas as tabelas: ativar RLS
- users: SELECT/UPDATE onde auth.uid() = id
- [entidade]: SELECT/INSERT/UPDATE/DELETE onde user_id = auth.uid()

## Estrutura de pastas
[Estrutura completa esperada]

## Padrões de código
- TypeScript strict mode, zero `any`
- Zod para validação de todos os inputs
- React Hook Form para formulários
- Server Components por padrão, Client Components só quando necessário
- Error boundaries em todas as rotas
- Loading states para todas as operações async

## Critérios de qualidade
- Lighthouse: Performance >90, Accessibility >90, Best Practices >90, SEO >90
- WCAG AA compliance
- Responsivo: mobile, tablet, desktop
- Zero erros no console em produção

## NÃO fazer
- Não usar `any` no TypeScript
- Não fazer queries ao banco sem RLS
- Não deixar estados de loading sem feedback visual
- Não hardcodar strings — usar constantes
- Não criar componentes com mais de 150 linhas — extrair
- Não usar useEffect para fetch de dados — usar Server Components ou React Query
```

### Template — Projeto Médio/Grande

```
Crie uma [TIPO DE PLATAFORMA] completa seguindo estas especificações:

## Visão do produto
[Descrição completa do que é, para quem, que problema resolve]

## Stack técnica

### Core
- Frontend: [framework + versão exata]
- Backend: [framework + versão exata]
- Banco de dados: [banco + provider + extensões]
- Auth: [provider + métodos suportados]
- Storage: [provider para uploads]
- Real-time: [se aplicável — tecnologia]

### Integrações
- Pagamentos: [provider + tipo: subscription/one-time/split]
- Email: [provider — transacional e marketing]
- [Integração específica]: [provider + versão da API]

### Infra
- Deploy: [plataforma + plano]
- CI/CD: [pipeline]
- Monitoramento: [ferramenta]
- Analytics: [ferramenta]

## Módulos do sistema

### Módulo 1: [Nome]
**Responsabilidade**: [o que este módulo faz]
**Tabelas**: [quais tabelas pertencem a este módulo]
**Telas**:
- [Tela 1]: [o que mostra e permite fazer]
- [Tela 2]: [o que mostra e permite fazer]
**API Endpoints**:
- `GET /api/[recurso]` — [o que retorna]
- `POST /api/[recurso]` — [o que cria]
- `PATCH /api/[recurso]/:id` — [o que atualiza]

### Módulo 2: [Nome]
[Mesmo formato...]

## Schema completo do banco de dados

### Tabela: [nome]
| Coluna | Tipo | Constraints | Descrição |
|---|---|---|---|
| id | uuid | PK, DEFAULT gen_random_uuid() | ID único |
| [coluna] | [tipo] | [constraints] | [descrição] |

### Indexes
- [tabela].[coluna]: btree (filtragem frequente)
- [tabela].[coluna]: gin (busca textual)

### RLS Policies
[Política detalhada por tabela com a lógica SQL]

### Migrations — ordem de execução
1. Create extensions (pgvector, etc.)
2. Create enum types
3. Create tables (ordem respeitando FKs)
4. Create indexes
5. Enable RLS + create policies
6. Create functions + triggers
7. Seed data (se aplicável)

## Estrutura de pastas
[Árvore completa com cada diretório explicado]

## Padrões de código obrigatórios
[Lista detalhada de padrões, convenções de nomes, patterns]

## Critérios de qualidade não-negociáveis
- Lighthouse: todas as métricas >90
- WCAG AA compliance
- TypeScript strict, zero `any`, zero `as` assertions desnecessárias
- RLS em 100% das tabelas
- Error handling em 100% das operações async
- Loading/empty/error states em 100% das telas
- Testes E2E para fluxos críticos
- Rate limiting em endpoints públicos

## Anti-padrões — NÃO FAZER
[Lista detalhada do que não fazer, com o porquê]
```

---

## Perguntas estratégicas por domínio

### Para SaaS B2B
- Qual o tamanho das empresas-alvo? (define complexidade de permissões)
- Precisam de white-label ou customização por cliente?
- Há compliance específico? (LGPD, HIPAA, SOC2)
- Qual o modelo de pricing? (per-seat, usage-based, flat)

### Para Apps Consumer
- Qual a ação principal que o usuário faz? (o "aha moment")
- Mobile-first ou web-first?
- Qual a estratégia de aquisição? (orgânico, paid, referral — afeta features)
- Há aspecto social? (perfis públicos, feed, compartilhamento)

### Para Marketplaces
- Quem é o supply e quem é o demand?
- Como resolver o chicken-and-egg? (afeta MVP features)
- Qual o modelo de revenue? (comissão, assinatura, freemium)
- Há necessidade de verificação de identidade?

### Para Ferramentas com IA
- Qual o modelo/provider principal de LLM?
- Há necessidade de knowledge base própria? (RAG)
- Qual o volume esperado de requests/dia? (custo)
- O output da IA precisa ser editável pelo usuário?

### Para Ferramentas internas
- Quantos usuários internos vão usar?
- Precisa de audit log / compliance?
- Integra com SSO/LDAP corporativo?
- Quais sistemas internos existentes precisam conversar com este?

---

## Estimativas de prazo com vibecoding

Prazos realistas usando IA para gerar código (Claude Code, Cursor, etc.):

| Complexidade | Com IA | Sem IA (comparativo) |
|---|---|---|
| Micro | 1-3 dias | 1-2 semanas |
| Pequeno | 1-2 semanas | 1-2 meses |
| Médio | 3-6 semanas | 3-6 meses |
| Grande | 2-4 meses | 6-12 meses |

### Fatores que aumentam o prazo
- Integrações com APIs externas: +30% por integração complexa
- Multi-tenancy: +40% sobre a estimativa base
- Real-time: +20-30%
- Compliance (LGPD, HIPAA): +20-50%
- Mobile nativo: +60-100% (vs web only)
- Processamento de pagamentos: +15-25%

### Fatores que reduzem o prazo
- BaaS como Supabase: -20-30% (auth, storage, realtime de graça)
- Component library madura (shadcn): -10-15%
- Template/boilerplate existente: -20-30%
- Experiência prévia com stack: -15-20%
- Skill de geração de código específica do projeto: -10-20%
