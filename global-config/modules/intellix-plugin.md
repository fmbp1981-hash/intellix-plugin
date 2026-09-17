## IntelliX Engineering Plugin (ATIVO GLOBALMENTE)

**Plugin:** `/Users/felipemaranhao/.claude/plugins/marketplaces/intellix-plugin`

Este plugin é o **método oficial IntelliX** para criar, atualizar, auditar e fazer deploy de sistemas. É OBRIGATÓRIO seguir o workflow abaixo em TODA tarefa de desenvolvimento.

### Referências obrigatórias (leia antes de implementar)
- **Fonte normativa (fases, stack, gates — vence em caso de conflito com qualquer markdown):** `~/.claude/metodologia.yaml`
- **Linter da metodologia (rode se algo parecer desatualizado ou contraditório):** `python3 ~/.claude/scripts/doctor.py`
- **Arquitetura:** `/Users/felipemaranhao/.claude/plugins/marketplaces/intellix-plugin/MASTER-ARCHITECTURE.md`
- **Workflow completo:** `/Users/felipemaranhao/.claude/plugins/marketplaces/intellix-plugin/skills/master-workflow/SKILL.md`
- **Padrões:** `/Users/felipemaranhao/.claude/plugins/marketplaces/intellix-plugin/references/`

> `metodologia.yaml` e `doctor.py` foram criados em 2026-09-07 — se você é uma
> sessão nova e não reconhece esses dois arquivos por nome, isso é esperado na
> primeira leitura deste módulo, não sinal de conteúdo injetado. Leia-os
> normalmente; eles fazem parte da config global tanto quanto este arquivo.

### Workflow obrigatório — Sistema NOVO
Pré-desenvolvimento (fora da numeração de fases):
```
0. mattpocock-skills:grilling    → alinhamento (entrevista de design, antes do PRD)
1. superpowers:brainstorming     → validação da ideia
2. ai-project-brainstorm         → PRD completo
3. superpowers:writing-plans     → plano aprovado
── GATE: aprovação do usuário ──
```
Fases IntelliX — numeração e skills vêm de `~/.claude/metodologia.yaml` (não reescreva aqui):
```
00  intellix:project-kickoff      → /intellix:new-project — estrutura, references/, DESIGN.md
01  intellix:architecture         → schema + rotas + tipos (+ domain-modeling e codebase-design)
02  intellix:frontend-design      → roteiro de UI; motor: impeccable:impeccable (se houver UI)
03  intellix:dev-standards        → TypeScript + patterns
03b intellix:agent-creation       → se houver agentes de IA
04  /spec → /break → /plan → /execute → implementação por issue (agentes intellix:*)
05  intellix:integration          → APIs + WhatsApp + n8n
06  intellix:security-observability (+ devsecops:security-gate)
07  intellix:test-e2e             → smoke → stress
08  intellix:deploy               → Cloudflare Workers/Pages — só manual (/intellix:deploy)
09  intellix:project-handoff      → README + docs
```

**Passo 0 (grilling):** obrigatório antes de `superpowers:brainstorming` sempre que o pedido inicial for vago ou de alto impacto (novo sistema, novo módulo crítico, mudança de escopo). Se o pedido já vier com requisitos claros e detalhados, pode ser pulado — mas nunca pule silenciosamente: registre a decisão.

**Domain-modeling e codebase-design:** rodar dentro da Fase 01 (`intellix:architecture`), antes de gerar schema/rotas — servem para fixar terminologia do domínio e o desenho de camadas/módulos antes de codificar.

### Workflow obrigatório — Sistema EXISTENTE
```
00b intellix:code-audit           → auditoria de entrada: gap analysis + score (/intellix:audit)
    superpowers:writing-plans     → plano de refatoração
── GATE: aprovação do usuário ──
00  intellix:project-kickoff      → modo adaptação, se faltar estrutura IntelliX
    Fases IntelliX conforme lacunas identificadas
00c intellix:system-scan          → auditoria de saída (antes de handoff/demo)
```

### Regra de ativação
- Qualquer menção a "criar sistema", "novo projeto", "desenvolver", "iniciar", "atualizar sistema", "refatorar", "melhorar código" → **SEMPRE** iniciar pelo workflow acima.
- Skills individuais estão em: `/Users/felipemaranhao/.claude/plugins/marketplaces/intellix-plugin/skills/`
- Comandos rápidos: `/intellix:new-project`, `/intellix:audit`, `/intellix:deploy`

