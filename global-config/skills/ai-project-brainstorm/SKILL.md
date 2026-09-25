---
name: ai-project-brainstorm
description: >
  Transforma uma ideia de projeto em um documento de planejamento completo com
  PRD, arquitetura, banco de dados, stack, roadmap e prompt de geração para IA.
  Use esta skill SEMPRE que o usuário: descrever uma ideia de projeto, app, SaaS
  ou sistema; pedir para planejar, arquitetar ou definir stack de um projeto;
  mencionar "brainstorm", "ideia de projeto", "project idea", "PRD", "MVP",
  "planejar sistema", "system design", "arquitetura de projeto", "tech stack",
  "stack para", "roadmap", "prompt para gerar sistema", "vibecoding de projeto novo",
  "novo SaaS", "novo app", "quero criar um", "quero construir um", "me ajuda a planejar",
  "preciso de um sistema que", "build an app for", "I want to create", ou qualquer
  variação que indique concepção de um projeto de software novo.
  Também ative quando o usuário pedir para gerar o prompt final que uma IA
  usaria para implementar o sistema completo.
  NÃO use para projetos já em andamento que precisam apenas de correções, debug
  ou refatoração. NÃO use para criação de skills (usar skill-creator).
compatibility:
  tools: [bash]
  dependencies: []
---

# AI Project Brainstorm

Transforma uma ideia bruta de projeto em um documento de planejamento executável: PRD orientado a MVP, arquitetura do sistema, banco de dados, stack tecnológica, roadmap de desenvolvimento e prompt de geração para IA — tudo calibrado ao tamanho e complexidade reais do projeto.

## Setup

Sem dependências externas. A skill gera apenas documentos Markdown.

## Workflow

### Passo 1: Receber, interpretar e classificar a ideia

Quando o usuário descrever a ideia, faça três coisas antes de qualquer pergunta:

1. **Identifique o domínio** — SaaS B2B, consumer app, ferramenta interna, marketplace, plataforma de IA, etc.

2. **Classifique a complexidade** — Comunique a classificação ao usuário para que ele possa validar ou corrigir. Isso evita que todo o planejamento seja construído sobre uma premissa errada.

| Nível | Sinais típicos | Exemplo |
|---|---|---|
| **Micro** | 1-3 telas, sem auth ou banco mínimo | Landing page com formulário, calculadora, tool simples |
| **Pequeno** | 3-8 telas, auth básico, CRUD, 3-8 tabelas | Todo app, blog com admin, portfolio dinâmico |
| **Médio** | 8-20 telas, auth + roles, integrações, 8-20 tabelas | SaaS com dashboard, CRM, plataforma de agendamento |
| **Grande** | 20+ telas, multi-tenant, filas, real-time, 20+ tabelas | Marketplace, plataforma de cursos, ERP vertical |

3. **Resuma o entendimento** — Em 2-3 frases, diga o que você entendeu que o projeto é, para quem, e qual a complexidade inferida. Isso abre espaço para correção antes de investir tempo nas próximas fases.

### Passo 2: Entrevista estratégica

Faça perguntas adaptadas ao que o usuário descreveu — não use questionário genérico. O objetivo é entender o suficiente para tomar decisões de arquitetura, não levantar cada requisito.

**Sempre pergunte (adapte a formulação):**
1. **Usuários e acesso** — Quem usa? Perfis/roles diferentes? Autenticação?
2. **Funcionalidades core** — Quais 3-5 features definem o MVP? O que precisa funcionar no dia 1?
3. **Integrações** — Conexão com serviços externos? (pagamentos, WhatsApp, email, APIs)

**Pergunte apenas se relevante ao domínio:**
4. **Dados e escala** — Volume esperado? (calibra banco e infra)
5. **Real-time** — Atualizações ao vivo? (chat, notificações, dashboards)
6. **Monetização** — Como gera receita? (billing, planos, trial)
7. **Mobile** — App nativo necessário ou web responsivo basta?
8. **Multi-tenancy** — Dados isolados por cliente/empresa?

