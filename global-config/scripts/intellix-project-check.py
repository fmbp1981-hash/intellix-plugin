#!/usr/bin/env python3
# IntelliX Project Structure Check — SessionStart hook
# Verifica se o projeto atual segue os padroes IntelliX.
# Repete o aviso a cada sessao enquanto houver gaps.

import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CWD = os.getcwd()
PROJECT_NAME = os.path.basename(CWD)

# Ignorar diretorios que claramente nao sao projetos de desenvolvimento
IGNORE_DIRS = {
    "System32", "Windows", "Program Files", "Program Files (x86)",
    "Users", "AppData", "Temp", ".claude", "scripts"
}
if PROJECT_NAME in IGNORE_DIRS or CWD == os.path.expanduser("~"):
    sys.exit(0)

# So roda em diretorios que tem indicadores de projeto
HAS_PACKAGE_JSON  = os.path.isfile(os.path.join(CWD, "package.json"))
HAS_PYPROJECT     = os.path.isfile(os.path.join(CWD, "pyproject.toml"))
HAS_GO_MOD        = os.path.isfile(os.path.join(CWD, "go.mod"))
HAS_CARGO         = os.path.isfile(os.path.join(CWD, "Cargo.toml"))
HAS_SRC           = os.path.isdir(os.path.join(CWD, "src"))
HAS_APP           = os.path.isdir(os.path.join(CWD, "app"))

IS_PROJECT = HAS_PACKAGE_JSON or HAS_PYPROJECT or HAS_GO_MOD or HAS_CARGO

if not IS_PROJECT:
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
# Verificar fase atual (se ja foi inicializado pelo IntelliX)
# ─────────────────────────────────────────────────────────────────────────────
PHASE_FILE = os.path.join(CWD, ".intellix-phase")
current_phase = None
if os.path.isfile(PHASE_FILE):
    with open(PHASE_FILE, "r", encoding="utf-8") as f:
        current_phase = f.read().strip()

# Se o projeto ja esta em fase avancada, so reportar OK
if current_phase and current_phase not in ("", "init"):
    print(f"[INTELLIX] Projeto '{PROJECT_NAME}' — fase atual: {current_phase} (rastreado pelo IntelliX)")
    sys.exit(0)

# ─────────────────────────────────────────────────────────────────────────────
# Checklist de conformidade IntelliX
# ─────────────────────────────────────────────────────────────────────────────
gaps = []

# 1. Marcador de fase IntelliX
if not os.path.isfile(PHASE_FILE):
    gaps.append(".intellix-phase ausente — projeto nao rastreado pelo IntelliX Plugin")

# 2. MASTER-ARCHITECTURE.md (fonte unica de verdade)
if not os.path.isfile(os.path.join(CWD, "MASTER-ARCHITECTURE.md")):
    gaps.append("MASTER-ARCHITECTURE.md ausente — regras de arquitetura nao definidas")

# 3. references/ com arquivos minimos
refs_dir = os.path.join(CWD, "references")
if not os.path.isdir(refs_dir):
    gaps.append("references/ ausente — sem architecture.md, DESIGN.md, workflow.md")
else:
    missing_refs = []
    for ref in ["architecture.md", "DESIGN.md"]:
        if not os.path.isfile(os.path.join(refs_dir, ref)):
            missing_refs.append(ref)
    if missing_refs:
        gaps.append(f"references/ incompleto — faltam: {', '.join(missing_refs)}")

# 4. .claude/rules/ (convencoes especificas deste projeto)
#    NOTA (2026-09-07): NAO verificar .claude/agents/ nem .claude/skills/ por projeto.
#    Decisao de arquitetura: agents e skills ficam SOMENTE na camada global
#    (~/.claude + plugins) e sao invocados por referencia. Copiar para dentro do
#    repositorio cria fork congelado da metodologia que nunca recebe correcao.
#    Ver skills/project-kickoff/SKILL.md secao "O que NAO vai para dentro do projeto".
rules_dir = os.path.join(CWD, ".claude", "rules")
if not os.path.isdir(rules_dir):
    gaps.append(".claude/rules/ ausente — convencoes especificas do projeto nao documentadas")

# 5. Estrutura de camadas (src/)
src_dir = os.path.join(CWD, "src")
if os.path.isdir(src_dir):
    EXPECTED_LAYERS = {
        "repositories": "Data Access Layer — acesso ao banco",
        "services":     "Business Logic Layer — regras de negocio",
        "types":        "Tipos TypeScript centralizados",
        "validations":  "Zod schemas — validacao de inputs",
    }
    for folder, desc in EXPECTED_LAYERS.items():
        if not os.path.isdir(os.path.join(src_dir, folder)):
            gaps.append(f"src/{folder}/ ausente — {desc}")
else:
    # Projeto Next.js pode usar app/ com estrutura diferente
    if HAS_APP:
        # Aceitar estrutura app/ — verificar apenas lib/
        lib_dir = os.path.join(CWD, "lib")
        if not os.path.isdir(lib_dir):
            gaps.append("lib/ ausente — sem contratos, queries e utilities compartilhadas")

# 6. CLAUDE.md do projeto (contexto especifico) — raiz ou .claude/, ambos validos
has_claude_md = (
    os.path.isfile(os.path.join(CWD, "CLAUDE.md"))
    or os.path.isfile(os.path.join(CWD, ".claude", "CLAUDE.md"))
)
if not has_claude_md:
    gaps.append("CLAUDE.md ausente — sem contexto especifico do projeto para o Claude")

# 7. Vazamento de contexto local: CLAUDE.local.md fora do .gitignore
local_md = os.path.join(CWD, "CLAUDE.local.md")
gitignore = os.path.join(CWD, ".gitignore")
if os.path.isfile(local_md):
    ignored = False
    if os.path.isfile(gitignore):
        try:
            with open(gitignore, "r", encoding="utf-8", errors="ignore") as f:
                ignored = "CLAUDE.local.md" in f.read()
        except OSError:
            pass
    if not ignored:
        gaps.append("CLAUDE.local.md NAO esta no .gitignore — contexto local vaza para o repositorio")

# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────
if not gaps:
    print(f"[INTELLIX] Projeto '{PROJECT_NAME}': estrutura OK — segue os padroes IntelliX.")
    sys.exit(0)

SCORE = max(0, 100 - (len(gaps) * 14))

print(f"")
print(f"[INTELLIX-CHECK] Projeto: {PROJECT_NAME} | Score: {SCORE}/100 | {len(gaps)} gap(s) encontrado(s)")
print(f"[INTELLIX-CHECK] Gaps de conformidade com o IntelliX Plugin:")
for i, gap in enumerate(gaps, 1):
    print(f"  {i}. {gap}")
print(f"")
print(f"[INTELLIX-CHECK] ACAO REQUERIDA: Pergunte ao usuario:")
print(f"  'O projeto {PROJECT_NAME} tem {len(gaps)} gap(s) em relacao ao padrao IntelliX.")
print(f"   Deseja adaptar agora (intellix:project-kickoff) ou continuar sem adaptar?'")
print(f"[INTELLIX-CHECK] Repete a cada sessao enquanto o projeto nao seguir os padroes.")
print(f"")

sys.exit(0)
