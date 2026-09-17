#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bash-guardrail.py — substituto do bash-safety-check.py, desativado em 2026-09-07.

MODELO DE AMEAÇA (a coisa mais importante deste arquivo)
Este hook defende contra **acidente**, não contra **evasão**. Quem executa os
comandos é o agente, que não está tentando burlar o filtro — está prestes a
errar. Isso muda o desenho por completo:

  - Não faz sentido perseguir ofuscação (base64, variável, eval). Um agente que
    quisesse contornar contornaria, e nenhum hook impede isso. Perseguir esse
    caso só gera complexidade e falso positivo.
  - Faz muito sentido pegar o dedo escorregando: `rm -rf` com alvo errado,
    `--force` na branch errada, SQL destrutivo apontado para produção.

Por isso a lista é CURTA e restrita ao que é ao mesmo tempo catastrófico e
irreversível. Coisa recuperável (git reset --hard, que tem reflog) fica de fora
de propósito: bloquear o recuperável só gera atrito.

POR QUE O ANTERIOR FOI DESATIVADO (auditoria 2026-09-07, achados C3 e C4)
Ele casava substring no comando inteiro. Duas consequências:
  - `DROP TABLE invoices;` passava — o regex `[^I]` com IGNORECASE excluía "i";
  - bloqueava qualquer comando que apenas MENCIONASSE o padrão. Numa sessão
    barrou 4 trabalhos legítimos, incluindo uma varredura de segredos e a
    redação da documentação do próprio bug.

Aqui o comando é TOKENIZADO (shlex), heredocs são tratados como dado e não como
código, e regra de SQL só vale quando o comando é de fato um cliente de banco.
Escrever sobre `DROP TABLE` deixa de ser confundido com executar.

