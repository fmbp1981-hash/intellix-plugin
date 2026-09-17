#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de contrato dos hooks — Fase 2.2 do PLANO-CORRECAO-2026-09-07.md.

Usa unittest da biblioteca padrão (pytest não está instalado e não vale criar
dependência para uma suíte que precisa rodar em qualquer máquina).

CONTRATO QUE TODO HOOK DEVE CUMPRIR
Estes scripts rodam em toda mensagem e em toda chamada de ferramenta, em todo
projeto. Um erro neles polui ou trava a sessão inteira. Logo:

  1. compila sem erro de sintaxe;
  2. sai com código 0 mesmo com stdin vazio;
  3. sai com código 0 mesmo com stdin JSON malformado;
  4. sai com código 0 rodando num diretório vazio (projeto desconhecido);
  5. termina em menos de 5 s.

Exceção deliberada: hooks de bloqueio (PreToolUse) podem sair com 2 para vetar
uma ferramenta. O phase-gate-hook é um desses — os testes de contrato o exercitam
com payloads que NÃO disparam bloqueio, e a classe TestPhaseGate cobre o
comportamento de veto separadamente. O bash-safety-check foi desativado em
2026-09-07 por bloquear trabalho legítimo (ver docstring dele).

Rodar:  python3 scripts/tests/test_hooks.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # ~/.claude
SCRIPTS = ROOT / "scripts"

# Scripts declarados como hooks em settings.json.
HOOK_SCRIPTS = [
    "bash-guardrail.py",
    "phase-gate-hook.py",
    "auto-claude-md.py",
    "new-session-flag.py",
    "intellix-project-check.py",
    "doctor.py",
    "perplexity-check.py",
    "context-loader.py",
    "intellix-skill-router.py",
    "session-tracker.py",
    "context-monitor.py",
    "session-history.py",
]

TIMEOUT = 5.0

PAYLOAD_VAZIO = ""
PAYLOAD_MALFORMADO = '{"isto": "não fecha'
PAYLOAD_VALIDO = json.dumps(
    {
        "session_id": "test-session",
        "prompt": "teste automatizado",
        "tool_name": "Bash",
        "tool_input": {"command": "echo ok"},
        "cwd": "/tmp",
    }
)


def run_hook(script: str, stdin: str, cwd: Path | None = None):
    """Executa um hook e devolve (returncode, stdout, stderr, duração)."""
    inicio = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=TIMEOUT + 5,
        cwd=str(cwd or ROOT),
    )
    return proc.returncode, proc.stdout, proc.stderr, time.monotonic() - inicio


class TestContratoDosHooks(unittest.TestCase):
    """Um hook que viola o contrato quebra toda sessão do usuário."""

    def test_todos_compilam(self):
        for script in HOOK_SCRIPTS:
            with self.subTest(script=script):
                caminho = SCRIPTS / script
                self.assertTrue(caminho.is_file(), f"{script} não existe mas está wireado em settings.json")
                r = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(caminho)],
                    capture_output=True, text=True,
                )
                self.assertEqual(r.returncode, 0, f"{script} não compila:\n{r.stderr}")

    def test_stdin_vazio_nao_quebra(self):
        for script in HOOK_SCRIPTS:
            with self.subTest(script=script):
                rc, _, err, _ = run_hook(script, PAYLOAD_VAZIO)
                self.assertEqual(rc, 0, f"{script} saiu com {rc} em stdin vazio. stderr:\n{err[:400]}")

    def test_stdin_malformado_nao_quebra(self):
        """Payload corrompido não pode gerar traceback na sessão do usuário."""
        for script in HOOK_SCRIPTS:
            with self.subTest(script=script):
                rc, _, err, _ = run_hook(script, PAYLOAD_MALFORMADO)
                self.assertEqual(rc, 0, f"{script} saiu com {rc} em JSON malformado. stderr:\n{err[:400]}")
                self.assertNotIn("Traceback", err, f"{script} vazou traceback com JSON malformado")

    def test_diretorio_desconhecido_nao_quebra(self):
        """Hook rodando em diretório vazio (projeto que ele nunca viu)."""
        with tempfile.TemporaryDirectory() as tmp:
            for script in HOOK_SCRIPTS:
                with self.subTest(script=script):
                    rc, _, err, _ = run_hook(script, PAYLOAD_VALIDO, cwd=Path(tmp))
                    self.assertEqual(rc, 0, f"{script} saiu com {rc} em diretório vazio. stderr:\n{err[:400]}")

    def test_dentro_do_orcamento_de_tempo(self):
        """Rodam a cada mensagem — latência acumula e o usuário sente."""
        for script in HOOK_SCRIPTS:
            with self.subTest(script=script):
                _, _, _, dur = run_hook(script, PAYLOAD_VALIDO)
                self.assertLess(dur, TIMEOUT, f"{script} levou {dur:.1f}s (orçamento {TIMEOUT}s)")