Se os requisitos envolverem decisão automatizada sobre texto em volume,
tempo de resposta crítico ou obrigação de manter dados em ambiente controlado,
registre a decisão aberta **`evaluate decision layer`** e encaminhe sua avaliação
para a skill `intellix-decision-layer`
(`global-config/skills/intellix-decision-layer/SKILL.md`). Nesta fase, não
escolha mecanismo, limiar nem fornecedor: isso pertence à arquitetura do projeto.

> Para perguntas específicas por domínio (SaaS B2B, marketplace, IA, etc.), consulte `resources/references/architecture-patterns.md` seção "Perguntas estratégicas por domínio".

Limite: máximo 6 perguntas por rodada. Se a ideia já é detalhada, faça menos.

### Passo 3: Definir arquitetura e stack

A recomendação deve ser **proporcional à complexidade**. A razão é simples: projetos pequenos com arquitetura grande criam overhead de manutenção que mata o projeto; projetos grandes com arquitetura pequena criam gargalos que forçam reescrita.

**Arquitetura — guia de decisão:**

| Complexidade | Arquitetura | Por quê |
|---|---|---|
| Micro | Monolito simples / Static + Serverless | Overhead mínimo, deploy instantâneo, um dev mantém sozinho |
| Pequeno | Monolito modular (App Router) | Um repo, módulos separados por domínio, evolui sem fricção |
| Médio | Monolito modular + serviços auxiliares | Core monolítico, serviços separados só onde há benefício claro (ex: fila de emails, worker de IA) |
| Grande | Modular com bounded contexts | Módulos independentes que podem ser extraídos, event-driven onde faz sentido, mas começa monolítico e extrai quando doer |

**Banco de dados — guia de decisão:**

| Necessidade | Recomendação | Contexto |
|---|---|---|
| CRUD relacional (maioria dos casos) | PostgreSQL via Supabase | Relações claras, RLS integrado, auth pronto, realtime grátis |
| Schema volátil, dados não-relacionais | MongoDB / Firestore | Prototipagem rápida, documentos aninhados, schema-less |
| Real-time pesado | Supabase Realtime / Firebase RTDB | Chat, collaborative editing, dashboards live |
| Busca textual | PostgreSQL FTS ou Elasticsearch | FTS resolve 90% dos casos; ES só se busca é core do produto |
| Vetores / IA | pgvector (Supabase) ou Pinecone | pgvector suficiente até ~1M vetores, Pinecone acima disso |
| Cache / Rate limiting | Redis / Upstash | Sessões, cache de queries pesadas, rate limiting |

**Stack — sem favoritos, cada projeto decide:**

Avalie individualmente. Não há stack padrão. Cada escolha deve ter uma justificativa vinculada a um requisito real do projeto ("Next.js porque precisa de SSR para SEO" serve; "Next.js porque é popular" não serve).

| Camada | Opções e quando cada uma faz sentido |
|---|---|
| **Frontend** | Next.js (SSR, SEO, apps complexos) · Vite+React (SPAs, dashboards) · Astro (content-heavy) · React Native/Expo (mobile nativo) · Flutter (cross-platform UI customizada) |
| **Backend** | Next.js API Routes (pequeno-médio, JS/TS ecosystem) · FastAPI (ML/data, Python) · NestJS (enterprise, DDD) · Elixir/Phoenix (real-time massivo) |
| **BaaS** | Supabase (PostgreSQL+auth+storage+realtime, excelente default) · Firebase (prototipagem rápida, mobile-first) · Convex (real-time first) |
| **Auth** | Supabase Auth (se já usa Supabase) · Clerk (UX premium) · NextAuth (self-hosted) · Auth0 (enterprise) |
| **Pagamentos** | Stripe (internacional, SaaS) · Asaas (Brasil, boleto+pix) · Mercado Pago (Brasil, marketplace) |
| **Deploy** | Cloudflare Workers/Pages (padrão IntelliX) · Railway (containers) · Fly.io (edge) · AWS/GCP (enterprise) · Vercel (só como exceção declarada no projeto) |
| **UI** | Tailwind+shadcn/ui (utilitário) · Chakra UI (design system) · MUI (Material) · Mantine (features-rich) |
| **Validação** | Zod (TypeScript) · Pydantic (Python) |
| **Testes** | Playwright (E2E) · Vitest (unit) · pytest (Python) |

