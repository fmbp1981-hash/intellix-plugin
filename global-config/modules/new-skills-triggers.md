## Triggers — Novas Skills de Qualidade IntelliX

### Skills com invocação AUTOMÁTICA pelo Claude (Skill tool)

Quando detectar qualquer um dos padrões abaixo, invocar a skill via `Skill` tool ANTES de responder.

#### `intellix:architecture`
**Invocar quando:** criando serviços, repositórios, use cases, handlers, factories, aplicando SOLID/DDD/Clean Architecture, discutindo camadas de software, estruturando um módulo novo. (Substitui o antigo gatilho para `architecture-patterns`, skill que não está instalada.)
- Keywords: "criar serviço", "repository", "use case", "service layer", "SOLID", "Clean Architecture", "DDD", "dependency injection", "bounded context"

#### `lgpd-compliance`
**Invocar quando:** criando ou modificando qualquer feature que colete, trate ou armazene dados pessoais de pessoas físicas — cadastro de usuários, formulários com nome/email/CPF/telefone, autenticação, SaaS, CRM, e-commerce, agendamento, chat, bot WhatsApp, analytics, ou integração com sistemas fiscais oficiais (SPED, NFe/NFSe, e-CAC).
- Keywords: "LGPD", "dados pessoais", "proteção de dados", "privacidade", "consentimento", "DPO", "titular de dados", "política de privacidade", "vazamento de dados", "ANPD", "direitos dos usuários", "exclusão de dados", "portabilidade", "cadastro de usuário", "formulário com CPF/email/telefone", "sigilo fiscal", "CTN"
- Também invocar em paralelo sempre que `security-observability` (Fase 06) for acionada e o projeto tratar dados de pessoas físicas — não depender apenas do texto interno da Fase 06 para isso.

#### `code-review:code-review`
**Invocar quando:** fazendo code review de qualquer PR ou trecho de código. Aplica os padrões do plugin oficial `code-review`.
- Keywords: "code review", "revisar PR", "analisar código", "qualidade do código", "feedback de código"

#### `superpowers:systematic-debugging`
**Invocar quando:** investigando bugs, erros, crashes, comportamentos inesperados, ou implementando fallbacks/error boundaries.
- Keywords: "bug", "erro", "crash", "não funciona", "stack trace", "exception", "error boundary", "fallback", "recovery"

#### `intellix:test-e2e`
**Invocar quando:** escrevendo ou revisando testes E2E com Playwright ou Cypress — page objects, fixtures, interceptadores, locators. (Substitui o antigo gatilho para `e2e-testing-patterns`, skill que não está instalada; para automação de browser use também o plugin `playwright`.)
- Keywords: "playwright", "cypress", "page object", "fixture", "locator", "intercept", "e2e test"

#### `gsap-*` (gsap-core, gsap-timeline, gsap-scrolltrigger, gsap-react, gsap-plugins, gsap-performance, gsap-utils)
**Invocar quando:** criando ou ajustando animações JavaScript com GSAP — tweens, timelines, scroll-driven animation, easing, stagger, matchMedia responsivo.
- Keywords: "gsap", "tween", "timeline de animação", "scroll animation", "scrolltrigger", "easing", "stagger", "animação em React/Vue com JS"

#### `hyperframes` (+ hyperframes-core, hyperframes-animation, hyperframes-cli, hyperframes-creative, hyperframes-keyframes, hyperframes-registry)
**Invocar quando:** qualquer pedido para criar, editar, animar ou renderizar vídeo, motion graphic, promo, explainer, overlay ou slideshow via HTML.
- Keywords: "criar vídeo", "renderizar vídeo", "motion graphic", "promo", "explainer", "overlay", "hyperframes"

#### `motion-design`
**Invocar quando:** aplicando princípios de motion design — timing, easing, choreography, micro-interações, transições de página, loading states.
- Keywords: "micro-interação", "transição de página", "loading state", "motion design", "choreography de animação"

#### `remotion-to-hyperframes`
**Invocar quando:** converter Remotion para HyperFrames, ou criar/editar vídeo com Remotion (React-based) — intro/outro, logo animation, reels/shorts, captions em vídeo.
- Keywords: "remotion", "vídeo em React", "intro/outro", "logo animation", "reel", "short", "vídeo genérico/amador"