class TestPhaseGate(unittest.TestCase):
    """Gate de fase (3.2). Bloqueia código de produção enquanto a arquitetura não
    fechou — mas erra para o lado de LIBERAR, senão vira o bash-safety-check."""

    GATE = SCRIPTS / "phase-gate-hook.py"

    def _run(self, file_path: str) -> int:
        return subprocess.run(
            [sys.executable, str(self.GATE)],
            input=json.dumps({"tool_input": {"file_path": file_path}}),
            capture_output=True, text=True, timeout=10,
        ).returncode

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.proj = Path(self.tmp.name) / "proj"
        (self.proj / "src" / "components").mkdir(parents=True)
        (self.proj / "tests").mkdir()
        (self.proj / "supabase" / "migrations").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _fase(self, valor: str):
        (self.proj / ".intellix-phase").write_text(valor, encoding="utf-8")

    def test_bloqueia_codigo_de_producao_em_fase_de_planejamento(self):
        self._fase("arch")
        self.assertEqual(self._run(str(self.proj / "src/components/Card.tsx")), 2)

    def test_libera_apos_avancar_a_fase(self):
        self._fase("dev")
        self.assertEqual(self._run(str(self.proj / "src/components/Card.tsx")), 0)

    def test_nao_opina_em_projeto_fora_do_metodo(self):
        """Sem .intellix-phase, o projeto não optou pelo IntelliX."""
        livre = Path(self.tmp.name) / "livre" / "src"
        livre.mkdir(parents=True)
        self.assertEqual(self._run(str(livre / "app.tsx")), 0)

    def test_isencoes_nao_sao_bloqueadas(self):
        """Falso positivo aqui custa mais que falso negativo."""
        self._fase("arch")
        for rel in [
            "tests/card.test.ts",
            "src/components/Card.test.tsx",
            "src/types/db.d.ts",
            "next.config.ts",
            "supabase/migrations/x.ts",
            "src/README.md",
        ]:
            with self.subTest(arquivo=rel):
                self.assertEqual(self._run(str(self.proj / rel)), 0, f"{rel} não deveria ser bloqueado")

    def test_isencao_por_segmento_e_nao_por_substring(self):
        """Regressão: a 1ª versão isentava qualquer caminho contendo 'test',
        então TestimonialCard.tsx (e todo projeto em ~/meu-teste/) escapava."""
        self._fase("arch")
        self.assertEqual(self._run(str(self.proj / "src/components/TestimonialCard.tsx")), 2)

    def test_payload_invalido_libera(self):
        for payload in ["", "{quebrado", "{}"]:
            with self.subTest(payload=payload):
                rc = subprocess.run(
                    [sys.executable, str(self.GATE)], input=payload,
                    capture_output=True, text=True, timeout=10,
                ).returncode
                self.assertEqual(rc, 0)

    def test_mensagem_de_bloqueio_diz_como_prosseguir(self):
        """Bloqueio sem saída de emergência clara treina o usuário a contornar."""
        self._fase("arch")
        r = subprocess.run(
            [sys.executable, str(self.GATE)],
            input=json.dumps({"tool_input": {"file_path": str(self.proj / "src/a.tsx")}}),
            capture_output=True, text=True, timeout=10,
        )
        self.assertIn("intellix:architecture", r.stderr)
        self.assertIn("echo dev", r.stderr)