> Para padrões específicos por domínio (SaaS B2B, marketplace, plataforma de IA), consulte `resources/references/architecture-patterns.md` seção "Padrões de arquitetura por domínio".

### Passo 4: Montar o documento de planejamento

Gere o documento Markdown com estas 7 seções obrigatórias. Use o template de complexidade correspondente em `resources/references/architecture-patterns.md` seção "Templates de prompt de geração por complexidade" como base estrutural.

**Seções obrigatórias do documento:**

1. **Visão geral** — O que é, para quem, classificação (domínio + complexidade + tipo)
2. **Funcionalidades do MVP** — Core (dia 1) + Nice-to-have (pós-MVP) + Fora de escopo (com motivo)
3. **Arquitetura do sistema** — Componentes, responsabilidades, tecnologias, decisões com justificativa e decisões abertas (incluindo `evaluate decision layer`, quando acionada)
4. **Banco de dados** — Tabelas com campos/tipos/constraints + relacionamentos + RLS policies
5. **Stack tecnológica** — Tabela camada/tecnologia/justificativa
6. **Roadmap** — Fases com duração e tarefas concretas (usar estimativas de vibecoding do reference file)
7. **Prompt de geração** — Prompt auto-contido para IA construir o sistema completo

### Passo 5: Calibragem final — a regra da proporcionalidade

Antes de entregar, verifique se cada decisão é proporcional:

- Projeto Micro com microserviços? → Reduza. Se um dev solo vai manter, monolito.
- Projeto Grande com monolito simples? → Escale. Bounded contexts existem por uma razão.
- Stack com 15 tecnologias para um CRUD? → Simplifique. Cada dependência é superfície de manutenção.
- Roadmap de 6 meses para 5 telas? → Comprima. Vibecoding muda radicalmente os prazos.
- Prompt de geração que diz "conforme descrito acima"? → Reescreva. Deve funcionar colado em outra sessão.

A regra de ouro: **o documento deve ser executável**. Uma IA (ou um dev) deve conseguir construir o MVP lendo apenas este documento.

### Passo 6: Salvar e entregar

1. Salve em `/mnt/user-data/outputs/[nome-do-projeto]-brainstorm.md`
2. Use `present_files` para compartilhar
3. Pergunte: "Quer ajustar alguma seção ou partimos para a implementação?"

## Padrões

### Nome do arquivo de output
`[nome-do-projeto]-brainstorm.md` — ex: `nossocrm-brainstorm.md`, `agendai-brainstorm.md`

### Tom e linguagem
Português BR. Tom técnico mas acessível. Toda decisão com justificativa ("usamos X porque Y"). Termos técnicos quando precisos, sem jargão gratuito.

### Regras do prompt de geração (seção 7 do documento)
O prompt de geração é o entregável mais importante — é o que vai alimentar o Claude Code ou outro agente. Ele precisa ser:
- **Auto-contido** — Repetir tudo que for necessário. Nunca referenciar "o documento acima". A razão: o prompt será copiado para outra sessão que não tem o contexto do documento.
- **Imperativo** — "Crie...", "Implemente...", "Configure..."
- **Específico** — Versões exatas, nomes de tabelas, endpoints
- **Com anti-padrões** — Dizer o que NÃO fazer. A razão: LLMs tendem a tomar atalhos (usar `any`, pular RLS, ignorar loading states) quando não há restrição explícita.
- **Com critérios mensuráveis** — Lighthouse >90, WCAG AA, RLS em 100% das tabelas, TypeScript strict, zero `any`

## Exemplos

**Exemplo 1: Ideia simples → resultado enxuto**

Input: "Quero criar um app de lista de tarefas com categorias"

Resumo da classificação: "Entendi: um app de gestão de tarefas pessoais com organização por categorias. Classifico como **Pequeno** — CRUD simples com auth básico, ~5 tabelas."

Stack recomendada: Next.js 16 + Supabase + Tailwind + shadcn/ui + Cloudflare Workers
Banco: 4 tabelas (users, tasks, categories, task_categories)
Roadmap: 1-2 semanas com vibecoding
Prompt de geração: ~40 linhas, direto e enxuto

