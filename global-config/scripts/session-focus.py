# -*- coding: utf-8 -*-
"""
Helper — Atualiza o foco, tarefas e decisões da sessão ativa.
Chamado pelo Claude durante a sessão para registrar progresso.

Uso:
  python session-focus.py [opções]

Opções:
  --focus "texto"       Define o foco atual da sessão
  --done "tarefa"       Marca tarefa como concluída (pode repetir)
  --pending "tarefa"    Adiciona tarefa pendente (pode repetir)
  --decision "texto"    Registra decisão técnica (pode repetir)
  --phase "fase"        Atualiza a fase IntelliX (ex: "Fase 03 - Frontend")
  --show                Exibe resumo do estado atual da sessão
  --reset-pending       Limpa todas as pendências atuais

Exemplos:
  python session-focus.py --focus "Implementando autenticação OAuth"
  python session-focus.py --done "Schema do banco criado" --pending "Configurar RLS"
  python session-focus.py --decision "Usar Supabase Auth em vez de custom JWT"
  python session-focus.py --show
"""
import json
import sys
import os
import io
import argparse
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
    session_file.write_text(
        json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def show_session(session: dict):
    print("\n" + "─" * 60)
    print(f"📋 SESSÃO ATIVA: {session.get('project', '—')}")
    print("─" * 60)

    phase = session.get("intellix_phase") or "—"
    print(f"🔖 Fase IntelliX: {phase}")

    focus = session.get("current_focus") or "Não definido"
    print(f"🎯 Foco atual: {focus}")

    started = session.get("started_at", "")[:16].replace("T", " ")
    print(f"🕐 Iniciada em: {started}")

    pending = session.get("tasks_pending", [])
    if pending:
        print(f"\n⏳ Pendências ({len(pending)}):")
        for t in pending:
            print(f"  - [ ] {t}")

    done = session.get("tasks_completed", [])
    if done:
        print(f"\n✅ Concluídas ({len(done)}):")
        for t in done[-5:]:  # Últimas 5
            print(f"  - [x] {t}")

    decisions = session.get("key_decisions", [])
    if decisions:
        print(f"\n⚙️ Decisões técnicas ({len(decisions)}):")
        for d in decisions[-3:]:  # Últimas 3
            print(f"  - {d}")

    n_created = len(session.get("files_created", []))
    n_modified = len(session.get("files_modified", []))
    print(f"\n📁 Arquivos: {n_created} criados, {n_modified} modificados")
    print("─" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Atualiza foco e progresso da sessão ativa do Claude Code"
    )
    parser.add_argument("--focus", type=str, help="Define o foco atual da sessão")
    parser.add_argument(
        "--done",
        type=str,
        action="append",
        default=[],
        help="Marca tarefa como concluída",
    )
    parser.add_argument(
        "--pending",
        type=str,
        action="append",
        default=[],
        help="Adiciona tarefa pendente",
    )
    parser.add_argument(
        "--decision",
        type=str,
        action="append",
        default=[],
        help="Registra decisão técnica",
    )
    parser.add_argument("--phase", type=str, help="Atualiza a fase IntelliX")
    parser.add_argument(
        "--reset-pending",
        action="store_true",
        help="Limpa todas as pendências atuais",
    )
    parser.add_argument(
        "--show", action="store_true", help="Exibe resumo da sessão atual"
    )

    args = parser.parse_args()

    cwd = os.getcwd()
    slug = get_project_slug(cwd)
    session = load_active_session(slug)

    # Modo leitura apenas
    if args.show:
        show_session(session)
        return

    changed = False

    if args.focus:
        session["current_focus"] = args.focus
        print(f"🎯 Foco atualizado: {args.focus}")
        changed = True

    if args.phase:
        session["intellix_phase"] = args.phase
        print(f"🔖 Fase atualizada: {args.phase}")
        changed = True

    if args.reset_pending:
        session["tasks_pending"] = []
        print("🗑️  Pendências limpas.")
        changed = True

    for task in args.done:
        if task not in session["tasks_completed"]:
            session["tasks_completed"].append(task)
            # Remover das pendências se estava lá
            session["tasks_pending"] = [
                t for t in session["tasks_pending"] if t != task
            ]
            print(f"✅ Concluída: {task}")
            changed = True

    for task in args.pending:
        if task not in session["tasks_pending"]:
            session["tasks_pending"].append(task)
            print(f"⏳ Pendência adicionada: {task}")
            changed = True

    for decision in args.decision:
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"[{timestamp}] {decision}"
        if decision not in session["key_decisions"]:
            session["key_decisions"].append(entry)
            print(f"⚙️  Decisão registrada: {decision}")
            changed = True

    if changed:
        save_active_session(slug, session)
        print(f"\n💾 Sessão '{slug}' salva.")
    elif not args.show:
        print("ℹ️  Nenhuma alteração. Use --show para ver o estado atual.")


if __name__ == "__main__":
    main()