class TestSessaoCompartilhada(unittest.TestCase):
    """Identidade de projeto e escrita concorrente (3.4) — achado C6."""

    def setUp(self):
        sys.path.insert(0, str(SCRIPTS))
        import _session_common
        self.sc = _session_common

    def test_projetos_homonimos_nao_colidem(self):
        """O bug: dois clientes com pasta 'api' dividiam o mesmo arquivo de estado."""
        a = self.sc.get_project_slug("/tmp/cliente-a/api")
        b = self.sc.get_project_slug("/tmp/cliente-b/api")
        self.assertNotEqual(a, b)

    def test_slug_estavel_para_o_mesmo_caminho(self):
        c = "/tmp/cliente-a/api"
        self.assertEqual(self.sc.get_project_slug(c), self.sc.get_project_slug(c))

    def test_slug_permanece_legivel(self):
        """Hash sozinho seria ilegível; o nome da pasta tem que sobreviver."""
        self.assertTrue(self.sc.get_project_slug("/tmp/x/meu-crm").startswith("meu-crm-"))

    def test_escrita_concorrente_nao_perde_dados(self):
        """Sem lock, a última escrita vencia e apagava o progresso da outra sessão."""
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "estado.json"
            def escreve(i):
                self.sc.update_json(alvo, lambda d: {**d, "itens": d.get("itens", []) + [i]})
            with ThreadPoolExecutor(max_workers=16) as ex:
                list(ex.map(escreve, range(50)))
            self.assertEqual(len(self.sc.read_json(alvo)["itens"]), 50)

    def test_json_corrompido_nao_quebra(self):
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "corrompido.json"
            alvo.write_text("{isto nao e json", encoding="utf-8")
            self.assertEqual(self.sc.read_json(alvo, {"ok": True}), {"ok": True})

    def test_escrita_e_atomica(self):
        """os.replace garante que ninguém lê um JSON pela metade."""
        with tempfile.TemporaryDirectory() as tmp:
            alvo = Path(tmp) / "a.json"
            self.sc.write_json_atomic(alvo, {"x": 1})
            self.assertEqual(self.sc.read_json(alvo), {"x": 1})
            self.assertFalse(list(Path(tmp).glob("*.tmp")), "sobrou arquivo temporário")


class TestBashGuardrail(unittest.TestCase):
    """Substituto do bash-safety-check (desativado em 2026-09-07).

    Modelo de ameaça: defende contra ACIDENTE do agente, não contra evasão.
    Por isso a lista é curta e restrita ao irreversível — e por isso os casos de
    "deve liberar" pesam tanto quanto os de "deve bloquear": foi falso positivo,
    não falha de detecção, que matou o hook anterior.
    """

    GUARDRAIL = SCRIPTS / "bash-guardrail.py"
    # Montado em pedaços para o próprio arquivo de teste não virar falso positivo
    # de qualquer varredura futura de SQL destrutivo.
    D, T, TB = "D" + "ROP", "TRUN" + "CATE", "TAB" + "LE"

    def _rc(self, cmd: str) -> int:
        return subprocess.run(
            [sys.executable, str(self.GUARDRAIL)],
            input=json.dumps({"tool_input": {"command": cmd}}),
            capture_output=True, text=True, timeout=10,
        ).returncode

    def test_bypasses_comprovados_em_2026_09_07(self):
        """Os quatro que escapavam do filtro antigo."""
        casos = [
            f'psql -c "{self.D} {self.TB} invoices;"',   # regex [^I] com IGNORECASE
            f'psql -c "{self.T} clientes;"',             # TABLE é opcional no Postgres
            'bash -c "rm -rf ~"',                        # indireção
            'sudo rm -rf /',                             # via sudo
        ]
        for cmd in casos:
            with self.subTest(cmd=cmd):
                self.assertEqual(self._rc(cmd), 2, "bypass não foi fechado")

    def test_falsos_positivos_que_derrubaram_o_hook_antigo(self):
        """Mencionar um padrão destrutivo não é executá-lo. O filtro anterior
        bloqueou 4 trabalhos legítimos numa sessão, incluindo a documentação do
        próprio bug e uma varredura de segredos."""
        casos = [
            f'python3 -c "print(\'testando {self.D} {self.TB}\')"',
            f'echo "documentando o bug do {self.D} {self.TB}" >> notas.md',
            f'cat <<EOF > schema.sql\n{self.D} {self.TB} antiga;\nEOF',
            'grep -rn "senha" scripts/',
        ]
        for cmd in casos:
            with self.subTest(cmd=cmd):
                self.assertEqual(self._rc(cmd), 0, "bloqueou trabalho legítimo")

    def test_operacoes_catastroficas_bloqueadas(self):
        for cmd in [
            'git push --force origin main',
            'git clean -fdx',
            'rm -rf $HOME',
            f'supabase db execute --command "{self.D} DATABASE prod"',
        ]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self._rc(cmd), 2)

    def test_operacoes_rotineiras_liberadas(self):
        """Inclui o recuperável de propósito: git reset --hard tem reflog, e
        bloquear o que dá para desfazer só gera atrito."""
        for cmd in [
            'rm -rf node_modules',
            'rm -rf ./build/cache',
            'git push origin main',
            'git reset --hard HEAD~1',
            'git clean -n',
            'psql -c "DELETE FROM logs WHERE created_at < now()"',
            f'psql -c "{self.D} {self.TB} IF EXISTS tmp"',
        ]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self._rc(cmd), 0)

    def test_payload_invalido_libera(self):
        for payload in ["", "{quebrado", "{}", '{"tool_input":{}}']:
            with self.subTest(payload=payload):
                rc = subprocess.run(
                    [sys.executable, str(self.GUARDRAIL)], input=payload,
                    capture_output=True, text=True, timeout=10,
                ).returncode
                self.assertEqual(rc, 0)


