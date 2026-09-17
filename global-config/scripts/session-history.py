# -*- coding: utf-8 -*-
"""
Hook Stop — Salva histórico completo da sessão.
Ao encerrar qualquer sessão Claude Code:
  1. Salva .md em ~/.claude/history/YYYY/MM/DD-{projeto}-{session_id}.md
  2. Atualiza ~/.claude/history/index.md (uma linha por sessão, grep-ável)
  3. Atualiza context.md do projeto (para retomada rápida)
  4. Notifica via WhatsApp (Evolution API) se configurado
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

CLAUDE_DIR   = Path.home() / ".claude"
HISTORY_DIR  = CLAUDE_DIR / "history"
SESSIONS_DIR = CLAUDE_DIR / "sessions" / "active"
INDEX_FILE   = HISTORY_DIR / "index.md"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# get_project_slug vive em _session_common.py desde 2026-09-07 (Fase 3.4).
# A versão anterior usava só o basename, então dois projetos chamados "api"
# compartilhavam o mesmo arquivo de estado. Ver docstring do módulo.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _session_common import get_project_slug  # noqa: E402


def load_active_session(slug: str) -> dict | None:
    session_file = SESSIONS_DIR / f"{slug}.json"
    if session_file.exists():
        try:
            return json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def clear_active_session(slug: str):
    """Limpa a sessão ativa após salvar (próxima sessão começa do zero para tracking)."""
    session_file = SESSIONS_DIR / f"{slug}.json"
    if session_file.exists():
        session_file.unlink()


def build_session_md(session: dict, session_id: str, cwd: str) -> str:
    """Gera o .md completo da sessão para salvar no histórico."""
    now = datetime.now()
    project = session.get("project", Path(cwd).name)
    phase = session.get("intellix_phase", "—")
    started = session.get("started_at", now.isoformat())
    focus = session.get("current_focus", "Não especificado")

    files_created = session.get("files_created", [])
    files_modified = session.get("files_modified", [])
    tasks_completed = session.get("tasks_completed", [])
    tasks_pending = session.get("tasks_pending", [])
    decisions = session.get("key_decisions", [])

    lines = [
        f"# Sessão {project} — {now.strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"| Campo | Valor |",
        f"|---|---|",
        f"| **Projeto** | `{project}` |",
        f"| **Path** | `{cwd}` |",
        f"| **Session ID** | `{session_id[:8]}...` |",
        f"| **Fase IntelliX** | `{phase}` |",
        f"| **Iniciada em** | {started} |",
        f"| **Encerrada em** | {now.isoformat()} |",
        f"",
        f"## Foco da Sessão",
        f"",
        f"{focus}",
        f"",
    ]

    if files_created:
        lines += [f"## Arquivos Criados ({len(files_created)})", ""]
        for f in files_created:
            lines.append(f"- `{f['file']}` ({f['at']})")
        lines.append("")

    if files_modified:
        lines += [f"## Arquivos Modificados ({len(files_modified)})", ""]
        for f in files_modified:
            lines.append(f"- `{f['file']}` ({f['at']})")
        lines.append("")

    if tasks_completed:
        lines += ["## Tarefas Concluídas", ""]
        for t in tasks_completed:
            lines.append(f"- [x] {t}")
        lines.append("")

    if tasks_pending:
        lines += ["## ⏳ Pendências (retomar aqui)", ""]
        for t in tasks_pending:
            lines.append(f"- [ ] {t}")
        lines.append("")

    if decisions:
        lines += ["## Decisões Técnicas", ""]
        for d in decisions:
            lines.append(f"- {d}")
        lines.append("")

    lines += [
        "## Como Retomar",
        "",
        "```",
        f"cd {cwd}",
        f"# Fase atual: {phase}",
    ]
    if tasks_pending:
        lines.append(f"# Próximo passo: {tasks_pending[0]}")
    lines += ["```", ""]

    return "\n".join(lines)


def update_index(session: dict, session_id: str, cwd: str, history_path: Path):
    """Atualiza o index.md com uma linha por sessão (grep-ável)."""
    now = datetime.now()
    project = session.get("project", Path(cwd).name)
    phase = session.get("intellix_phase", "—")
    n_files = len(session.get("files_created", [])) + len(session.get("files_modified", []))
    pending = len(session.get("tasks_pending", []))
    focus = session.get("current_focus", "")[:60] if session.get("current_focus") else ""

    line = (
        f"| {now.strftime('%Y-%m-%d %H:%M')} "
        f"| [{project}]({history_path.name}) "
        f"| `{phase}` "
        f"| {n_files} arquivos "
        f"| {pending} pendências "
        f"| {focus} |"
    )

    if not INDEX_FILE.exists():
        header = (
            "# IntelliX Session Index\n\n"
            "> Histórico grep-ável de todas as sessões. "
            "Use: `grep 'nome-projeto' index.md`\n\n"
            "| Data/Hora | Projeto | Fase | Arquivos | Pendências | Foco |\n"
            "|---|---|---|---|---|---|\n"
        )
        INDEX_FILE.write_text(header, encoding="utf-8")

    with open(INDEX_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def update_project_context(session: dict, cwd: str):
    """
    Atualiza o context.md do projeto — este é o arquivo lido na próxima sessão
    para retomar exatamente de onde parou.
    """
    project_slug = get_project_slug(cwd)
    context_dir = CLAUDE_DIR / "projects" / f"C--{cwd.replace(':', '').replace('/', '-').replace(chr(92), '-').strip('-')}" / "memory"
    context_dir.mkdir(parents=True, exist_ok=True)

    context_file = context_dir / "session-context.md"
    now = datetime.now()

    phase = session.get("intellix_phase", "—")
    tasks_pending = session.get("tasks_pending", [])
    tasks_completed = session.get("tasks_completed", [])
    files_created = session.get("files_created", [])
    files_modified = session.get("files_modified", [])
    decisions = session.get("key_decisions", [])
    focus = session.get("current_focus", "")

    content = f"""---
