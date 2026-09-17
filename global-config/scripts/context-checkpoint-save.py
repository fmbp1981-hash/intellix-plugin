# -*- coding: utf-8 -*-
"""
Salva um checkpoint detalhado do contexto atual da sessao.
Chamado pelo skill context-checkpoint antes de limpar o contexto com /clear.

O arquivo gerado (context-checkpoint.md) e lido com PRIORIDADE
na proxima sessao pelo context-loader.py.

Uso:
  python context-checkpoint-save.py \
    --focus "tarefa atual e contexto completo" \
    --pending "primeiro proximo passo concreto" \
    --done "o que foi concluido" \
    --decision "decisao tecnica relevante"
"""
import json
import sys
import os
import io
import argparse
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

CLAUDE_DIR = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions" / "active"


def get_project_memory_dir(cwd: str) -> Path:
    slug = "C--" + cwd.replace(":", "").replace("/", "-").replace("\\", "-").strip("-")
    return CLAUDE_DIR / "projects" / slug / "memory"


# get_project_slug vive em _session_common.py desde 2026-09-07 (Fase 3.4).
# A versão anterior usava só o basename, então dois projetos chamados "api"
# compartilhavam o mesmo arquivo de estado. Ver docstring do módulo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _session_common import get_project_slug  # noqa: E402


def load_active_session(slug: str) -> dict:
    session_file = SESSIONS_DIR / f"{slug}.json"
    if session_file.exists():
        try:
            return json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def reset_counter(slug: str):
    counter_file = SESSIONS_DIR / f"{slug}-ctx-counter.json"
    if counter_file.exists():
        counter_file.write_text(
            json.dumps({"count": 0, "warned": False, "since_warn": 0})
        )


def main():
    parser = argparse.ArgumentParser(description="Salva checkpoint de contexto")
    parser.add_argument("--focus", default="", help="Tarefa atual e contexto")
    parser.add_argument("--pending", action="append", default=[], help="Proximo passo (repetivel)")
    parser.add_argument("--done", action="append", default=[], help="O que foi concluido (repetivel)")
    parser.add_argument("--decision", action="append", default=[], help="Decisao tecnica (repetivel)")
    args = parser.parse_args()

    cwd = os.getcwd()
    slug = get_project_slug(cwd)
    memory_dir = get_project_memory_dir(cwd)
    memory_dir.mkdir(parents=True, exist_ok=True)

    session = load_active_session(slug)
    now = datetime.now()

    # Mesclar pendencias: args + sessao ativa (args tem prioridade, no topo)
    pending = list(args.pending)
    for p in session.get("tasks_pending", []):
        if p not in pending:
            pending.append(p)

    completed = list(args.done)
    for d in session.get("tasks_completed", []):
        if d not in completed:
            completed.append(d)

    decisions = []
    for dec in args.decision:
        decisions.append(f"[{now.strftime('%H:%M')}] {dec}")
    for d in session.get("key_decisions", []):
        if d not in decisions:
            decisions.append(d)

    phase = session.get("intellix_phase", "nao definida")
    focus = args.focus or session.get("current_focus", "nao registrado")
    files_created = session.get("files_created", [])
    files_modified = session.get("files_modified", [])

    pending_md = "".join(f"- [ ] {t}\n" for t in pending) if pending else "- Nenhuma pendencia registrada\n"
    completed_md = "".join(f"- [x] {t}\n" for t in completed) if completed else "- Nenhum concluido registrado\n"
    files_md = "".join(f"- `{f['file']}`\n" for f in files_created + files_modified) if (files_created or files_modified) else "- Nenhum arquivo rastreado\n"
    decisions_md = "".join(f"- {d}\n" for d in decisions) if decisions else "- Nenhuma decisao registrada\n"
    next_step = pending[0] if pending else "definir na sessao"

    content = f"""---
name: context-checkpoint
description: Checkpoint gerado por limpeza de contexto -- retomada automatica na proxima sessao
type: project
checkpoint: true
---

# Checkpoint de Contexto -- {slug}

**Gerado em:** {now.strftime('%Y-%m-%d %H:%M')}
**Tipo:** CHECKPOINT (context clear intencional)
**Fase IntelliX:** `{phase}`

## Foco da Ultima Sessao
{focus}

## Pendencias -- Retomar Aqui
{pending_md}
## Concluido na Ultima Sessao
{completed_md}
## Arquivos Tocados
{files_md}
## Decisoes Tecnicas Registradas
{decisions_md}
## Como Retomar
```
cd {cwd}
# Fase: {phase}
# Proximo passo: {next_step}
```
"""

    checkpoint_file = memory_dir / "context-checkpoint.md"
    checkpoint_file.write_text(content, encoding="utf-8")

    # Resetar contador para a proxima sessao comecar do zero
    reset_counter(slug)

    print(f"Checkpoint salvo: {checkpoint_file}")
    print(f"  Pendencias: {len(pending)}")
    print(f"  Arquivos rastreados: {len(files_created) + len(files_modified)}")
    print(f"  Fase: {phase}")
    print()
    print("Agora execute /clear para limpar o contexto.")
    print("O checkpoint sera restaurado automaticamente na primeira mensagem da nova sessao.")


if __name__ == "__main__":
    main()