#### `graphify`
**Invocar quando:** perguntas sobre arquitetura do codebase, relações entre arquivos, ou quando existir a pasta `graphify-out/`.
- Keywords: "arquitetura do código", "mapa do codebase", "relação entre arquivos", "graphify"

#### `cloudflare`
**Invocar quando:** qualquer tarefa envolvendo Cloudflare — Workers, Pages, KV, D1, R2, Workers AI, WAF, Tunnel, Terraform/Pulumi para Cloudflare.
- Keywords: "cloudflare", "workers", "cloudflare pages", "KV namespace", "D1", "R2", "WAF", "cloudflare tunnel"

#### ⛔ Skills de deploy do plugin `vercel` — deprioritizadas, não desabilitadas
**Decisão de 2026-09-07** (avaliação pendente da auditoria `WORKFLOW-SPINE-VS-ORBIT.md`, resolvida): com a troca de stack de deploy para Cloudflare (Workers/Pages), as skills de deploy do plugin oficial `vercel` — `deployments-cicd`, `env-vars`, `vercel-cli`, `cdn-caching`, `vercel-functions`, `next-upgrade` — **não devem ser invocadas automaticamente** para tarefas de deploy/CI-CD/env vars/produção. Use `cloudflare` e `wrangler` para isso.
- **Por que não desabilitar o plugin:** o Claude Code só permite habilitar/desabilitar plugin inteiro em `settings.json`, não skill individual — e o plugin `vercel` também contém `nextjs`, `shadcn`, `react-best-practices`, que continuam relevantes independente do host de deploy. Desabilitar o plugin inteiro cortaria essas três junto.
- **Por que não editar os arquivos das skills:** elas vivem em `plugins/cache/claude-plugins-official/vercel/` — cache gerenciado do plugin oficial, sobrescrito a cada atualização. Editar ali não é uma correção durável.
- **Regra prática:** só invocar uma dessas seis skills de deploy do `vercel` se o usuário disser explicitamente que aquele projeto específico continua hospedado na Vercel (exceção pontual, não o padrão). Fora isso, tratar menção a "deploy" como Cloudflare por padrão (ver `modules/dev-rules.md`, tabela Stack Padrão).

---

### Skills mattpocock-skills (https://github.com/mattpocock/skills)

Plugin registrado no marketplace `claude-plugins-official` e **já instalado e habilitado** (`mattpocock-skills@claude-plugins-official: true` em `settings.json`). Preenche lacunas específicas do workflow IntelliX — ver `modules/intellix-plugin.md` para onde cada uma entra na sequência de fases.

O pacote tem 24 skills publicadas; a maioria é slash-command-only (`disable-model-invocation: true`, não aparecem para invocação automática via `Skill` tool). As seções abaixo cobrem as que valem gatilho no workflow IntelliX; `ask-matt`, `implement`, `to-spec`, `to-tickets`, `triage` e `wayfinder` formam um fluxo alternativo completo "ideia → ship" que **compete** com `superpowers:writing-plans`/`epic-workflow` — não usar automaticamente, só sob pedido explícito do usuário nomeando a skill.

#### `mattpocock-skills:grilling`
**Invocar quando:** o pedido de um sistema/feature novo for vago, de alto impacto, ou envolver escopo ainda não fechado — como pré-passo do `superpowers:brainstorming` (passo 0 do workflow de sistema novo).
- Keywords: "quero criar um sistema", "novo projeto", "nova feature", pedido inicial sem requisitos claros
- Pode ser pulado se o pedido já vier com requisitos detalhados — mas registre a decisão de pular, nunca pule silenciosamente.

#### `mattpocock-skills:domain-modeling`
**Invocar quando:** iniciando a Fase 01 (`intellix:architecture`), antes de definir schema/rotas — para fixar glossário e terminologia do domínio do projeto.
- Keywords: "modelar domínio", "entidades do sistema", "glossário do projeto", termos ambíguos entre stakeholders

