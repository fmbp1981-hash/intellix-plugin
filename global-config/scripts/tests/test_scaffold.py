#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do scaffold-check.py e do phase-gate.sh do plugin (lote P1-1, 2026-09-16).

Monta, num diretório temporário, a árvore que o kickoff promete (lida de
metodologia.yaml e dos templates do plugin), confirma que o verificador aprova e
então quebra um item por vez. Também exercita o phase gate de /plan com o
marcador de rascunho de references/architecture.md.

O plugin é procurado em $INTELLIX_PLUGIN_DIR ou em
<raiz>/plugins/marketplaces/intellix-plugin; sem ele, os testes do gate são pulados.

Rodar:  python3 scripts/tests/test_scaffold.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
ROOT = SCRIPTS.parent
CHECK = SCRIPTS / "scaffold-check.py"
PLUGIN = Path(os.environ.get("INTELLIX_PLUGIN_DIR") or ROOT / "plugins/marketplaces/intellix-plugin")
TEMPLATES = PLUGIN / "intellix-templates"


def artefatos() -> dict:
    import yaml

    return yaml.safe_load((ROOT / "metodologia.yaml").read_text(encoding="utf-8"))["artefatos_projeto"]


def montar_projeto(base: Path, com_ui: bool = True) -> Path:
    art = artefatos()
    for item in art["sempre"]:
        p = base / item.rstrip("/")
        if item.endswith("/"):
            p.mkdir(parents=True, exist_ok=True)
            (p / ".gitkeep").write_text("")
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        tpl = TEMPLATES / "references-template" / p.name
        p.write_text(tpl.read_text(encoding="utf-8") if item.startswith("references/") and tpl.is_file() else "x\n")
    (base / ".intellix-phase").write_text("arch\n")
    (base / ".gitignore").write_text("CLAUDE.local.md\n.claude/settings.local.json\n.env\n.env.local\n")
    (base / ".env.example").write_text("NEXT_PUBLIC_APP_URL=http://localhost:3000\nSUPABASE_SERVICE_ROLE_KEY=\n")
    if com_ui:
        (base / "src/app").mkdir(parents=True)
        (base / "DESIGN.md").write_text("# Design\n")
    return base


def check(proj: Path, *args: str):
    r = subprocess.run([sys.executable, str(CHECK), str(proj), *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout + r.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.proj = montar_projeto(Path(self._tmp.name) / "proj")

    def tearDown(self):
        self._tmp.cleanup()

    def assertFalha(self, trecho: str, *args: str):
        rc, out = check(self.proj, *args)
        self.assertEqual(rc, 1, out)
        self.assertIn(trecho, out)


class TestScaffoldCheck(Base):
    def test_projeto_completo_passa(self):
        rc, out = check(self.proj)
        self.assertEqual(rc, 0, out)

    def test_falta_artefato(self):
        (self.proj / "AGENTS.md").unlink()
        self.assertFalha("FALTA: AGENTS.md")

    def test_ui_exige_design(self):
        (self.proj / "DESIGN.md").unlink()
        self.assertFalha("FALTA: DESIGN.md")

    def test_sem_ui_nao_exige_design(self):
        (self.proj / "DESIGN.md").unlink()
        rc, out = check(self.proj, "--sem-ui")
        self.assertEqual(rc, 0, out)

    def test_agentes_no_projeto_sao_proibidos(self):
        (self.proj / "agentes").mkdir()
        self.assertFalha("PROIBIDO: agentes/")

    def test_claude_agents_no_projeto_sao_proibidos(self):
        (self.proj / ".claude/agents").mkdir(parents=True)
        self.assertFalha("PROIBIDO: .claude/agents/")

    def test_segredo_no_env_example(self):
        (self.proj / ".env.example").write_text("SUPABASE_SERVICE_ROLE_KEY=eyJvalor\n")
        self.assertFalha("SEGREDO: .env.example:1")

    def test_gitignore_incompleto(self):
        (self.proj / ".gitignore").write_text(".env\n")
        self.assertFalha("GITIGNORE: falta 'CLAUDE.local.md'")

    def test_fase_invalida(self):
        (self.proj / ".intellix-phase").write_text("fase-x\n")
        self.assertFalha("INVÁLIDO: .intellix-phase")

    @unittest.skipUnless(TEMPLATES.is_dir(), "plugin intellix não encontrado")
    def test_rascunho_de_arquitetura_bloqueia_fase_arch(self):
        self.assertIn("intellix-rascunho-kickoff", (self.proj / "references/architecture.md").read_text())
        self.assertFalha("PENDENTE: references/architecture.md", "--fase", "arch")

    def test_uso_invalido_sai_com_2(self):
        rc, _ = check(self.proj, "--fase", "qualquer")
        self.assertEqual(rc, 2)
        r = subprocess.run([sys.executable, str(CHECK), "/nao/existe"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)


@unittest.skipUnless((PLUGIN / "hooks/scripts/phase-gate.sh").is_file(), "phase-gate.sh não encontrado")
class TestPhaseGate(Base):
    def gate(self, fase: str):
        r = subprocess.run(["bash", str(PLUGIN / "hooks/scripts/phase-gate.sh"), fase],
                           cwd=self.proj, capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout + r.stderr

    def test_plan_bloqueia_com_rascunho_e_libera_apos_fase_01(self):
        (self.proj / "issues/001-exemplo.md").write_text("# issue\n")
        rc, out = self.gate("plan")
        self.assertEqual(rc, 1, out)
        self.assertIn("rascunho do kickoff", out)
        arq = self.proj / "references/architecture.md"
        arq.write_text("\n".join(l for l in arq.read_text().splitlines() if "intellix-rascunho-kickoff" not in l))
        rc, out = self.gate("plan")
        self.assertEqual(rc, 0, out)

    def test_plan_bloqueia_sem_issues(self):
        rc, out = self.gate("plan")
        self.assertEqual(rc, 1)
        self.assertIn("issues/", out)

    def _arquitetura_definida(self):
        arq = self.proj / "references/architecture.md"
        arq.write_text("\n".join(l for l in arq.read_text().splitlines() if "intellix-rascunho-kickoff" not in l))

    def test_deploy_bloqueia_logo_apos_o_kickoff(self):
        """Achado do teste E2E de 2026-09-16: o gate de deploy passava logo após o
        kickoff (security.md do template + tests/ com subpastas vazias)."""
        (self.proj / "tests/unit").mkdir(parents=True)
        rc, out = self.gate("deploy")
        self.assertEqual(rc, 1, out)
        self.assertIn("rascunho do kickoff", out)
        self.assertIn("tests/", out)

    def test_deploy_libera_com_arquitetura_e_testes(self):
        self._arquitetura_definida()
        (self.proj / "tests/unit").mkdir(parents=True)
        (self.proj / "tests/unit/a.test.ts").write_text("x")
        rc, out = self.gate("deploy")
        self.assertEqual(rc, 0, out)

    def test_handoff_exige_readme_e_registro_de_deploy(self):
        rc, out = self.gate("handoff")
        self.assertEqual(rc, 1)
        self.assertIn("docs/deploys.jsonl", out)
        (self.proj / "docs").mkdir()
        (self.proj / "docs/deploys.jsonl").write_text('{"resultado": "sucesso"}\n')
        rc, out = self.gate("handoff")
        self.assertEqual(rc, 0, out)
        (self.proj / "README.md").unlink()
        rc, _ = self.gate("handoff")
        self.assertEqual(rc, 1)

if __name__ == "__main__":
    unittest.main(verbosity=1)
