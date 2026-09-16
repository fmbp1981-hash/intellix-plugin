# IntelliX Engineering Plugin — Guia do Workflow

**Organização:** IntelliX.AI · **Uso:** interno
**Atualizado em:** 2026-09-16 (remediação da estrutura) · **Versão do plugin:** ver `.claude-plugin/plugin.json`

> **Este guia explica o workflow; ele não é a regra.** Fases, IDs de skills, gates, stack e
> artefatos obrigatórios são definidos em `~/.claude/metodologia.yaml`. Se este texto e o
> YAML discordarem, vale o YAML — rode `python3 ~/.claude/scripts/doctor.py --strict`.
> Diagrama: [`workflow-flowchart.mmd`](workflow-flowchart.mmd) (fonte única; o PDF/PNG
> publicados em `docs/generated/` são gerados a partir dele e deste arquivo).

---

## 1. O que é

O IntelliX Engineering Plugin é o método de desenvolvimento da IntelliX.AI: fases, skills,
comandos, agentes e gates que levam um projeto — de landing page a SaaS com agentes de IA e
WhatsApp — da ideia à entrega com a mesma qualidade e previsibilidade.

| Princípio | Na prática |
|---|---|
| Arquitetura antes de código | O gate de fase bloqueia `/plan` e `/execute` enquanto a Fase 01 não registrar as decisões |
| Aprovação explícita | PRD, plano, SPEC, issues e plano tático são aprovados antes de avançar |
| Uma fonte por fato | Regras no `metodologia.yaml`; princípios no `MASTER-ARCHITECTURE.md`; procedimentos nas skills |
| Revisão em estágios | Cada arquivo do `/execute` passa por implementação, spec review e quality review |
| Nada copiado para o projeto | Skills, comandos e agentes vêm do plugin; o projeto guarda só contexto e decisões próprias |

---

## 2. Visão geral

```
PRÉ-DESENVOLVIMENTO   diagnóstico → grilling → brainstorming → PRD → plano      (GATE: aprovação)
FASES IntelliX        00 kickoff → 01 arquitetura → 02 frontend → 03 padrões → 03b agentes
                      → 04 implementação por issue → 05 integração → 06 segurança
                      → 07 testes → 08 deploy → 09 handoff
SISTEMA EXISTENTE     00b auditoria de entrada → plano → 00 (modo adaptação) → fases conforme lacunas
                      → 00c auditoria de saída
```

---

## 3. Pré-desenvolvimento

| Passo | Skill | Entregável |
|---|---|---|
| Diagnóstico com o cliente | — (formulário `docs/CLIENTE-DIAGNOSTICO.md`) | ficha preenchida |
| Alinhamento (pedido vago ou de alto impacto) | `mattpocock-skills:grilling` | decisões de escopo registradas |
| Validação da ideia | `superpowers:brainstorming` | ideia validada ou redirecionada |
| PRD | `ai-project-brainstorm` | PRD.md |
| Plano de implementação | `superpowers:writing-plans` | plano aprovado |

**Gate:** o cliente aprova PRD e plano antes da Fase 00.

---

## 4. Fases IntelliX

| Fase | Skill / comando | O que produz | Gate |
|---|---|---|---|
| **00** Kickoff | `/intellix:new-project` → `intellix:project-kickoff` | estrutura canônica, `AGENTS.md`, `CLAUDE.md`, `references/`, `DESIGN.md` semente, CI de segurança, `.env.example`, `package.json`; o `scaffold-check.py` confere | aprovação do usuário |
| **01** Arquitetura | `intellix:architecture` (+ `mattpocock-skills:domain-modeling`, `mattpocock-skills:codebase-design`) | schema com RLS, rotas, tipos, repository/service; decisões na seção 6 de `references/architecture.md` (remove o marcador de rascunho) e ADRs | aprovação do usuário |
| **02** Frontend *(se houver UI)* | `intellix:frontend-design` | `PRODUCT.md`, `DESIGN.md`, tokens e componentes base | — |
| **03** Padrões | `intellix:dev-standards` | TypeScript strict, naming, Server Actions, TanStack Query | — |
| **03b** Agentes de IA *(se houver)* | `intellix:agent-creation` → `intellix-agent-creation` | blueprint/configuração (GPT Maker, n8n ou nativo) | — |
| **04** Implementação | `/intellix:spec` → `/intellix:break` → `/intellix:plan` → `/intellix:execute` | `SPEC.md`, `issues/`, código e testes por issue | aprovação por issue |
| **05** Integração *(se houver)* | `intellix:integration` | SDKs, webhooks, WhatsApp (Evolution API), n8n | — |
| **06** Segurança | `intellix:security-observability` + `devsecops:lgpd-compliance` | rate limit, CSP, logs, Sentry, LGPD | `devsecops:security-gate` = PASS |
| **07** Testes | `intellix:test-e2e` | smoke → funcional → segurança → performance → stress | 100% passando |
| **08** Deploy *(manual)* | `/intellix:deploy` | Cloudflare Workers/Pages, domínio, health check, runbook, `docs/deploys.jsonl` | autorização explícita |
| **09** Handoff | `intellix:project-handoff` | README, ADRs, acessos, dívida técnica | — |
| Módulo opcional | `intellix:live-chat` | inbox omnichannel IA + humano | — |

### 4.1 Fase 02 — roteiro de UI