#### `mattpocock-skills:codebase-design`
**Invocar quando:** desenhando módulos, camadas e limites de responsabilidade dentro da Fase 01, em conjunto com `intellix:architecture`.
- Keywords: "design de módulo", "limites de camada", "estrutura de pastas", "separação de responsabilidades"

#### `mattpocock-skills:writing-for-agents`
**Invocar quando:** escrevendo documentação consumida por IA (SKILL.md, CLAUDE.md, specs) — reforça o mesmo objetivo do padrão já definido em `modules/dev-rules.md` ("Formato de Documentação"). Usar como checklist complementar, não como fonte concorrente.

#### `mattpocock-skills:resolving-merge-conflicts`
**Invocar quando:** resolvendo conflitos de merge/rebase — complementa `git-workflow-and-versioning`, focando em resolução por intenção (o que cada lado tentava fazer) em vez de escolha mecânica de lado.
- Keywords: "conflito de merge", "resolver conflito", "merge conflict", "rebase conflitando"

#### ⛔ Não usar em paralelo (evitar instrução conflitante)
As skills abaixo do mattpocock-skills têm equivalente já ativo no workflow IntelliX/superpowers. **Não invocar automaticamente** — se o usuário pedir explicitamente por nome, pode usar, mas avise que existe redundância.
- `mattpocock-skills:diagnosing-bugs` → já coberto por `superpowers:systematic-debugging`
- `mattpocock-skills:tdd` → já coberto por `superpowers:test-driven-development`
- `mattpocock-skills:code-review` → complementar a `code-review:code-review`/`superpowers:requesting-code-review`, mas não invocar as três juntas automaticamente — priorizar as duas já ativas; usar a do mattpocock só se o usuário pedir explicitamente a revisão "em dois eixos" (padrões + fidelidade à spec)
- `mattpocock-skills:prototype`, `mattpocock-skills:research` → uso pontual sob pedido explícito do usuário, não têm gatilho automático definido ainda

---

### Gauntlet Loop (builder/critic multi-agente)

Criado e popularizado por **Matt Shumer** (jul/2026, demo "Claude of Duty").

**Avisar quando (decisão de 2026-09-07 — postura proativa, não mais só reativa):**
- O usuário pedir uma UI/tela com qualidade comparável a um produto de referência concreto (ex: "quero uma tela no nível do Linear/Stripe"), ou pedir validação de um fluxo E2E contra critérios de aceite concretos de uma spec — e ainda não tiver mencionado `ultracode` nem pedido orquestração multi-agente; **ou**
- **Ao iniciar a Fase 02 (`intellix:frontend-design`) ou a Fase 07 (`intellix:test-e2e`) do workflow IntelliX** — perguntar proativamente se existe uma referência de qualidade concreta (Fase 02: app/tela real) ou critérios de aceite verificáveis (Fase 07), em vez de esperar o usuário mencionar por conta própria. Ver `modules/intellix-plugin.md` seção "Onde sugerir" para o texto exato da pergunta por fase.
- Perguntar proativamente não significa assumir a resposta nem pular a confirmação — se não houver referência concreta e nomeada, ou o usuário preferir seguir sem, continue o fluxo normal da fase sem insistir de novo na mesma tarefa.
- **Formato do aviso:**
  > `[TÉCNICA RECOMENDADA] Para bater a qualidade de <referência>, posso rodar um Gauntlet Loop — builder e critic em par, comparando o resultado real contra a referência às cegas (aprovação SIM/NÃO, sem nota numérica), repetindo até o crítico aprovar. Isso usa a ferramenta Workflow (custo ~15x tokens de um chat normal) e exige sua confirmação explícita. Quer que eu rode o workflow salvo gauntlet-loop.js?`
- **Nunca invocar a ferramenta `Workflow` automaticamente** para isso — apenas sugerir e esperar confirmação.
- Não sugerir para tarefas pequenas ou sem referência concreta, nomeada e coletável disponível — o método falha com barras vagas ("qualidade profissional", "design moderno"); só funciona com barras comparáveis e verificáveis (um produto/tela/repo/API real que o Claude consiga ler/screenshot).
- **Crítico deve ser binário (SIM/NÃO), nunca nota 1-10** — escalas numéricas inflam a cada rodada e o loop encerra sem resolver os problemas reais.
- **Sem round fixo como critério de sucesso** — o `maxRounds` do workflow é rede de segurança de custo, não a condição desejada de parada. Se uma peça atingir o `maxRounds` sem aprovação, isso é sinal de revisão manual, não de "concluído".

