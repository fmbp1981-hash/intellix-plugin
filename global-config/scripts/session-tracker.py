# -*- coding: utf-8 -*-
"""
Hook PostToolUse (Edit/Write) — Rastreia arquivos modificados durante a sessão.
Mantém um arquivo de sessão ativa por projeto para reconstruir contexto se a sessão cair.
"""
from __future__ import annotations
import json
import sys
import os
import io
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

CLAUDE_DIR = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions" / "active"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


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
    return {
        "project": slug,
        "project_path": os.getcwd(),
        "started_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
        "intellix_phase": None,
        "files_modified": [],
        "files_created": [],
        "tasks_completed": [],
        "tasks_pending": [],
        "key_decisions": [],
        "current_focus": None,
        "session_count": 0,
    }


def save_active_session(slug: str, session: dict):
    session_file = SESSIONS_DIR / f"{slug}.json"
    session["last_activity"] = datetime.now().isoformat()
    session_file.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")


def read_intellix_phase(cwd: str) -> str | None:
    phase_file = Path(cwd) / ".intellix-phase"
    if phase_file.exists():
        return phase_file.read_text(encoding="utf-8").strip()
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Só rastrear Edit e Write
    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    cwd = os.getcwd()
    slug = get_project_slug(cwd)
    session = load_active_session(slug)

    # Atualizar fase IntelliX
    phase = read_intellix_phase(cwd)
    if phase:
        session["intellix_phase"] = phase

    # Registrar arquivo modificado/criado
    file_path = tool_input.get("file_path", "")
    if file_path:
        # Tornar path relativo ao projeto se possível
        try:
            rel_path = str(Path(file_path).relative_to(cwd))
        except ValueError:
            rel_path = file_path

        entry = {
            "file": rel_path,
            "at": datetime.now().strftime("%H:%M"),
            "tool": tool_name,
        }

        if tool_name == "Write":
            if rel_path not in [f["file"] for f in session["files_created"]]:
                session["files_created"].append(entry)
        else:
            # Evitar duplicatas, atualizar timestamp
            existing = [f for f in session["files_modified"] if f["file"] == rel_path]
            if existing:
                existing[0]["at"] = entry["at"]
            else:
                session["files_modified"].append(entry)

    save_active_session(slug, session)


if __name__ == "__main__":
    main()