`intellix:frontend-design` conduz a fase; o design em si é feito pelo **`impeccable:impeccable`**
(motor de design). Ordem: `impeccable:impeccable` (`init` → `shape`) → `ui-ux-pro-max` →
`ui-design:design-system-patterns` → `impeccable:impeccable` (`new-work`) →
`impeccable:impeccable` (`polish`/`animate`/…) → `vercel:shadcn` →
`ui-design:visual-design-foundations` + `accessibility` + `seo`. Antes de começar, a skill
pergunta se existe um produto de referência concreto (possível Gauntlet Loop, só com
confirmação).

### 4.2 Fase 04 — o ciclo `/execute`

Cada arquivo da issue passa por três estágios obrigatórios:

1. **Implementação** por agente do plugin, conforme o tipo de arquivo:
   `intellix:model-writer` (migrations, tipos, repositories), `intellix:action-writer`
   (Server Actions, route handlers, services, integrações), `intellix:component-writer`
   (páginas, componentes, modais, hooks de UI), `intellix:test-writer` (testes).
2. **Spec review** — `intellix:spec-reviewer` (Happy Path, Edge Cases, Error Cases).
3. **Quality review** — `intellix:code-quality-reviewer` (Critical/Important bloqueiam).

Um quarto estágio (crítico contra referência externa) roda só quando a issue ou o `DESIGN.md`
define `quality_reference`. Detalhes: `references/four-commands.md`.

### 4.3 Fase 08 — deploy

Cloudflare é a plataforma padrão. Vercel só entra como exceção declarada no `CLAUDE.md` e em
`references/stack.md` do projeto. Fluxo trunk-based: PR → preview (`wrangler versions upload`);
`main` → staging; produção só via `/intellix:deploy` com autorização. Antes da produção:
medir LCP/CLS/INP com `browser-testing-with-devtools`; rollout gradual com
`shipping-and-launch`; pipeline com `ci-cd-and-automation` (não use os exemplos com `npx vercel` dela).

---

## 5. Auditorias e gates

| Perfil | Quando | Saída | Critério |
|---|---|---|---|
| Entrada — `intellix:code-audit` (`/intellix:audit`) | projeto existente, antes de refatorar | `docs/intellix-audit-<data>.md` | score em 12 dimensões; críticos antes de feature nova |
| Saída — `intellix:system-scan` | pré-handoff, demo, trimestral | `docs/system-scan/SCAN-<data>.md` | Classe A/B/C |
| Gate de segurança — `devsecops:security-gate` | antes de qualquer deploy | bloco `SECURITY_GATE` | zero CRITICAL/HIGH sem aceitação formal |
| Pentest — `/devsecops:pentest` | janela autorizada | `strix_runs/` | CRITICAL/HIGH bloqueiam deploy |
| Gate de fase — `phase-gate.sh` | `/plan`, `/execute`, deploy, handoff | bloqueio com a lista do que falta | artefatos presentes e arquitetura definida |

| Gate humano | Momento | Quem aprova |
|---|---|---|
| PRD | fim do pré-desenvolvimento | cliente |
| Plano | antes da Fase 00 | cliente |
| SPEC e issues | Fase 04, por feature | dev lead |
| Plano tático | Fase 04, por issue | dev lead |
| Deploy em produção | Fase 08 | responsável técnico |

---

## 6. Tipos de projeto e atalhos

| Tipo | Fases | Pula |
|---|---|---|
| Landing page / site | 00 → 01 (só rotas) → 02 → 07 (smoke) → 08 → 09 | 03b, 05, 06 completo |
| SaaS com autenticação | 00 → 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 | 03b se não houver IA |
| CRM / dashboard com agentes de IA | 00 → 01 → 02 → 03 → 03b → 04 → 05 → 06 → 07 → 08 → 09 | — |
| Automação WhatsApp + n8n | 00 → 01 → 03 → 03b → 04 → 05 → 06 → 07 → 08 → 09 | 02 |
| API sem interface | 00 → 01 → 03 → 04 → 05 → 06 → 07 → 08 | 02 |
| Projeto existente | 00b → plano → 00 (adaptação) → fases conforme lacunas → 00c | conforme o audit |

---

## 7. Onde está cada coisa

| Precisa de | Arquivo |
|---|---|
| Regras normativas (fases, IDs, stack, artefatos, hooks, auditorias) | `~/.claude/metodologia.yaml` |
| Princípios e visão do sistema | `MASTER-ARCHITECTURE.md` |
| Orquestração passo a passo | `skills/master-workflow/SKILL.md` |
| Ciclo `/spec` `/break` `/plan` `/execute` | `references/four-commands.md` |
| Padrões técnicos | `references/` (data layer, API, frontend, acessibilidade, segurança, operações) |
| Bootstrap de projeto novo | `skills/project-kickoff/references/bootstrap-projeto-novo.md` |
| Templates copiados para o projeto | `intellix-templates/` |
| Formulário de diagnóstico | `docs/CLIENTE-DIAGNOSTICO.md` |
| Convenções para mexer no plugin | `PLUGIN-CONVENTIONS.md` |

---

## 8. Como gerar os derivados

Os derivados publicados ficam em `docs/generated/` e **não são editados à mão**:

```bash
# diagrama (Mermaid CLI)
npx -y @mermaid-js/mermaid-cli -i docs/workflow-flowchart.mmd -o docs/generated/workflow-flowchart.png
# guia em PDF
npx -y md-to-pdf docs/WORKFLOW-DOCUMENTATION.md && mv docs/WORKFLOW-DOCUMENTATION.pdf docs/generated/
```

Registre em `docs/generated/PROVENIENCIA.md` a data, o commit de origem e os comandos usados.