**Como invocar (depois de confirmado pelo usuário):** rodar o workflow salvo passando `args`:
```js
Workflow({
  name: "gauntlet-loop",
  args: {
    target: "<O QUE construir/melhorar>",
    reference: "<REFERÊNCIA CONCRETA, nomeada e coletável — app/tela/repo/API real>",
    testCommand: "<opcional: comando de teste/lint local, ex: 'npm test'>",
    maxRounds: 8,   // opcional, default 8 — rede de segurança, não meta
    isolate: false  // true se as peças podem tocar os mesmos arquivos em paralelo
  }
})
```
Workflow salvo: `.claude/workflows/gauntlet-loop.js` (decompõe em peças, roda builder + critic binário por peça em paralelo entre peças que não se tocam, sequencial dentro de cada peça).

**Variante para loops muito longos/multi-sessão:** quando o escopo é grande demais para uma sessão de `Workflow` (ex: backlog inteiro, não uma feature isolada), existe um padrão alternativo via terminal usando `/loop` + arquivos de estado durável no Git (`STATE.md`, `TASK_LEDGER.md`, `CRITERIA.md`, `LOOP.md` na raiz do projeto, branches `loop/task-<id>`). Não é a ferramenta `Workflow` — é um protocolo de instruções persistentes que sobrevive a queda de sessão. Só propor sob pedido explícito do usuário para esse cenário específico.

---

### `archify` (diagrama de arquitetura/workflow/sequência/dataflow/lifecycle — sugestão proativa, nunca automática)

Instalada e auditada em 2026-09-09 (`tt-a1i/archify`, MIT, ver commit da instalação para o
detalhe da auditoria de segurança). Gera HTML autocontido a partir de evidência real do
repositório — não invenção de dependência.

**Decisão de 2026-09-10:** sugerir proativamente nos estágios abaixo, sempre perguntando
antes de rodar (nunca invocar sozinho) — mesmo padrão do Gauntlet Loop: a pergunta é
automática, a execução não é.

**Quando sugerir:**
- **Fase 00b (`intellix:code-audit`), após a Fase 1 (Mapeamento do Codebase):** o diagrama
  mostra a arquitetura **real** encontrada — útil antes de escrever o relatório de gaps da
  Dimensão 2 (Clean Architecture), porque expõe visualmente acoplamento e camada pulada que
  prosa esconde.
- **Fase 00c (`intellix:system-scan`), Estágio 5 (Veredito):** anexar ao relatório
  `SCAN-[data].md` como evidência visual do estado da arquitetura, junto da nota ponderada.
- **Fase 01 (`intellix:architecture`), depois do schema/rotas definidos:** diagrama da
  arquitetura **pretendida**, antes de codificar — mais barato corrigir acoplamento errado
  no diagrama do que depois de implementado.
- **Fase 09 (`intellix:project-handoff`):** artefato de entrega ao cliente — diagrama real
  da arquitetura final, complementa README/ADRs.
- **Fora das fases:** sempre que o usuário pedir para "visualizar", "entender" ou "explicar"
  a arquitetura/fluxo/sequência de um sistema, e a explicação em prosa estiver ficando longa
  ou difícil de acompanhar.

**Formato do aviso:**
> `[SKILL DISPONÍVEL] Posso gerar um diagrama real da arquitetura aqui com a skill archify — ajuda a visualizar [acoplamento/fluxo/o que for relevante ao estágio] antes de [prosseguir/fechar o relatório]. Quer que eu gere?`

**Não sugerir:** em toda revisão de PR pequena, feature isolada, ou quando o sistema é
trivial o bastante para caber numa frase — o custo de gerar e validar o diagrama não se
paga. Se o usuário recusar uma vez na mesma tarefa, não insistir de novo.

---

### Skills com aviso de chamada MANUAL (Claude informa o usuário)

