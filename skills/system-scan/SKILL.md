---
name: system-scan
description: >
  Use esta skill para uma auditoria COMPLETA e periódica de um sistema já em
  produção ou em fase de conclusão — véspera de handoff, antes de uma demonstração
  importante para cliente, ou como prática trimestral de manutenção. Diferente de
  `intellix:code-audit` (que decide SE vale refatorar antes de continuar
  desenvolvendo), esta skill produz um veredito de maturidade — "Classe A" ou não —
  com nota ponderada por dimensão, comparável ao scan anterior. Também ativa
  quando o usuário mencionar: "auditoria completa", "sistema classe A", "escanear
  o sistema", "auditoria de arquitetura profissional", "limpar o código",
  "organizar a estrutura do projeto", "está pronto pra produção de verdade".
  Esta é a Fase 00c do fluxo IntelliX — opcional, roda a qualquer momento após a
  Fase 01 (architecture) existir.
user-invocable: true
---

# Fase 00c — System Scan (Auditoria Classe A)

Orquestrador de 6 estágios que amarra ferramentas que já existem no arsenal
IntelliX/DevSecOps mas que, sozinhas, nenhuma cobre o sistema inteiro. Produz um
relatório único, versionável, e comparável entre execuções — regressão de
qualidade fica visível, não escondida.

> **Por que isto não é apenas `intellix:code-audit`:** o code-audit é ótimo para
> decidir "posso continuar desenvolvendo em cima disto, ou preciso refatorar
> antes?" — é o gate de entrada. Este scan responde uma pergunta diferente:
> "este sistema, hoje, está no nível que eu venderia como construído por um
> sênior de 20 anos, seguindo o que o mercado considera padrão em 2026?" — é o
> gate de saída. O code-audit vira o **Estágio 2** deste scan, não é substituído.

---

## Quando usar

```
Handoff para o cliente se aproximando?              → SEMPRE rodar antes
Demo importante ou investidor vai auditar o código?  → SEMPRE rodar antes
Prática de manutenção trimestral em sistema ativo?   → rodar como rotina
Meio de uma sprint, só quero saber se posso mexer?   → use intellix:code-audit, não este
Projeto não tem nem Fase 01 (architecture) ainda?    → cedo demais, rode project-kickoff primeiro
```

---

## Visão geral dos 6 estágios

```
Estágio 0 — Limpeza mecânica       → dead code, deps órfãs, arquivos mortos
Estágio 1 — intellix:code-audit    → as 12 dimensões (reaproveitado, não duplicado)
Estágio 2 — Static analysis        → CodeQL + Semgrep (vulnerabilidade real, não grep)
Estágio 3 — Fleet de 5 revisores   → mesmo fleet do gate de pré-deploy do devsecops
Estágio 4 — A11y + Performance     → WCAG + Core Web Vitals medidos de verdade
Estágio 5 — Veredito Classe A      → nota ponderada + comparação com scan anterior
```

Cada estágio tem critério de saída binário — "passou" ou "não passou", com o
motivo — nunca uma impressão vaga de "está bom".

---

## Estágio 0 — Limpeza mecânica (obrigatório, sempre primeiro)

> **Por que primeiro:** lixo no código confunde diagnóstico. Um `service`
> chamado de 3 lugares mas 2 são dead code parece acoplamento saudável até você
> descobrir que só 1 chamada é real. Limpar antes de avaliar.

```bash
# Dependências instaladas mas nunca importadas, e imports que apontam pro nada
npx depcheck
npx knip                      # cobre TS/JS: exports não usados, arquivos órfãos, deps fantasma

# Arquivos que nenhum outro arquivo importa (candidato a órfão — confirmar antes de apagar)
npx madge --orphans src/

# Tamanho de bundle por rota — abaixo disso e o dead code de UI já pesa no build
npx next build --profile 2>&1 | tail -30
```

**Regra de execução:** liste os achados, confirme com o usuário quais são
realmente órfãos (pode haver falso positivo — código chamado via string dinâmica,
webhook, cron), remova só o confirmado. Nunca apagar em lote sem revisão.

---

## Estágio 1 — `intellix:code-audit` (reaproveitado)

```
Skill("intellix:code-audit")
```

Rode as 5 fases dele por completo — mapeamento, gap analysis nas 12 dimensões,
relatório de gaps, roadmap de sprints. O relatório dele (`Score Geral: X/100`)
entra como um dos insumos do veredito final deste scan (Estágio 5), não é
substituído nem duplicado aqui.