Contrato: exit 0 libera, exit 2 bloqueia (stderr vai ao agente).
Testes: scripts/tests/test_hooks.py::TestBashGuardrail
"""
from __future__ import annotations

import json
import re
import shlex
import sys

# Clientes de banco: só nestes o SQL destrutivo é executado de fato.
CLIENTES_DB = {"psql", "mysql", "mariadb", "sqlite3", "supabase", "wrangler", "pgcli", "usql"}

# Shells que recebem comando como argumento — precisa olhar dentro.
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}

SQL_DESTRUTIVO = re.compile(
    r"\b(?:DROP\s+(?:TABLE|DATABASE|SCHEMA)|TRUNCATE(?:\s+TABLE)?|DELETE\s+FROM)\b",
    re.IGNORECASE,
)
SQL_COM_ESCOPO = re.compile(r"\bWHERE\b|\bIF\s+EXISTS\b", re.IGNORECASE)

# Alvos onde `rm -rf` é catastrófico.
ALVOS_FATAIS = {"/", "/*", "~", "~/", "$HOME", "${HOME}", "/Users", "/home", "."}


def remover_heredocs(cmd: str) -> str:
    """Conteúdo de heredoc é DADO, não comando.

    Sem isto, escrever um arquivo que contenha SQL de exemplo seria lido como
    execução desse SQL — foi um dos falsos positivos que derrubaram o hook antigo.
    """
    return re.sub(r"<<-?\s*'?\"?(\w+)'?\"?.*?^\1", " ", cmd, flags=re.DOTALL | re.MULTILINE)


OPERADORES = {";", "&&", "||", "|", "&", "\n"}


def segmentos_tokenizados(cmd: str) -> list[list[str]]:
    """Divide o comando em trechos, RESPEITANDO ASPAS.

    Separar por regex em `;` quebrava `psql -c "TRUNCATE x;"` no meio da string
    SQL, a análise abortava por aspas desbalanceadas e o comando passava livre.
    Era assim que os bypasses 1 e 2 escapavam também da versão nova.
    `punctuation_chars` faz o shlex devolver os operadores como tokens próprios,
    sem tocar no que está entre aspas.
    """
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        brutos = list(lex)
    except ValueError:
        return []

    segs: list[list[str]] = []
    atual: list[str] = []
    for t in brutos:
        if t in OPERADORES:
            if atual:
                segs.append(atual)
            atual = []
        else:
            atual.append(t)
    if atual:
        segs.append(atual)
    return segs


def _nome(tok: str) -> str:
    return tok.split("/")[-1]


def avaliar(cmd: str, profundidade: int = 0) -> str | None:
    """Devolve o motivo do bloqueio, ou None para liberar."""
    if profundidade > 2:
        return None

    for toks in segmentos_tokenizados(remover_heredocs(cmd)):
        if not toks:
            continue
        prog = _nome(toks[0])

        # bash -c "..." — analisa o comando interno
        if prog in SHELLS:
            for i, t in enumerate(toks[1:], 1):
                if t == "-c" and i + 1 < len(toks):
                    motivo = avaliar(toks[i + 1], profundidade + 1)
                    if motivo:
                        return motivo
            continue

        # sudo <cmd> — analisa o que vem depois
        if prog == "sudo":
            motivo = avaliar(" ".join(shlex.quote(t) for t in toks[1:]), profundidade + 1)
            if motivo:
                return f"{motivo} (via sudo)"
            continue

        # 1. rm -rf em alvo fatal
        if prog == "rm":
            flags = "".join(t for t in toks[1:] if t.startswith("-"))
            if "r" in flags and "f" in flags:
                alvos = [t for t in toks[1:] if not t.startswith("-")]
                for alvo in alvos:
                    limpo = alvo.rstrip("/") or "/"
                    if alvo in ALVOS_FATAIS or limpo in ALVOS_FATAIS:
                        return f"rm -rf em alvo crítico: {alvo}"
                    # caminho absoluto raso: /etc, /usr, /var...
                    if alvo.startswith("/") and alvo.count("/") == 1 and len(alvo) > 1:
                        return f"rm -rf na raiz do sistema: {alvo}"
                if not alvos:
                    return "rm -rf sem alvo explícito"

        # 2. push forçado em branch protegida
        if prog == "git" and "push" in toks:
            forcado = any(t in ("--force", "-f", "--force-with-lease") for t in toks)
            protegida = any(t in ("main", "master", "producao", "production") for t in toks)
            if forcado and protegida:
                return "git push forçado em branch protegida (main/master)"

        # 3. git clean apagando arquivos não rastreados (não tem reflog)
        if prog == "git" and "clean" in toks:
            flags = "".join(t[1:] for t in toks if re.fullmatch(r"-[a-zA-Z]+", t))
            if "f" in flags and ("d" in flags or "x" in flags):
                return "git clean -fd remove arquivos não rastreados — não há reflog para isso"

        # 4. SQL destrutivo, SÓ quando é cliente de banco de verdade
        if prog in CLIENTES_DB:
            sql = " ".join(toks[1:])
            achado = SQL_DESTRUTIVO.search(sql)
            if achado and not SQL_COM_ESCOPO.search(sql):
                return f"SQL destrutivo sem escopo em {prog}: {achado.group(0)}"

        # 5. sobrescrita de dispositivo / formatação
        if prog == "dd" and any(t.startswith("of=/dev/") for t in toks):
            return "dd escrevendo direto em dispositivo de bloco"
        if prog.startswith("mkfs"):
            return "formatação de sistema de arquivos"

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return 0

    cmd = (payload.get("tool_input") or {}).get("command") or ""
    if not cmd.strip():
        return 0

    try:
        motivo = avaliar(cmd)
    except Exception:  # noqa: BLE001 — falha de análise nunca bloqueia trabalho
        return 0

    if not motivo:
        return 0

    print(
        f"""
═══ GUARDRAIL: OPERAÇÃO CATASTRÓFICA BLOQUEADA ═══
Motivo: {motivo}

Este bloqueio cobre só o que é irreversível e destrutivo. Se for intencional,
execute manualmente no seu terminal — o hook não roda lá.

Se este bloqueio foi indevido, é bug: registre o comando em
scripts/tests/test_hooks.py::TestBashGuardrail como caso de falso positivo.
Guardrail que atrapalha trabalho legítimo é desativado, não tolerado.
""".strip(),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        sys.exit(0)