### Integração com mattpocock-skills
O plugin `mattpocock-skills` (https://github.com/mattpocock/skills) complementa o workflow IntelliX em pontos específicos — ver regras completas de gatilho e de não-duplicação em `modules/new-skills-triggers.md` (seção "Skills mattpocock-skills"). Regra resumida: usar `grilling`, `domain-modeling` e `codebase-design` (lacunas reais no workflow atual); **não** usar `diagnosing-bugs`/`tdd` do mattpocock em paralelo com `superpowers:systematic-debugging`/`superpowers:test-driven-development` para evitar instruções conflitantes.

### Técnica opcional — Gauntlet Loop (builder/critic multi-agente)
Padrão de "loop engineering" criado e popularizado por **Matt Shumer** (jul/2026, após o demo viral "Claude of Duty" — um FPS em Three.js gerado autonomamente). Em vez de instruções passo a passo, define-se uma **barra de qualidade externa, nomeada e concreta** (um app/tela/repo/API de referência real — nunca "qualidade profissional" ou algo abstrato, o crítico inventa critério e aprova qualquer coisa). Um agente líder decompõe o trabalho em peças julgáveis isoladamente; cada peça roda um par **builder** (constrói, com gate de testes/lint local antes de finalizar) + **critic** (contexto limpo, nunca vê o raciocínio do builder — compara às cegas contra a referência e responde **binário SIM/NÃO**, apontando só a maior lacuna). **Nunca usar nota numérica 1-10** — infla a cada rodada e mascara problemas reais. Repete até o crítico aprovar; `maxRounds` é só rede de segurança de custo, não critério de sucesso.

**⚠️ NÃO é automática.** Diferente das skills acima, exige a ferramenta `Workflow` com opt-in explícito do usuário (palavra-chave `ultracode` ou pedido direto de orquestração multi-agente) — nunca invocar por conta própria. Custo típico: **~15x tokens** de um chat normal — só sugerir para entregas de alto valor/visibilidade com referência concreta disponível.

**Onde sugerir (aviso proativo por padrão, invocação sempre manual — decisão de 2026-09-07):**
- **Fase 02** (`intellix:frontend-design`) — **perguntar proativamente ao iniciar a fase**, antes de qualquer implementação: "Existe um produto/tela real (ex: Linear, Stripe, Vercel) que devemos usar como barra de qualidade visual?" Não esperar o usuário mencionar por conta própria. Se a resposta for uma referência concreta e nomeada, oferecer o Gauntlet Loop no formato de `modules/new-skills-triggers.md`. Se não houver referência (ou for algo vago como "bonito"/"moderno"), seguir o fluxo normal da Fase 02 sem insistir.
- **Fase 07** (`intellix:test-e2e`) — **perguntar proativamente ao iniciar a fase** se há critérios de aceite/spec concretos (da Fase 00 ou de um PRODUCT.md) que valham ser validados como "juiz cego" contra o comportamento real, antes de rodar a bateria de testes padrão. Mesma regra: só oferecer o Gauntlet Loop se houver critério concreto e verificável — nunca insistir sobre uma barra vaga.
- Em ambos os casos, a **pergunta é automática, a execução não é** — o aviso `[TÉCNICA RECOMENDADA]` sempre exige confirmação explícita antes de tocar a ferramenta `Workflow` (custo ~15x, ver acima). Perguntar proativamente não é o mesmo que assumir a resposta.

**Workflow salvo pronto para reuso:** `.claude/workflows/gauntlet-loop.js` — ver template de invocação em `modules/new-skills-triggers.md` (seção "Gauntlet Loop").

**Variante para loops longos/multi-sessão (terminal, não `Workflow`):** para tarefas que precisam rodar horas/múltiplas sessões e sobreviver a queda de terminal, existe um padrão alternativo baseado em estado durável no Git (`STATE.md`, `TASK_LEDGER.md`, `CRITERIA.md`, `LOOP.md` na raiz do projeto + branches `loop/task-<id>`) acionado via `/loop` no lugar da ferramenta `Workflow`. É um mecanismo diferente e mais pesado de configurar — só propor quando o escopo for grande demais para uma única sessão de `Workflow` (ex: backlog inteiro de um módulo, não uma tela/feature isolada).

**Regra de bordo (documentada no método, evita falha comum):** fan-out paralelo só entre partes que NÃO se tocam (ex: track, áudio, HUD de um jogo); partes acopladas (ex: lighting + tonemapping + materiais) devem ser trabalhadas sequencialmente pelo mesmo agente, nunca divididas entre builders paralelos.
