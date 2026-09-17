# -*- coding: utf-8 -*-
"""
Hook PostToolUse (todos os tools) — Monitor de janela de contexto.

Conta tool calls como proxy de uso do contexto.
Ao atingir o threshold, injeta alerta obrigando Claude a salvar checkpoint.

Threshold padrao: 40 tool calls -> 1 aviso
Avisos subsequentes: a cada 15 tool calls apos o 1
"""
import json
import sys
import os
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

CLAUDE_DIR = Path.home() / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions" / "active"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

THRESHOLD = int(os.environ.get("CONTEXT_MONITOR_THRESHOLD", "40"))
REPEAT_EVERY = int(os.environ.get("CONTEXT_MONITOR_REPEAT", "15"))


# get_project_slug vive em _session_common.py desde 2026-09-07 (Fase 3.4).
# A versão anterior usava só o basename, então dois projetos chamados "api"
# compartilhavam o mesmo arquivo de estado. Ver docstring do módulo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _session_common import get_project_slug, is_subagent_call  # noqa: E402


def counter_path(slug: str) -> Path:
    return SESSIONS_DIR / f"{slug}-ctx-counter.json"


def load_counter(slug: str) -> dict:
    f = counter_path(slug)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"count": 0, "warned": False, "since_warn": 0}


def save_counter(slug: str, data: dict):
    counter_path(slug).write_text(json.dumps(data), encoding="utf-8")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # Subagents (Task/Agent) têm orçamento de contexto próprio — não contam
    # para o limite do thread principal. Ver docstring de is_subagent_call.
    if is_subagent_call(data):
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if not tool_name:
        sys.exit(0)

    cwd = os.getcwd()
    slug = get_project_slug(cwd)
    counter = load_counter(slug)

    counter["count"] += 1
    if counter["warned"]:
        counter["since_warn"] += 1

    should_warn = False
    if not counter["warned"] and counter["count"] >= THRESHOLD:
        should_warn = True
        counter["warned"] = True
        counter["since_warn"] = 0
    elif counter["warned"] and counter["since_warn"] >= REPEAT_EVERY:
        should_warn = True
        counter["since_warn"] = 0

    save_counter(slug, counter)

    if should_warn:
        total = counter["count"]
        msg = (
            f"\n CONTEXT-MONITOR: {total} tool calls nesta sessao "
            f"(threshold={THRESHOLD}) -- contexto possivelmente acima de 50%.\n"
            f"ACAO OBRIGATORIA: invoque a skill `context-checkpoint` AGORA.\n"
            f"Ela salva o estado completo e instrui como retomar apos /clear.\n"
            f"NAO continue respondendo sem antes executar o checkpoint.\n"
        )
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": msg,
            }
        }
        print(json.dumps(output, ensure_ascii=False))

    sys.exit(0)


if __name__ == "__main__":
    main()
