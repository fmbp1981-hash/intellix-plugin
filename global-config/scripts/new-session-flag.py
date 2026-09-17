# -*- coding: utf-8 -*-
"""
Hook SessionStart — Cria flag de nova sessão.
Sinaliza ao context-loader.py que a primeira mensagem desta sessão
deve receber o contexto do projeto automaticamente.

Também incrementa o session_count da sessão ativa (se existir)
para rastrear quantas sessões foram abertas para este projeto.
"""
import json
import sys
import os
import io
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

CLAUDE_DIR   = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions" / "active"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


# get_project_slug vive em _session_common.py desde 2026-09-07 (Fase 3.4).
# A versão anterior usava só o basename, então dois projetos chamados "api"
# compartilhavam o mesmo arquivo de estado. Ver docstring do módulo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _session_common import get_project_slug  # noqa: E402


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    cwd = os.getcwd()
    slug = get_project_slug(cwd)

    # Criar flag .new_session — consumida pela primeira mensagem via context-loader.py
    flag_file = SESSIONS_DIR / f"{slug}.new_session"
    flag_file.write_text(datetime.now().isoformat(), encoding="utf-8")

    # Incrementar session_count na sessão ativa (se houver)
    session_file = SESSIONS_DIR / f"{slug}.json"
    if session_file.exists():
        try:
            session = json.loads(session_file.read_text(encoding="utf-8"))
            session["session_count"] = session.get("session_count", 0) + 1
            session["last_activity"] = datetime.now().isoformat()
            session_file.write_text(
                json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    # Injetar mensagem de status no contexto do SessionStart
    project_name = Path(cwd).name
    print(f"\n🚀 Sessão iniciada — projeto: `{project_name}`")

    # Verificar se há contexto salvo para alertar o usuário
    memory_dir = (
        CLAUDE_DIR
        / "projects"
        / f"C--{cwd.replace(':', '').replace('/', '-').replace(chr(92), '-').strip('-')}"
        / "memory"
    )
    context_file = memory_dir / "session-context.md"
    if context_file.exists():
        print(
            f"   💾 Contexto anterior encontrado — será injetado na primeira mensagem.\n"
            f"   → Para retomar: basta enviar sua primeira mensagem normalmente.\n"
        )
    else:
        print(f"   ℹ️  Sem histórico anterior para este projeto.\n")


if __name__ == "__main__":
    main()
