#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phase-gate-hook.py — Gate de fase com enforcement real (Fase 3.2 do
PLANO-CORRECAO-2026-09-07.md).

PROBLEMA QUE RESOLVE (achado C5 da auditoria)
O plugin já tinha `hooks/scripts/phase-gate.sh`, bem construído e chamado pelos
comandos /plan, /execute e /deploy. Mas isso só cobre o caminho dos COMANDOS.
Quando o agente escreve código direto com Write/Edit — sob pressão de "só
implementa logo", ou depois de uma compactação de contexto que apagou o combinado
— nada verifica se a arquitetura foi definida antes. O princípio "Aprovação
Explícita" do MASTER-ARCHITECTURE virava sugestão.

Este hook fecha o caminho da FERRAMENTA: bloqueia Write/Edit em código de produção
enquanto o projeto ainda estiver nas fases de planejamento.

PRINCÍPIO DE DESIGN — só bloquear o que é inequívoco.
O bash-safety-check foi desativado em 2026-09-07 por bloquear trabalho legítimo
(4 vezes numa sessão). Este hook adota o oposto: na dúvida, LIBERA. Só bloqueia
quando as quatro condições valem ao mesmo tempo:

  1. existe `.intellix-phase` no projeto  → o projeto optou pelo método IntelliX;
  2. o valor está em `bloqueia_codigo_em` (metodologia.yaml: init, arch);
  3. o arquivo alvo é código de produção (src/ ou app/, extensão de código);
  4. não é teste, config, doc, migration nem scaffolding.

Fora disso, sai 0 e não opina. Projeto sem `.intellix-phase` nunca é afetado.

Contrato de hook: exit 0 libera, exit 2 bloqueia (stderr vai para o agente).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GLOBAL_ROOT = Path(__file__).resolve().parent.parent  # ~/.claude

# Extensões consideradas código de produção.
EXT_CODIGO = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"}

# Diretórios que contêm código de produção.
DIRS_PRODUCAO = ("src/", "app/", "lib/", "components/")

# Isenções por SEGMENTO de caminho, nunca por substring solta.
# Substring daria falso-negativo grave: um projeto em ~/meu-teste/ ou um arquivo
# TestimonialCard.tsx conteriam "test" e escapariam do gate inteiro.
DIRS_ISENTOS = {
    "tests", "test", "__tests__", "e2e", "playwright", "vitest", "cypress",
    "docs", "scripts", "node_modules", ".claude", ".next", "dist", "build",
    "migrations", "seeds", "fixtures", "mocks", "stories",
}

# Isenções por sufixo de nome de arquivo.
SUFIXOS_ISENTOS = (".test.", ".spec.", ".config.", ".stories.", ".d.")


def fases_bloqueadas() -> set[str]:
    """Lê metodologia.yaml. Se indisponível, usa o padrão documentado."""
    padrao = {"init", "arch"}
    f = GLOBAL_ROOT / "metodologia.yaml"
    if not f.is_file():
        return padrao
    try:
        import yaml

        meta = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        valores = meta.get("controle_de_fase", {}).get("bloqueia_codigo_em")
        return set(valores) if valores else padrao
    except Exception:  # noqa: BLE001 — nunca derrubar a sessão por causa do YAML
        return padrao


def main() -> int:
    # 1. Payload do hook. Qualquer problema aqui = liberar.
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0

    caminho = (payload.get("tool_input") or {}).get("file_path") or ""
    if not caminho:
        return 0

    p = Path(caminho)
    rel = str(p).replace("\\", "/")

    # 2. É código de produção?
    if p.suffix.lower() not in EXT_CODIGO:
        return 0
    partes = [seg.lower() for seg in p.parts]
    if not any(d.rstrip("/") in partes for d in DIRS_PRODUCAO):
        return 0
    if DIRS_ISENTOS & set(partes):
        return 0
    if any(s in p.name.lower() for s in SUFIXOS_ISENTOS):
        return 0

    # 3. O projeto optou pelo método IntelliX? Procura .intellix-phase subindo
    #    a árvore a partir do arquivo alvo.
    marcador = None
    for pasta in [p.parent, *p.parent.parents]:
        candidato = pasta / ".intellix-phase"
        if candidato.is_file():
            marcador = candidato
            break
        if (pasta / ".git").exists():  # não atravessa a raiz do repositório
            break
    if marcador is None:
        return 0  # projeto fora do método — nenhuma opinião

    try:
        fase = marcador.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return 0

    # 4. A fase atual permite escrever código?
    if fase not in fases_bloqueadas():
        return 0

    projeto = marcador.parent.name
    print(
        f"""
═══ INTELLIX PHASE GATE: BLOQUEADO ═══
Arquivo:  {rel}
Projeto:  {projeto}
Fase:     '{fase}' (definida em {marcador})

Código de produção não pode ser escrito enquanto a fase for '{fase}' — a
arquitetura ainda não foi fechada. Escrever agora é o retrabalho que o método
existe para evitar (MASTER-ARCHITECTURE §0).

Como prosseguir, na ordem:
  1. Fase 01 — Skill("intellix:architecture"): schema com RLS, rotas, tipos,
     repository/service. Grave o resultado em references/architecture.md.
  2. Avance o marcador:  echo dev > {marcador}
  3. Repita a escrita.

Se este projeto é uma exceção deliberada (protótipo descartável, spike),
diga isso ao usuário e peça confirmação explícita para avançar o marcador —
não contorne em silêncio.
""".strip(),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 — falha do gate nunca pode travar o trabalho
        sys.exit(0)