Para estas skills, **não invocar automaticamente**. Em vez disso, exibir um aviso claro ao usuário com o comando exato a chamar.

#### `improve-codebase-architecture`
**Avisar quando:** detectar discussão sobre estrutura do projeto, reorganização de módulos, acoplamento excessivo, god classes, circular imports, prop drilling excessivo, refatoração de arquitetura.
- **Formato do aviso:**
  > `[SKILL RECOMENDADA] Antes de prosseguir, rode /improve-codebase-architecture para análise estrutural do codebase. Esta skill identifica acoplamento, abstrações erradas e módulos mal organizados antes que você comece a refatorar.`
- Nota: essa skill é do pacote `mattpocock-skills` (slash-only).

#### `mattpocock-skills:grill-with-docs`
**Avisar quando:** o passo 0 (grilling, ver `modules/intellix-plugin.md`) for necessário **e** já existir um working directory de projeto. É o `grilling` + `domain-modeling` combinados num único comando stateful, que já grava `CONTEXT.md`/ADR em vez de você chamar as duas skills separadamente.
- **Formato do aviso:**
  > `[SKILL RECOMENDADA] Rode /grill-with-docs para a entrevista de alinhamento — ela já grava CONTEXT.md e ADRs automaticamente, substituindo a chamada manual de grilling + domain-modeling.`
- Sem working directory de projeto (ex: planejamento solto, fora de um repo) → preferir `mattpocock-skills:grilling` (auto) em vez de avisar sobre esta.
- Não avisar E chamar `mattpocock-skills:grilling`/`domain-modeling` manualmente na mesma tarefa — escolher um caminho.

#### `mattpocock-skills:wizard`
**Avisar quando:** a tarefa exigir um passo manual que só o humano pode executar — configurar credenciais/secrets num dashboard de terceiro, provisionar infra por UI, ou um cutover/migração one-off — tipicamente dentro das Fases 05 (integration) e 08 (deploy) do IntelliX.
- **Formato do aviso:**
  > `[SKILL RECOMENDADA] Para os passos manuais desta etapa (dashboard, credenciais, cutover), rode /wizard — ele gera um script bash interativo que guia você por cada etapa, captura os valores e já grava em .env/GitHub secrets.`
- Não avisar para passos que o próprio Claude consegue executar (essa skill é só para o que exige ação humana fora do editor).

#### Registro de ADR (sem skill dedicada)
**Avisar quando:** tomando uma decisão técnica relevante — escolha de biblioteca, framework, abordagem, padrão de design, trade-off técnico.
- **Formato do aviso:**
  > `[ADR RECOMENDADO] Esta é uma decisão técnica relevante. Registre um ADR em docs/adr/ do projeto antes de implementar (regra em ~/.claude/metodologia.yaml → metricas.adr). Isso evita que a decisão seja revertida por falta de contexto futuro.`

#### `vercel:react-best-practices`
**Avisar quando:** discutindo otimização de performance de React/Next.js — bundle size, lazy loading, re-renders, memoização, Server Components, caching. (Substitui o antigo aviso para `/performance`, skill que não está instalada. A skill trata de performance de React/Next e independe do host de deploy.)
- **Formato do aviso:**
  > `[SKILL RECOMENDADA] Antes de otimizar, rode /vercel:react-best-practices — analisa bundle, re-renders, Server Components e caching.`

#### `browser-testing-with-devtools`
**Avisar quando:** prestes a fazer deploy em produção, ou quando o usuário mencionar que vai subir uma nova versão. (Substitui o antigo aviso para `/core-web-vitals`, skill que não está instalada.)
- **Formato do aviso:**
  > `[SKILL RECOMENDADA] Antes do deploy em produção, rode /browser-testing-with-devtools e meça LCP, CLS e INP (Lighthouse via Chrome DevTools MCP) — falhas nessas métricas afetam SEO e experiência do usuário.`

---

### Regra geral

- Se o hook `[SKILL] AVISO:` aparecer no contexto → reproduzir o aviso ao usuário no início da resposta, com o comando exato
- Se o hook `[SKILL] RECOMENDADO:` aparecer → invocar a skill via `Skill` tool antes de responder
- Nunca ignorar silenciosamente os avisos do hook