class TestRuidoDeHooksEmSubagents(unittest.TestCase):
    """Achado do lote de remediação de 2026-09-16 (ruído de hooks em subagents).

    Dois defeitos reais, observados na própria sessão que fez a remediação:

    1. context-monitor.py contava e avisava sobre tool calls de SUBAGENTS
       (Task/Agent), inflando o contador do thread principal e mandando uma
       subagent somente-leitura "invocar context-checkpoint" — coisa que não
       faz sentido para ela.
    2. intellix-skill-router.py lia `sys.stdin.read()` cru como se fosse o
       prompt, em vez de fazer o parse do JSON e usar só o campo "prompt".
       Um projeto com "worktree" no caminho (cwd/transcript_path) disparava
       a sugestão de git-workflow-and-versioning mesmo sem o usuário ter
       dito nada sobre git — o roteador estava varrendo o envelope inteiro,
       não o texto do usuário.
    """

    ROUTER = SCRIPTS / "intellix-skill-router.py"
    MONITOR = SCRIPTS / "context-monitor.py"

    def test_router_ignora_prompt_de_subagent(self):
        payload = json.dumps({
            "session_id": "t",
            "prompt": "criar novo sistema saas com deploy em producao",
            "agent_id": "sub-1",
            "agent_type": "Explore",
        })
        rc, out, err, _ = run_hook("intellix-skill-router.py", payload)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "", "roteador não deveria sugerir nada dentro de uma subagent")

    def test_router_nao_confunde_path_do_cwd_com_o_prompt(self):
        """cwd contém 'worktree' — não pode virar sugestão de git-workflow."""
        payload = json.dumps({
            "session_id": "t",
            "prompt": "decida a melhor abordagem",
            "cwd": "/Users/x/.claude/.claude/worktrees/algum-branch-longo",
            "transcript_path": "/Users/x/.claude/.claude/worktrees/algum-branch-longo/t.jsonl",
        })
        rc, out, err, _ = run_hook("intellix-skill-router.py", payload)
        self.assertEqual(rc, 0)
        self.assertNotIn("git-workflow-and-versioning", out)
        self.assertIn("doubt-driven-development", out, "match real no texto do prompt deve continuar funcionando")

    def test_router_ainda_sugere_a_partir_do_prompt_real(self):
        payload = json.dumps({"session_id": "t", "prompt": "preciso resolver um conflito de merge/rebase"})
        rc, out, err, _ = run_hook("intellix-skill-router.py", payload)
        self.assertEqual(rc, 0)
        self.assertIn("git-workflow-and-versioning", out)

    def test_monitor_ignora_tool_call_de_subagent(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = json.dumps({
                "session_id": "t", "tool_name": "Read",
                "agent_id": "sub-1", "agent_type": "Explore",
            })
            # Bombardeia acima do threshold — se contasse, teria disparado o aviso.
            for _ in range(45):
                rc, out, err, _ = run_hook("context-monitor.py", payload, cwd=Path(tmp))
                self.assertEqual(rc, 0)
                self.assertEqual(out, "", "subagent não deve nunca disparar o aviso de checkpoint")

    def test_monitor_continua_contando_o_thread_principal(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = json.dumps({"session_id": "t", "tool_name": "Read"})
            saidas = [run_hook("context-monitor.py", payload, cwd=Path(tmp))[1] for _ in range(41)]
            self.assertTrue(
                any("CONTEXT-MONITOR" in s for s in saidas),
                "thread principal deve continuar disparando o aviso ao passar do threshold",
            )


# Os testes do doctor.py vivem em test_doctor.py (fixtures isoladas em diretório
# temporário). A versão anterior desta classe criava arquivos dentro da config
# real (~/.claude/modules, ~/.claude/skills) — substituída em 2026-09-16 (P0-2).


if __name__ == "__main__":
    unittest.main(verbosity=2)
