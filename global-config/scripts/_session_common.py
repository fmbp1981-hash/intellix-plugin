# -*- coding: utf-8 -*-
"""
_session_common.py — identidade de projeto e escrita concorrente segura.

Criado em 2026-09-07 (Fase 3.4 do PLANO-CORRECAO-2026-09-07.md), a partir do
achado C6 da auditoria.

DOIS DEFEITOS QUE ISTO CORRIGE

1. COLISÃO DE IDENTIDADE
   `get_project_slug()` estava duplicada em 6 scripts, todas usando só
   `Path(cwd).name` — o nome da pasta. Dois clientes com um projeto chamado
   `api`, `frontend` ou `app` compartilhavam o MESMO arquivo de estado em
   `sessions/active/<slug>.json`: o foco de um sobrescrevia o do outro.
   Agora o slug carrega um hash curto do caminho ABSOLUTO, então continua
   legível (`api-3f9c1a`) mas é único por diretório.

2. ESCRITA CONCORRENTE SEM LOCK
   Duas abas de terminal no mesmo projeto faziam read-modify-write no mesmo
   JSON. A última escrita vencia e apagava silenciosamente o progresso da outra.
   `update_json()` serializa com `fcntl.flock` e grava de forma atômica
   (arquivo temporário + `os.replace`), então uma queda no meio da escrita não
   deixa JSON truncado.

NOTA DE MIGRAÇÃO
Os arquivos criados antes desta mudança usam o slug antigo (só o basename) e
não guardam o caminho de origem — não há como saber a qual projeto pertenciam.
Por isso não são migrados automaticamente: adivinhar poderia fundir o estado de
dois projetos, que é justamente o bug. O contexto de sessão é efêmero e se
reconstrói sozinho; os arquivos antigos podem ser apagados quando incomodarem.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

try:
    import fcntl  # POSIX (macOS/Linux). No Windows o lock é no-op.

    TEM_FLOCK = True
except ImportError:  # pragma: no cover
    TEM_FLOCK = False


def is_subagent_call(data: dict) -> bool:
    """True quando o hook disparou dentro de uma chamada de subagent (Task/Agent).

    O contrato oficial de hooks do Claude Code inclui `agent_id` no payload
    só quando o hook roda dentro de uma subagent — nunca no thread principal.
    Hooks que contam uso de contexto do thread principal (context-monitor) ou
    sugerem skills do workflow principal (intellix-skill-router) devem pular
    nesse caso: a subagent tem seu próprio orçamento de contexto e seu próprio
    prompt de tarefa vindo do orquestrador, então o aviso/sugestão do fluxo
    principal não se aplica — só confunde a subagent e infla o contador do
    thread principal com chamadas que não são dele.

    Achado do lote de remediação de 2026-09-16 (ruído de hooks em subagentes).
    """
    return bool(data.get("agent_id"))


def get_project_slug(cwd: str | Path) -> str:
    """Identificador estável e único por diretório.

    Formato: `<nome-legível>-<hash6>`. O nome ajuda humano a reconhecer;
    o hash do caminho absoluto garante que dois projetos homônimos em pastas
    diferentes não colidam.
    """
    p = Path(cwd).expanduser()
    try:
        p = p.resolve()
    except OSError:
        p = p.absolute()
    nome = p.name.lower().replace(" ", "-").replace("_", "-") or "raiz"
    h = hashlib.sha256(str(p).encode("utf-8")).hexdigest()[:6]
    return f"{nome}-{h}"


@contextmanager
def _locked(path: Path):
    """Lock exclusivo por arquivo, entre processos. Libera sempre."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_suffix(path.suffix + ".lock")
    fh = None
    try:
        fh = open(lock, "w", encoding="utf-8")
        if TEM_FLOCK:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        yield
    except OSError:
        yield  # não conseguiu travar: seguir sem lock é melhor que quebrar o hook
    finally:
        if fh is not None:
            try:
                if TEM_FLOCK:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                fh.close()
            except OSError:
                pass


def read_json(path: Path, default: dict | None = None) -> dict:
    """Lê JSON tolerando arquivo ausente ou corrompido."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return dict(default or {})


def write_json_atomic(path: Path, data: dict) -> bool:
    """Grava via arquivo temporário + os.replace: nunca deixa JSON pela metade."""
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def update_json(path: Path, fn, default: dict | None = None) -> dict:
    """Read-modify-write serializado. `fn(dados) -> dados`.

    Use SEMPRE isto em vez de ler, alterar e escrever solto: sem o lock, duas
    sessões simultâneas se sobrescrevem.
    """
    path = Path(path)
    with _locked(path):
        dados = read_json(path, default)
        try:
            novos = fn(dados)
        except Exception:  # noqa: BLE001 — hook não pode quebrar por erro de callback
            return dados
        if novos is not None:
            write_json_atomic(path, novos)
            return novos
        return dados
