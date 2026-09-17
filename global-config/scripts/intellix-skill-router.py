#!/usr/bin/env python3
# IntelliX Skill Router Hook
# UserPromptSubmit hook — lê o prompt via stdin e sugere as skills MAIS relevantes.
#
# Regra de ouro: sugerir 1-3 skills relevantes, nunca o catálogo inteiro.
# Uma lista de 15+ sugestões é ruído — o modelo ignora e o usuário perde confiança
# no roteador. Por isso este script pontua as regras e corta no top N.

from __future__ import annotations
import json
import sys
import re
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _session_common import is_subagent_call  # noqa: E402

_raw = sys.stdin.read()
try:
    _payload = json.loads(_raw)
except (json.JSONDecodeError, ValueError, TypeError):
    # Payload não é JSON (não deveria acontecer em produção) — trata o texto
    # bruto como prompt em vez de quebrar, mesma postura defensiva do resto
    # dos hooks (ver test_stdin_malformado_nao_quebra).
    _payload = {"prompt": _raw}

# Achado de 2026-09-16: antes disto o roteador varria o STDIN CRU inteiro —
# incluindo cwd/transcript_path/session_id — em vez de só o campo "prompt".
# Um projeto com "worktree" no caminho (ex: .claude-worktrees-...) disparava
# a sugestão de git-workflow-and-versioning mesmo sem o usuário ter dito nada
# sobre git. Também pula dentro de subagents: eles recebem um prompt de
# tarefa do orquestrador, não uma mensagem do usuário no fluxo IntelliX.
if is_subagent_call(_payload):
    sys.exit(0)

prompt = str(_payload.get("prompt", "")).lower()

MAX_SUGGESTIONS = 3