---

## Estágio 2 — Static Analysis automatizada

> **Por que:** o code-audit usa `grep` dirigido — pega o que você pensou em
> procurar. Static analysis pega o que ninguém pensou em procurar: SQL injection
> por concatenação disfarçada, path traversal, ReDoS, uso inseguro de `eval`.

> **Correção de nomenclatura (verificado em 2026-09-08):** `codeql-build` e
> `semgrep-scan` **não são skills** — são scripts da ferramenta `Workflow`
> (`plugins/marketplaces/trailofbits/plugins/static-analysis/workflows/*.js`).
> `Workflow` exige opt-in explícito do usuário (palavra-chave `ultracode` ou
> pedido direto de orquestração multi-agente) — nunca disparar por conta própria,
> mesmo dentro deste scan automatizado. As skills reais do plugin (invocáveis
> normalmente via `Skill()`) são `static-analysis:codeql` e
> `static-analysis:semgrep`, que ensinam a rodar a ferramenta manualmente.

**Como proceder:**
1. Pergunte ao usuário se ele autoriza rodar os workflows `codeql-build` e
   `semgrep-scan` (mais completos, custam mais tokens, requerem opt-in).
2. Se não autorizado, use `Skill("static-analysis:codeql")` e
   `Skill("static-analysis:semgrep")` para configurar e rodar manualmente.

**Critério de saída:** zero findings CRITICAL/HIGH sem justificativa registrada.
Findings MEDIUM viram item do roadmap (Estágio 5), não bloqueiam o scan.

---

## Estágio 3 — Fleet de revisores (mesmo gate do pré-deploy)

> **Por que:** o code-audit é você (ou o agente) lendo o próprio código.
> O fleet é 5 revisores especializados, cada um só focado na sua dimensão,
> somente-leitura — o mesmo padrão que `devsecops:security-baseline` já usa
> antes de qualquer deploy. Rodar aqui, sobre o sistema inteiro em vez de um
> diff, é o que transforma "gate de PR" em "auditoria de sistema".

Dispare em paralelo (Agent tool, background), cada um revisando o repositório
inteiro, não um diff:

```
security-reviewer        → OWASP API Top 10, secrets, headers, rate limiting
privacy-lgpd-reviewer     → LGPD, base legal, dado pessoal em log/URL/resposta
multi-tenant-reviewer     → isolamento cross-tenant, IDOR/BOLA
database-architect        → RLS, SECURITY DEFINER, grants, migrations
architect-reviewer        → camadas, acoplamento, formato de API, naming
```

**Critério de saída:** consolide os 5 relatórios. Zero CRITICAL aberto sem
aceitação formal de risco — mesma régua do `devsecops:security-gate`.

---

## Estágio 4 — Acessibilidade e Performance real

> **Achado desta auditoria (2026-09-08):** o `intellix:test-e2e` promete
> "Performance tests — Lighthouse, Core Web Vitals" mas não implementa nenhum —
> só mede tempo de resposta de servidor sob carga (métrica diferente, legítima,
> mas não é Core Web Vitals). Este estágio cobre o que estava faltando.

### 4a — Acessibilidade
```
/accessibility-audit
```
> `accessibility-audit` é slash command do plugin `ui-design` (não skill via
> `Skill()`) — verificado em 2026-09-08. A skill correspondente do mesmo plugin
> é `ui-design:accessibility-compliance`, se precisar de referência em prosa
> em vez de rodar o comando.

Critério: WCAG 2.2 AA — sem exceção documentada.

### 4b — Core Web Vitals (medido, não estimado)
```bash
npx lighthouse https://staging.seudominio.com.br --output=json --output-path=./lighthouse-report.json --preset=desktop
npx lighthouse https://staging.seudominio.com.br --output=json --output-path=./lighthouse-report-mobile.json
```

**Thresholds reais de 2026** (75º percentil de usuário real Chrome, janela de 28
dias — verificado via pesquisa nesta sessão, não assumido de memória):

| Métrica | O que mede | Bom |
|---|---|---|
| LCP (Largest Contentful Paint) | velocidade de carregamento | ≤ 2.5s |
| INP (Interaction to Next Paint) | responsividade à interação — substituiu o FID em 2024 | ≤ 200ms |
| CLS (Cumulative Layout Shift) | estabilidade visual | ≤ 0.1 |

Essas são as três métricas reais do Google — não confundir com o
`thresholds = {"mean": 3.0, "p95": 5.0}` do teste de stress em
`intellix:test-e2e` (Passo 9), que mede tempo de resposta HTTP do servidor sob
carga, uma coisa completamente diferente e válida no seu próprio contexto.