**Exemplo 2: Ideia complexa → resultado modular**

Input: "Preciso de uma plataforma de agendamento para clínicas médicas com gestão de pacientes, prontuário eletrônico, pagamentos e integração com WhatsApp para confirmação"

Resumo da classificação: "Entendi: plataforma SaaS B2B vertical para clínicas odontológicas. Multi-tenant (cada clínica isolada). Classifico como **Médio-Grande** — 8+ módulos, ~20 tabelas, integrações externas."

Stack recomendada: Next.js 16 + Supabase (PostgreSQL + Auth + RLS multi-tenant) + WhatsApp API + Asaas
Banco: ~22 tabelas com RLS por clínica_id, módulos separados (agendamento, pacientes, prontuário, financeiro)
Roadmap: 5-7 semanas com vibecoding
Prompt de geração: ~150 linhas, com cada módulo detalhado

**Exemplo 3: Ideia vaga → entrevista antes de tudo**

Input: "Quero criar um SaaS"

Resposta: "Interessante! Antes de planejar a arquitetura, preciso entender melhor: que problema esse SaaS resolve? Quem seria o usuário principal? Qual é a funcionalidade que faz alguém pagar por isso?"

Nunca adivinhar. Só prosseguir com clareza suficiente para classificar.

## Armadilhas comuns

- ❌ Recomendar microserviços para projetos Micro/Pequeno → ✅ Monolito modular. Microserviços adicionam complexidade operacional (deploy independente, service discovery, observabilidade distribuída) que um dev solo não consegue manter. Regra prática: se um dev mantém, monolito.

- ❌ Gerar prompt de geração com "conforme descrito acima" → ✅ Prompt 100% auto-contido. O prompt vai ser colado em outra sessão de Claude Code que não tem contexto nenhum do documento. Se referenciar algo externo, vai gerar código incompleto.

- ❌ Empilhar tecnologias sem justificativa → ✅ Cada tech com um "porque" vinculado a um requisito real. O excesso de dependências é a principal causa de projetos vibecoded que travam na manutenção. Limites sugeridos: Micro 4-5, Pequeno 6-8, Médio 8-12, Grande sem limite rígido mas cada uma justificada.

- ❌ Omitir RLS ao recomendar Supabase → ✅ RLS em 100% das tabelas. É o mecanismo primário de segurança row-level. Sem RLS, qualquer usuário autenticado pode ler dados de outros usuários via API REST do Supabase.

- ❌ Definir tabelas antes de pensar nos relacionamentos → ✅ Comece pelos relacionamentos (1:1, 1:N, N:N) e derive as tabelas a partir deles. Redesign de schema é o tipo mais caro de refatoração em projetos já com dados.

- ❌ Roadmap com prazos de dev manual → ✅ Prazos de vibecoding: Micro 1-3 dias, Pequeno 1-2 semanas, Médio 3-6 semanas, Grande 2-4 meses. Consulte o reference file para fatores de ajuste.

## Checklist de qualidade

Antes de entregar o documento, verifique:

- [ ] Classificação de complexidade comunicada ao usuário e coerente com as features
- [ ] Arquitetura proporcional à complexidade
- [ ] Banco de dados cobre todas as entidades do MVP
- [ ] Relacionamentos entre tabelas documentados (1:1, 1:N, N:N)
- [ ] Cada escolha de stack tem justificativa vinculada a um requisito
- [ ] Roadmap com fases, duração e tarefas concretas
- [ ] Prompt de geração auto-contido — funciona colado em sessão nova
- [ ] Prompt de geração inclui anti-padrões e critérios mensuráveis
- [ ] Nenhuma feature do MVP é na verdade nice-to-have
- [ ] Nenhuma decisão sem justificativa

## Output e entrega

- Salvar em `/mnt/user-data/outputs/[nome-do-projeto]-brainstorm.md`
- Usar `present_files` para compartilhar com o usuário
- Após entrega, perguntar: "Quer ajustar alguma seção ou partimos para a implementação?"