# ─────────────────────────────────────────────────────────────────────────────
# GATES DE WORKFLOW — sempre exibidos, fora do limite de sugestões.
# São avisos de processo (não skills), curtos e raros por design.
# ─────────────────────────────────────────────────────────────────────────────
GATES = [
    (
        r"writing.?plans|escrever.?plano|criar.?plano|gerar.?plano|montar.?plano"
        r"|plano de implementa[cç][aã]o|implementation plan|elaborar.?plano",
        "Apos writing-plans aprovado, o PROXIMO PASSO OBRIGATORIO e intellix:master-workflow.",
    ),
    (
        r"\bdeploy\b|colocar no ar|publicar em produ[cç][aã]o|wrangler deploy",
        "Deploy e manual: o usuario roda /intellix:deploy (a skill nao e invocavel pelo modelo). "
        "Antes, confirme Fase 07 concluida e devsecops:security-gate == PASS.",
    ),
    (
        r"subagent.?driven|inline.?execution|subagent driven development|executing.?plans"
        r"|escolho.?subagent|escolho.?inline|vou.?de.?subagent|prefiro.?inline",
        "Escolha de modo de execucao detectada. Verificar .intellix-phase antes de executar. "
        "Se nao existir ou for 'init': rodar intellix:project-kickoff primeiro.",
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# REGRAS DE SKILL — (peso, skill, regex, motivo)
#
# Peso 100 = fase estruturante do workflow IntelliX (raramente deve perder).
# Peso  50 = skill de domínio específico (frontend, security, testes...).
# Peso  20 = skill transversal, útil mas quase sempre secundária.
#
# IMPORTANTE: só liste aqui skills que REALMENTE existem e estão habilitadas.
# Skills removidas ou em plugins desabilitados geram sugestão morta — o modelo
# tenta invocar, falha, e o usuário perde tempo. Auditado em 2026-08-25.
# ─────────────────────────────────────────────────────────────────────────────
RULES = [
    # ── Fases estruturantes IntelliX (peso 100) ────────────────────────────
    (100, "intellix:master-workflow",
     r"criar sistema|novo sistema|criar aplica[cç][aã]o|nova aplica[cç][aã]o|novo app|criar app"
     r"|quero construir|vamos construir|nova feature|nova funcionalidade"
     r"|novo m[oó]dulo|desenvolver sistema|novo saas|criar saas"
     r"|projeto do zero|partir do zero|intellix:master-workflow|/intellix:new-project"
     r"|\b/spec\b|\b/break\b|\b/plan\b|\b/execute\b|epic.?workflow",
     "sistema/feature nova detectada — entrar pelo workflow oficial"),

    (100, "intellix:code-audit",
     r"auditar|c[oó]digo legado|d[ií]vida t[eé]cnica|technical debt"
     r"|projeto existente|sistema existente|sistema legado"
     r"|enquadrar no padr[aã]o|adaptar o projeto",
     "projeto existente — gap analysis antes de mexer"),

    (100, "intellix:project-kickoff",
     r"novo projeto|criar projeto|iniciar projeto|scaffolding|estrutura inicial"
     r"|projeto novo|setup do projeto",
     "scaffolding de projeto novo"),

    # ── Fases de domínio IntelliX (peso 50) ────────────────────────────────
    (50, "intellix:architecture",
     r"arquitetura|schema do banco|modelagem|\berd\b|repository|service layer"
     r"|api design|multi.?tenant|row level security|\brls\b",
     "decisão de arquitetura/schema"),

    (50, "intellix:frontend-design",
     r"criar tela|criar p[aá]gina|criar componente|design system|dashboard"
     r"|landing page|mobile.?first|shadcn|\bui\b|\bux\b|frontend",
     "trabalho de interface"),

    (50, "intellix:agent-creation",
     r"criar agente|agente de ia|chatbot|whatsapp bot|bot de atendimento"
     r"|gptmaker|gpt maker|agente inteligente",
     "criação de agente de IA"),

    (50, "intellix:dev-standards",
     r"padr[aã]o de c[oó]digo|naming convention|estrutura de componente"
     r"|server action|tanstack|react query|zustand",
     "padrões de implementação"),

    (50, "intellix:integration",
     r"evolution api|whatsapp|\bn8n\b|webhook|edge function"
     r"|anthropic sdk|openai sdk|api externa|realtime",
     "integração externa"),

    (50, "intellix:security-observability",
     r"seguran[cç]a|security|vulnerabilidade|rate limit|\bowasp\b|\blgpd\b"
     r"|observabilidade|monitoramento|\bcsp\b|\bcsrf\b",
     "segurança/observabilidade"),

    (50, "intellix:test-e2e",
     r"\bteste\b|\btestes\b|\be2e\b|playwright|vitest|cobertura|\bqa\b"
     r"|smoke test|stress test|regress[aã]o|\btdd\b",
     "estratégia de testes"),

    (50, "cloudflare",
     r"cloudflare|\bworkers\b|cloudflare pages|wrangler",
     "plataforma de deploy padrão (Cloudflare)"),

    (50, "intellix:project-handoff",
     r"documenta[cç][aã]o final|\breadme\b|handoff|finalizar projeto"
     r"|entregar para o cliente|documentar o sistema",
     "entrega/handoff"),

    (50, "intellix:live-chat",
     r"live chat|chat ao vivo|\binbox\b|omnichannel|webchat|helpdesk"
     r"|handoff humano|painel de atendimento",
     "sistema de chat ao vivo"),

    # ── Skills transversais (peso 20) — todas verificadas como existentes ──
    (20, "karpathy-guidelines",
     r"escrever c[oó]digo|come[cç]ar a codar|vamos implementar|preciso implementar",
     "implementação — Think Before Coding, Simplicity First"),

    (20, "impeccable:impeccable",
     r"\bpolish\b|polir|refinar visual|micro.?intera[cç][aã]o|motion design"
     r"|deixar mais bonito|redesign|design sem personalidade",
     "polish/craft de UI"),

    (20, "ui-design:design-system-patterns",
     r"design.?token|dark.?mode|tema escuro|theme.?switch|tailwind.?config"
     r"|css variable|criar tokens",
     "tokens e infraestrutura de design system"),

    (20, "accessibility",
     r"acessibilidade|accessibility|\bwcag\b|\ba11y\b|aria.?label"
     r"|screen.?reader|leitor de tela|contraste de cor",
     "conformidade WCAG"),

    (20, "seo",
     r"\bseo\b|metatag|meta tag|open graph|schema\.org|structured data"
     r"|sitemap|canonical|indexa[cç][aã]o",
     "SEO técnico"),

    (20, "git-workflow-and-versioning",
     r"\bcommit\b|\bbranch\b|\brebase\b|pull.?request|trunk.?based|worktree"
     r"|conventional.?commit|versionamento",
     "workflow git"),

    (20, "api-and-interface-design",
     r"api.?p[uú]blica|contract.?first|versionamento.?de.?api|swagger|openapi"
     r"|design.?de.?api|error.?semantics",
     "design de API pública"),

    (20, "context-engineering",
     r"claude\.md|agents\.md|context.?engineering|system.?prompt"
     r"|atualizar.?claude\.md|revisar.?claude\.md",
     "qualidade do contexto do agente"),

    (20, "ci-cd-and-automation",
     r"github.?actions|\.github/workflows|ci\.yml|quality.?gate"
     r"|branch.?protection|configurar.?ci",
     "pipeline CI/CD"),

    (20, "shipping-and-launch",
     r"go.?live|staged.?rollout|rollout.?gradual|canary.?release"
     r"|blue.?green.?deploy|primeiro.?deploy.?produ[cç][aã]o",
     "go-live com rollout gradual"),

    (20, "deprecation-and-migration",
     r"deprec\w*|strangler|c[oó]digo.?morto|dead.?code"
     r"|substituir.?biblioteca|migrar.?de.+para|breaking.?change",
     "migração / remoção de legado"),

    (20, "doubt-driven-development",
     r"n[aã]o tenho certeza|d[uú]vida t[eé]cnica|qual.?a.?melhor.?forma"
     r"|risco t[eé]cnico|antes de implementar|melhor.?abordagem",
     "incerteza técnica — mapear antes de codar"),

    (20, "browser-testing-with-devtools",
     r"devtools|inspecionar.?request|network.?panel|console.?error"
     r"|debugar.?no.?chrome|breakpoint",
     "debug visual no browser"),
]

# ─────────────────────────────────────────────────────────────────────────────
# Execução
# ─────────────────────────────────────────────────────────────────────────────
for pattern, message in GATES:
    if re.search(pattern, prompt):
        print(f"[INTELLIX] ATENCAO: {message}")

matches = [
    (weight, skill, reason)
    for weight, skill, pattern, reason in RULES
    if re.search(pattern, prompt)
]

# Ordena por peso decrescente; empate mantém a ordem de declaração (fases antes
# de transversais), que é a ordem natural do workflow.
matches.sort(key=lambda m: -m[0])

for _, skill, reason in matches[:MAX_SUGGESTIONS]:
    print(f"[SKILL] RECOMENDADO: {skill} — {reason}")

if len(matches) > MAX_SUGGESTIONS:
    extras = ", ".join(skill for _, skill, _ in matches[MAX_SUGGESTIONS:])
    print(f"[SKILL] (tambem relevantes, use se fizer sentido: {extras})")

# Context7 é um lembrete de ferramenta, não uma skill — fica fora do limite.
if re.search(
    r"next\.?js|supabase|tailwind|shadcn|\bmotion\b|zod\b|tanstack|react.?hook.?form"
    r"|anthropic sdk|openai sdk|evolution.?api|\bn8n\b|vercel\b"
    r"|vers[aã]o atual|breaking change|migrar para"
    r"|app router|server action|server component|route handler",
    prompt,
):
    print(
        "[CONTEXT7] Use `resolve-library-id` + `query-docs` para obter a "
        "documentacao/versao atual antes de escrever codigo com esta biblioteca."
    )

sys.exit(0)
