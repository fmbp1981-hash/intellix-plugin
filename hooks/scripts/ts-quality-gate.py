#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ts-quality-gate.py — substitui o antigo hook "type: prompt" de hooks.json
(achado 2026-09-18: o modelo-juiz não emitia o literal "approve" para
arquivos fora do escopo TS/JS — ex: .py — e o harness tratava qualquer
resposta sem esse token exato como bloqueio, quebrando Write/Edit em TODO
arquivo não-TS/JS de todo projeto).

PRINCÍPIO DE DESIGN — igual ao phase-gate-hook.py: só bloquear o que é
inequívoco e verificável sem IA. O Passo 1 (filtro de extensão) é
determinístico e não deveria nunca ter dependido de um LLM.

O que este hook verifica (só quando o Passo 1 não isenta o arquivo):
  - uso de `any` explícito em TypeScript (`: any`, `as any`, `<any>`,
    `any[]`) — violação inequívoca da regra "zero any implícito"
    (~/.claude/modules/dev-rules.md).

O que este hook NÃO tenta verificar (fora do alcance de um script
determinístico, e já coberto em outro estágio do workflow IntelliX):
  - naming conventions, estrutura de camadas (components -> services ->
    repositories -> Supabase) — isso é revisão de conteúdo/arquitetura,
    já feita pelo agente `intellix:code-quality-reviewer` no Estágio 3 do
    /intellix:execute e pelo `architect-reviewer` no gate de pré-deploy.
    Duplicar esse julgamento aqui, de novo via LLM, reintroduziria a
    mesma classe de bug que este arquivo corrige.

Contrato de hook: exit 0 libera, exit 2 bloqueia (stderr vai para o agente).
Qualquer erro interno = liberar (nunca travar a sessão do usuário).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Extensões que ainda justificam checagem de conteúdo TS/JS.
EXT_TS_JS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte"}

# `any` explícito — regex conservador para reduzir falso positivo (ex: uma
# variável chamada `anything` ou `company` não deve disparar o gate).
_ANY_PATTERN = re.compile(
    r"""
    :\s*any\b            # : any  (anotação de tipo)
    | \bas\s+any\b        # as any (type assertion)
    | <\s*any\s*>         # <any>  (generic explícito)
    | \bany\s*\[\s*\]     # any[]  (array de any)
    """,
    re.VERBOSE,
)


def _conteudo_escrito(tool_input: dict) -> str:
    """Extrai o texto que está sendo introduzido pela chamada de ferramenta.

    Write: `content` é o arquivo inteiro. Edit/MultiEdit: só o `new_string`
    importa — o `old_string` já existia e não é responsabilidade desta
    escrita.
    """
    if "content" in tool_input:
        return str(tool_input.get("content") or "")
    if "new_string" in tool_input:
        return str(tool_input.get("new_string") or "")
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        return "\n".join(str(e.get("new_string") or "") for e in edits if isinstance(e, dict))
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — stdin vazio/malformado nunca bloqueia
        return 0

    tool_input = payload.get("tool_input") or {}
    caminho = tool_input.get("file_path") or ""
    if not caminho:
        return 0

    p = Path(caminho)
    rel = str(p).replace("\\", "/")

    # Passo 1 (determinístico): fora do escopo TS/JS -> approve, sempre.
    if p.suffix.lower() not in EXT_TS_JS:
        return 0

    # Passo 2: scripts da ferramenta Workflow são JS puro por exigência da
    # própria ferramenta, não código de produção da aplicação.
    if ".claude/workflows/" in rel:
        return 0

    # Passo 3: único ponto onde um LLM seria necessário para naming/camadas —
    # deliberadamente fora deste hook (ver docstring). Aqui só o que é
    # verificável por regex sem ambiguidade.
    conteudo = _conteudo_escrito(tool_input)
    match = _ANY_PATTERN.search(conteudo)
    if match is None:
        return 0

    trecho = conteudo[max(0, match.start() - 40) : match.end() + 40].strip()
    print(
        f"""
═══ INTELLIX TS QUALITY GATE: BLOQUEADO ═══
Arquivo:  {rel}
Achado:   uso de `any` explícito — {match.group(0)!r}
Contexto: ...{trecho}...

Regra: TypeScript strict, zero `any` explícito (~/.claude/modules/dev-rules.md).
Troque por um tipo concreto, `unknown` + narrowing, ou um generic.

Se este `any` é deliberado e justificado (ex: interoperar com uma lib sem
tipos), diga isso ao usuário e peça confirmação explícita antes de manter —
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
