#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scaffold-check.py — confere se um projeto tem os artefatos que o workflow IntelliX promete.

Criado em 2026-09-16 (lote P1-1, decisão D7). O kickoff é uma instrução para o
modelo, não um script — este verificador é o que transforma "o scaffolding gera X"
num fato checável, no projeto temporário de teste e em projetos reais de cliente.

A lista de arquivos vem de `artefatos_projeto` em ~/.claude/metodologia.yaml
(fonte normativa); este script não mantém uma segunda lista.

Uso:
    python3 scaffold-check.py <dir-do-projeto> [--fase kickoff|arch] [--ui|--sem-ui]

    --fase kickoff  (padrão) artefatos `sempre` + DESIGN.md se houver UI + higiene
    --fase arch     o mesmo + references/architecture.md já sem o marcador de rascunho
    --ui / --sem-ui força a detecção de interface (padrão: existe src/app ou src/components)

Saída: 0 = ok | 1 = faltas encontradas (listadas) | 2 = erro de uso/configuração
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("INTELLIX_ROOT") or Path(__file__).resolve().parent.parent)
MARCADOR_RASCUNHO = "intellix-rascunho-kickoff"

# Pastas que NUNCA vão para o repositório do cliente (fronteira global × projeto).
PROIBIDOS = [".claude/agents", ".claude/skills", ".claude/commands", "agentes"]

# Entradas que o .gitignore do projeto precisa conter.
GITIGNORE_OBRIGATORIO = ["CLAUDE.local.md", ".claude/settings.local.json", ".env.local"]

# Chaves de .env.example que precisam estar vazias (nunca valor real versionado).
SEGREDO = re.compile(r"(KEY|SECRET|TOKEN|PASSWORD)$", re.IGNORECASE)


def erro(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"scaffold-check: {msg}", file=sys.stderr)
    sys.exit(2)


def carregar_artefatos() -> dict:
    f = ROOT / "metodologia.yaml"
    try:
        import yaml  # PyYAML

        meta = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        erro(f"metodologia.yaml não encontrado em {f}")
    except Exception as e:  # noqa: BLE001
        erro(f"metodologia.yaml inválido ou PyYAML ausente: {e}")
    art = meta.get("artefatos_projeto")
    if not isinstance(art, dict) or not art.get("sempre"):
        erro("metodologia.yaml sem artefatos_projeto.sempre")
    return {"art": art, "fases": (meta.get("controle_de_fase") or {}).get("valores") or []}


def existe(proj: Path, item: str) -> bool:
    p = proj / item.rstrip("/")
    return p.is_dir() if item.endswith("/") else p.is_file()


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    fase = "kickoff"
    if "--fase" in argv:
        i = argv.index("--fase")
        if i + 1 >= len(argv):
            erro("--fase exige um valor")
        fase = argv[i + 1]
        args = [a for a in args if a != fase]
    if fase not in ("kickoff", "arch"):
        erro(f"fase desconhecida '{fase}' (use kickoff ou arch)")
    if len(args) != 1:
        erro("uso: scaffold-check.py <dir-do-projeto> [--fase kickoff|arch] [--ui|--sem-ui]")
    proj = Path(args[0]).resolve()
    if not proj.is_dir():
        erro(f"diretório inexistente: {proj}")

    cfg = carregar_artefatos()
    art = cfg["art"]
    if "--ui" in flags:
        com_ui = True
    elif "--sem-ui" in flags:
        com_ui = False
    else:
        com_ui = (proj / "src/app").is_dir() or (proj / "src/components").is_dir()

    faltas: list[str] = []

    exigidos = list(art.get("sempre") or [])
    if com_ui:
        exigidos += [x for x in (art.get("com_interface") or []) if x == "DESIGN.md"]
    for item in exigidos:
        if not existe(proj, item):
            faltas.append(f"FALTA: {item}")

    fase_file = proj / ".intellix-phase"
    if fase_file.is_file():
        valor = fase_file.read_text(encoding="utf-8").strip()
        if cfg["fases"] and valor not in cfg["fases"]:
            faltas.append(f"INVÁLIDO: .intellix-phase = '{valor}' (valores: {', '.join(cfg['fases'])})")

    for proibido in PROIBIDOS:
        if (proj / proibido).exists():
            faltas.append(f"PROIBIDO: {proibido}/ — agentes/skills/comandos ficam globais (vêm do plugin)")

    gi = proj / ".gitignore"
    if gi.is_file():
        linhas = {l.strip() for l in gi.read_text(encoding="utf-8").splitlines()}
        for entrada in GITIGNORE_OBRIGATORIO:
            if entrada not in linhas:
                faltas.append(f"GITIGNORE: falta '{entrada}'")

    env_ex = proj / ".env.example"
    if env_ex.is_file():
        for n, linha in enumerate(env_ex.read_text(encoding="utf-8").splitlines(), 1):
            m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", linha)
            if m and SEGREDO.search(m.group(1)) and m.group(2).strip() not in ("", '""', "''"):
                faltas.append(f"SEGREDO: .env.example:{n} ({m.group(1)}) tem valor — deve ficar vazio")

    arq = proj / "references/architecture.md"
    if fase == "arch" and arq.is_file() and MARCADOR_RASCUNHO in arq.read_text(encoding="utf-8"):
        faltas.append("PENDENTE: references/architecture.md ainda é o rascunho do kickoff (Fase 01 não registrou decisões)")

    if faltas:
        print(f"scaffold-check ({fase}, {'com' if com_ui else 'sem'} UI): {len(faltas)} problema(s) em {proj}")
        for f in faltas:
            print(f"  ✗ {f}")
        return 1
    print(f"scaffold-check ({fase}, {'com' if com_ui else 'sem'} UI): OK — {len(exigidos)} artefatos presentes em {proj}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