name: session-context
description: Contexto da última sessão — carregado automaticamente para retomar o trabalho
type: project
---

# Contexto da Última Sessão — {project_slug}

**Última atualização:** {now.strftime('%Y-%m-%d %H:%M')}
**Fase IntelliX:** `{phase}`

## Foco da Última Sessão
{focus or 'Não registrado'}

## ⏳ Pendências — Retomar Aqui
{"".join(f'- [ ] {t}' + chr(10) for t in tasks_pending) if tasks_pending else '- Nenhuma pendência registrada'}

## ✅ Concluído na Última Sessão
{"".join(f'- [x] {t}' + chr(10) for t in tasks_completed) if tasks_completed else '- Não registrado'}

## Arquivos Tocados
{"".join(f'- `{f["file"]}`' + chr(10) for f in files_created + files_modified) if files_created or files_modified else '- Nenhum arquivo rastreado'}

## Decisões Técnicas Registradas
{"".join(f'- {d}' + chr(10) for d in decisions) if decisions else '- Nenhuma decisão registrada'}

## Como Retomar
```
cd {cwd}
# 1. Ler este arquivo para ter contexto
# 2. Verificar .intellix-phase: {phase}
# 3. Próximo passo: {tasks_pending[0] if tasks_pending else 'definir na sessão'}
```
"""

    context_file.write_text(content, encoding="utf-8")


def notify_whatsapp(session: dict, cwd: str):
    """
    Notifica via Evolution API (WhatsApp) ao encerrar sessão.
    Ativa apenas se EVOLUTION_API_URL e EVOLUTION_NOTIFY_NUMBER estiverem configurados.
    """
    evolution_url = os.environ.get("EVOLUTION_API_URL")
    evolution_key = os.environ.get("EVOLUTION_API_KEY")
    evolution_instance = os.environ.get("EVOLUTION_DEFAULT_INSTANCE")
    notify_number = os.environ.get("EVOLUTION_NOTIFY_NUMBER")  # ex: 5511999999999

    if not all([evolution_url, evolution_key, evolution_instance, notify_number]):
        return  # Silencioso se não configurado

    try:
        import urllib.request

        project = session.get("project", Path(cwd).name)
        phase = session.get("intellix_phase", "—")
        n_created = len(session.get("files_created", []))
        n_modified = len(session.get("files_modified", []))
        pending = session.get("tasks_pending", [])
        now = datetime.now().strftime("%H:%M")

        msg_lines = [
            f"🤖 *IntelliX Session encerrada* — {now}",
            f"📁 Projeto: `{project}`",
            f"🔖 Fase: `{phase}`",
            f"📝 Arquivos: {n_created} criados, {n_modified} modificados",
        ]
        if pending:
            msg_lines.append(f"⏳ Pendências: {len(pending)}")
            msg_lines.append(f"   → {pending[0]}")

        msg = "\n".join(msg_lines)

        payload = json.dumps({
            "number": notify_number,
            "text": msg,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{evolution_url}/message/sendText/{evolution_instance}",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "apikey": evolution_key,
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Nunca falhar silenciosamente no hook Stop


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    session_id = data.get("session_id", datetime.now().strftime("%Y%m%d%H%M%S"))
    cwd = os.getcwd()
    slug = get_project_slug(cwd)

    session = load_active_session(slug)
    if not session:
        sys.exit(0)  # Sem sessão ativa rastreada, nada a fazer

    # 1. Gerar conteúdo .md da sessão
    session_md = build_session_md(session, session_id, cwd)

    # 2. Salvar em ~/.claude/history/YYYY/MM/DD-{slug}-{session_id_short}.md
    now = datetime.now()
    date_dir = HISTORY_DIR / now.strftime("%Y") / now.strftime("%m")
    date_dir.mkdir(parents=True, exist_ok=True)
    history_file = date_dir / f"{now.strftime('%d')}-{slug}-{session_id[:6]}.md"
    history_file.write_text(session_md, encoding="utf-8")

    # 3. Atualizar index.md
    update_index(session, session_id, cwd, history_file)

    # 4. Atualizar context.md do projeto (para retomada)
    update_project_context(session, cwd)

    # 5. Notificar WhatsApp (silencioso se não configurado)
    notify_whatsapp(session, cwd)

    # 6. Limpar sessão ativa (próxima sessão começa limpa para tracking)
    clear_active_session(slug)

    # 7. Resetar contador de contexto (nova sessao comeca do zero)
    counter_file = SESSIONS_DIR / f"{slug}-ctx-counter.json"
    if counter_file.exists():
        counter_file.write_text(chr(123)+chr(34)+chr(99)+chr(111)+chr(117)+chr(110)+chr(116)+chr(34)+chr(58)+chr(32)+chr(48)+chr(44)+chr(32)+chr(34)+chr(119)+chr(97)+chr(114)+chr(110)+chr(101)+chr(100)+chr(34)+chr(58)+chr(32)+chr(102)+chr(97)+chr(108)+chr(115)+chr(101)+chr(44)+chr(32)+chr(34)+chr(115)+chr(105)+chr(110)+chr(99)+chr(101)+chr(95)+chr(119)+chr(97)+chr(114)+chr(110)+chr(34)+chr(58)+chr(32)+chr(48)+chr(125), encoding="utf-8")

    print(f"\n✅ Sessão salva: {history_file.name}\n   → Use 'context-loader' na próxima sessão para retomar.\n")


if __name__ == "__main__":
    main()