---

## Estágio 5 — Veredito Classe A

### A rubrica

Ponderação por dimensão, calibrada contra o consenso de mercado 2026 para
SaaS/software profissional (não são pesos arbitrários — fonte: modelo de
maturidade SaaS que trata segurança/multi-tenancy/observabilidade como bloqueantes
de nota máxima, e arquitetura evolutiva — modular monolith antes de
microserviço prematuro — como o padrão saudável para estágio de crescimento):

| Dimensão | Peso | Fonte do critério |
|---|---|---|
| Segurança (Estágios 2+3, RLS, secrets, OWASP) | 25% | bloqueante — 1 CRITICAL aberto zera a dimensão inteira |
| Multi-tenancy / isolamento de dado | 15% | bloqueante — mesmo critério acima |
| LGPD / dado pessoal | 10% | bloqueante se o sistema processa dado de pessoa física |
| Arquitetura de camadas (code-audit dim. 2) | 15% | Clean Architecture / modular monolith |
| Qualidade de código (TS strict, dead code) | 10% | Estágio 0 + dimensão 1 do code-audit |
| Testes (cobertura, E2E, dim. 8) | 10% | — |
| Performance (Core Web Vitals reais) | 5% | thresholds acima |
| Acessibilidade (WCAG 2.2 AA) | 5% | — |
| Observabilidade + DevOps/CI-CD | 5% | métricas DORA — ver `metodologia.yaml` |

### Níveis de maturidade (não é só número)

```
Classe A   — nota ≥ 90 E zero bloqueante aberto (segurança/multi-tenant/LGPD)
Classe B   — nota ≥ 75, sem bloqueante aberto, mas dimensões abaixo do ideal
Classe C   — nota ≥ 50 OU algum bloqueante com aceitação formal de risco registrada
Reprovado  — qualquer bloqueante SEM aceitação formal, independente da nota
```

Um sistema com nota 95 e um CRITICAL de RLS ausente é **Reprovado**, não Classe A
com desconto. Segurança e isolamento de tenant não se compensam com nota alta em
outro lugar — é a mesma lógica do `devsecops:security-gate`.

### Relatório e histórico

Gere `docs/system-scan/SCAN-[data].md` com o veredito completo, e acrescente uma
linha a `docs/system-scan/historico.jsonl`:

```json
{"data":"2026-09-08","nota":78,"nivel":"Classe B","bloqueantes_abertos":0,"scan_anterior":"2026-06-01","delta_nota":6}
```

Na próxima execução, o Estágio 5 **lê essa linha** e reporta se o sistema
melhorou, piorou ou estagnou desde o último scan — sem histórico, cada auditoria
é uma opinião solta que não prova progresso nem regressão.

---

## Handover

> "System Scan concluído. Nível: **[Classe A/B/C/Reprovado]**, nota [X]/100
> ([+/-Y] desde o último scan em [data]).
> Bloqueantes abertos: [N] — [listar ou 'nenhum'].
> Relatório completo: `docs/system-scan/SCAN-[data].md`.
> Próximos passos priorizados: ver Estágio 5 do relatório."

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Decidir se pode continuar desenvolvendo sem refatorar antes | `intellix:code-audit` |
| Gate de segurança de um deploy específico (não do sistema inteiro) | `devsecops:security-gate` |
| Metodologia de segurança e classificação de severidade | `devsecops:security-baseline` |
| Dead code e migração de padrão legado | `deprecation-and-migration` |
| Refatorar arquitetura depois do diagnóstico | `mattpocock-skills:improve-codebase-architecture` |
| ADR para registrar decisão tomada durante o scan | `architecture-decision-records` |
| Verificação final antes de declarar pronto | `superpowers:verification-before-completion` |

---

## Armadilhas comuns

- Rodar o Estágio 0 (limpeza) e apagar código chamado dinamicamente (webhook,
  cron, string de rota) — sempre confirmar com o usuário antes de remover.
- Deixar o Estágio 4b sem `staging` real — Lighthouse contra `localhost` mede
  hardware da sua máquina, não a experiência real do usuário.
- Compensar bloqueante de segurança com nota alta em outra dimensão — a rubrica
  é desenhada para não permitir isso; não burle manualmente.
- Rodar o scan sem o histórico anterior e declarar "está ótimo" — sem
  comparação, você não sabe se está melhorando ou regredindo devagar.
