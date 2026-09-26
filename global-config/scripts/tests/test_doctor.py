#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes do doctor.py com fixtures isoladas (lote P0-2, 2026-09-16).

Cada teste monta uma raiz mínima e coerente num diretório temporário
(INTELLIX_ROOT), confirma que o doctor sai limpo nela e então reintroduz UM
defeito, exigindo que o doctor o detecte. Nada é escrito em ~/.claude — a versão
anterior destes testes criava arquivos temporários dentro da config real.

O teste de integração com o ambiente real (TestAmbienteReal) só roda com
INTELLIX_DOCTOR_LIVE=1, porque o resultado depende do estado da máquina.

Rodar:  python3 scripts/tests/test_doctor.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

DOCTOR = Path(__file__).resolve().parent.parent / "doctor.py"

METODOLOGIA = """\
versao: 1
stack:
  deploy: Cloudflare (Workers/Pages)
fases:
  - id: "00"
    nome: Kickoff
    skill: alpha
versoes:
  intellix: "1.0.0"
  devsecops: "1.0.0"
aliases_legados:
  - antigo: "nome-antigo"
    canonico: "intellix:alpha"
artefatos_projeto:
  sempre:
    - references/architecture.md
dependencias_globais:
  - modules/dep.md
skills_autorais_globais:
  - beta
agentes:
  implementadores: [writer]
"""

SESSION_START = """\
#!/bin/bash
cat <<EOF
  <intellix-phases>
    - intellix:alpha   → fase 00: kickoff
  </intellix-phases>
  <complementary-skills>
    - beta             → skill global
  </complementary-skills>
EOF
"""


def _manifest(name: str, ver: str) -> dict:
    return {"name": name, "version": ver, "skills": "./skills/", "commands": "./commands/"}


def _marketplace(mkt: str, name: str, ver: str) -> dict:
    return {"name": mkt, "plugins": [{"name": name, "source": "./", "version": ver}]}


def build_root(base: Path) -> Path:
    """Raiz mínima e sem achados."""
    files = {
        "metodologia.yaml": METODOLOGIA,
        "modules/dev-rules.md": "| Deploy | Cloudflare (Workers/Pages) |\n",
        "modules/dep.md": "dependência global\n",
        "modules/new-skills-triggers.md": "#### `intellix:alpha`\nInvocar quando: x\n",
        "skills/beta/SKILL.md": "---\nname: beta\n---\nconteúdo\n",
        "settings.json": json.dumps({"enabledPlugins": {
            "intellix@intellix-plugin": True, "devsecops@devsecops-plugin": True}}),
        "plugins/installed_plugins.json": json.dumps({"version": 2, "plugins": {}}),
        "plugins/marketplaces/intellix-plugin/.claude-plugin/plugin.json":
            json.dumps(_manifest("intellix", "1.0.0")),
        "plugins/marketplaces/intellix-plugin/.claude-plugin/marketplace.json":
            json.dumps(_marketplace("intellix-plugin", "intellix", "1.0.0")),
        "plugins/marketplaces/intellix-plugin/README.md": "# IntelliX Engineering Plugin v1.0\n",
        "plugins/marketplaces/intellix-plugin/skills/alpha/SKILL.md":
            "---\nname: alpha\n---\nLeia `references/architecture.md` e `references/padrao.md`.\n"
            "Use `~/.claude/modules/dep.md`. Depois `Skill(\"beta\")`.\n",
        "plugins/marketplaces/intellix-plugin/commands/run.md": "---\ndescription: roda\n---\n",
        "plugins/marketplaces/intellix-plugin/references/padrao.md": "padrão\n",
        "plugins/marketplaces/intellix-plugin/agents/writer.md": "---\nname: writer\ndescription: x\n---\n",
        "plugins/marketplaces/intellix-plugin/hooks/scripts/session-start.sh": SESSION_START,
        "plugins/marketplaces/intellix-plugin/hooks/scripts/phase-gate.sh":
            'exigir_arquivo "references/architecture.md" "motivo"\n',
        "plugins/marketplaces/devsecops-plugin/.claude-plugin/plugin.json":
            json.dumps(_manifest("devsecops", "1.0.0")),
        "plugins/marketplaces/devsecops-plugin/.claude-plugin/marketplace.json":
            json.dumps(_marketplace("devsecops-plugin", "devsecops", "1.0.0")),
        "plugins/marketplaces/devsecops-plugin/skills/gate/SKILL.md": "---\nname: gate\n---\nok\n",
    }
    for rel, content in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return base


def run_doctor(root: Path, *args: str) -> tuple[int, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("INTELLIX_")}
    env["INTELLIX_ROOT"] = str(root)
    r = subprocess.run(
        [sys.executable, str(DOCTOR), "--strict", *args],
        capture_output=True, text=True, timeout=60, env=env,
    )
    return r.returncode, r.stdout + r.stderr


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = build_root(Path(self._tmp.name))
        self.ix = self.root / "plugins/marketplaces/intellix-plugin"

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel: str, content: str, base: Path | None = None) -> Path:
        p = (base or self.root) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p

    def assertAchado(self, trecho: str):
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 1, f"--strict deveria falhar:\n{out}")
        self.assertIn(trecho, out)
        self.assertNotIn("Traceback", out)


class TestLinhaDeBase(Base):
    def test_fixture_limpa(self):
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)
        self.assertIn("consistente", out)

    def test_sem_strict_sempre_exit_0(self):
        self.write("modules/x.md", 'Skill("fantasma-xyz")\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith("INTELLIX_")}
        env["INTELLIX_ROOT"] = str(self.root)
        r = subprocess.run([sys.executable, str(DOCTOR)], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("fantasma-xyz", r.stdout)

    def test_yaml_quebrado_nao_lanca_excecao(self):
        self.write("metodologia.yaml", "fases: [\n")
        rc, out = run_doctor(self.root)
        self.assertNotIn("Traceback", out)
        self.assertIn("metodologia.yaml", out)


class TestReferencias(Base):
    def test_skill_inexistente(self):
        self.write("modules/x.md", 'Invoque `Skill("skill-que-nunca-existiu-xyz")`\n')
        self.assertAchado("skill-que-nunca-existiu-xyz")

    def test_namespace_inexistente(self):
        self.write("modules/x.md", "Use intellix:fantasma para isso.\n")
        self.assertAchado("`intellix:fantasma` não existe")

    def test_nome_antigo_em_nota_de_legado_e_aceito(self):
        self.write("modules/x.md", "O antigo intellix:fantasma (legado) foi absorvido.\n")
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_placeholder_ignorado(self):
        self.write("modules/x.md", 'Exemplo: `Skill("nome")`\n')
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_plugin_desabilitado_nao_conta(self):
        """Causa do falso verde de 2026-09-16: skill de plugin não habilitado
        passava como existente."""
        cache = self.root / "plugins/cache/mkt/extra/1.0"
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "extra", "version": "1.0"}), cache)
        self.write("skills/so-no-extra/SKILL.md", "---\nname: so-no-extra\n---\n", cache)
        inst = {"version": 2, "plugins": {"extra@mkt": [{"version": "1.0", "installPath": str(cache)}]}}
        self.write("plugins/installed_plugins.json", json.dumps(inst))
        self.write("modules/x.md", 'Skill("so-no-extra")\n')
        self.assertAchado("so-no-extra")
        # habilitado → passa a existir
        s = json.loads((self.root / "settings.json").read_text())
        s["enabledPlugins"]["extra@mkt"] = True
        self.write("settings.json", json.dumps(s))
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_manifest_com_lista_de_skills(self):
        cache = self.root / "plugins/cache/mkt/lista/1.0"
        self.write(".claude-plugin/plugin.json", json.dumps(
            {"name": "lista", "version": "1.0", "skills": ["./skills/eng/publicada"]}), cache)
        self.write("skills/eng/publicada/SKILL.md", "---\nname: publicada\n---\n", cache)
        self.write("skills/rascunho/nao-publicada/SKILL.md", "---\nname: nao-publicada\n---\n", cache)
        inst = {"version": 2, "plugins": {"lista@mkt": [{"version": "1.0", "installPath": str(cache)}]}}
        self.write("plugins/installed_plugins.json", json.dumps(inst))
        s = json.loads((self.root / "settings.json").read_text())
        s["enabledPlugins"]["lista@mkt"] = True
        self.write("settings.json", json.dumps(s))
        self.write("modules/x.md", "Use lista:publicada e lista:nao-publicada.\n")
        rc, out = run_doctor(self.root)
        self.assertIn("lista:nao-publicada", out)
        self.assertNotIn("lista:publicada`", out)

    def test_symlink_de_topo_reconhecido(self):
        alvo = self.write("fora/linkada/SKILL.md", "---\nname: linkada\n---\n").parent
        (self.root / "skills/linkada").symlink_to(alvo)
        self.write("modules/x.md", 'Skill("linkada") e Skill("beta")\n')
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_symlink_quebrado(self):
        (self.root / "skills/quebrado").symlink_to(self.root / "nao-existe")
        self.assertAchado("symlink quebrado")


class TestNovosChecks(Base):
    def test_09_reference_inexistente(self):
        self.write("skills/alpha/SKILL.md", "---\nname: alpha\n---\nLeia `references/DESIGN.md`.\n", self.ix)
        self.assertAchado("`references/DESIGN.md` não existe")

    def test_09_link_relativo_quebrado(self):
        self.write("references/padrao.md", "Ver [loop](verification-loop.md).\n", self.ix)
        self.assertAchado("link para arquivo inexistente `verification-loop.md`")

    def test_09_modulo_nao_declarado(self):
        self.write("modules/outro.md", "x\n")
        self.write("commands/run.md", "Ver `modules/outro.md`.\n", self.ix)
        self.assertAchado("não declarado em dependencias_globais")

    def test_10_frontmatter_diferente_da_pasta(self):
        self.write("skills/alpha/SKILL.md", "---\nname: alpha-workflow\n---\n", self.ix)
        self.assertAchado("pasta `alpha` declara name: `alpha-workflow`")

    def test_11_versao_divergente(self):
        self.write(".claude-plugin/marketplace.json",
                   json.dumps(_marketplace("intellix-plugin", "intellix", "0.9.0")), self.ix)
        self.assertAchado("marketplace.json=0.9.0")

    def test_11_registro_com_install_path_inexistente(self):
        inst = {"version": 2, "plugins": {"intellix@intellix-plugin": [
            {"version": "0.1.0", "installPath": str(self.root / "sumiu")}]}}
        self.write("plugins/installed_plugins.json", json.dumps(inst))
        self.assertAchado("installPath inexistente")

    def test_11_cabecalho_com_versao_velha(self):
        self.write("README.md", "# IntelliX Engineering Plugin v3.0\n", self.ix)
        self.assertAchado("cita v3.0")

    def test_12_nome_legado(self):
        self.write("modules/x.md", "Rode nome-antigo agora.\n")
        self.assertAchado("nome legado `nome-antigo`")

    def test_12_legado_em_tabela_de_compatibilidade(self):
        self.write("modules/x.md", "| nome-antigo | intellix:alpha | alias legado |\n")
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_13_lista_do_banner(self):
        self.write("hooks/scripts/session-start.sh",
                   SESSION_START.replace("beta ", "ckm-ui-styling "), self.ix)
        self.assertAchado("`ckm-ui-styling`")

    def test_13_aviso_manual_inexistente(self):
        self.write("modules/new-skills-triggers.md",
                   "#### `intellix:alpha`\n> rode /core-web-vitals antes\n")
        self.assertAchado("`/core-web-vitals`")

    def test_13_router_sugere_skill_nao_invocavel(self):
        self.write("skills/alpha/SKILL.md",
                   "---\nname: alpha\ndisable-model-invocation: true\n---\n", self.ix)
        self.write("scripts/intellix-skill-router.py", 'RULES = [(50, "intellix:alpha", r"x", "y")]\n')
        self.assertAchado("disable-model-invocation")

    def test_14_gate_exige_artefato_nao_declarado(self):
        self.write("hooks/scripts/phase-gate.sh", 'exigir_arquivo "references/DESIGN.md" "m"\n', self.ix)
        self.assertAchado("phase-gate exige `references/DESIGN.md`")

    def test_15_dependencia_global_ausente(self):
        (self.root / "modules/dep.md").unlink()
        self.assertAchado("dependência global declarada não existe: modules/dep.md")

    def test_16_vercel_como_deploy(self):
        self.write("references/padrao.md", "- **Hospedagem:** Vercel\n", self.ix)
        self.assertAchado("Vercel como deploy")

    def test_16_vercel_em_regex_de_roteamento_e_aceito(self):
        self.write("hooks/scripts/router.sh", 'echo "$P" | grep -qiE "deploy|vercel --prod"\n', self.ix)
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_16_skill_autoral_global_policiada(self):
        self.write("skills/beta/ref.md", "| Deploy | Vercel |\n")
        self.assertAchado("Vercel como deploy: skills/beta/ref.md")

    def test_17_diretorio_acidental(self):
        (self.ix / "{skills,hooks").mkdir()
        self.assertAchado("nome acidental")

    def test_17_backup_solto(self):
        self.write("hooks/scripts/router.sh.bak", "x\n", self.ix)
        self.assertAchado("backup solto")

    def test_18_skill_e_comando_com_mesmo_id(self):
        self.write("commands/alpha.md", "---\ndescription: x\n---\n", self.ix)
        self.assertAchado("intellix:alpha é ao mesmo tempo skill e comando")

    def test_19_fase_do_banner_divergente(self):
        self.write("hooks/scripts/session-start.sh",
                   SESSION_START.replace("fase 00", "fase 03"), self.ix)
        self.assertAchado("banner diz fase 03=alpha")

    def test_03_skill_solta_sombreando_plugin(self):
        cache = self.root / "plugins/cache/mkt/extra/1.0"
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "extra", "version": "1.0"}), cache)
        self.write("skills/beta/SKILL.md", "---\nname: beta\n---\n", cache)
        inst = {"version": 2, "plugins": {"extra@mkt": [{"version": "1.0", "installPath": str(cache)}]}}
        self.write("plugins/installed_plugins.json", json.dumps(inst))
        s = json.loads((self.root / "settings.json").read_text())
        s["enabledPlugins"]["extra@mkt"] = True
        self.write("settings.json", json.dumps(s))
        self.assertAchado('"beta" existe solta em skills/ e em extra:beta')

    def test_08_agente_do_contrato_ausente(self):
        (self.ix / "agents/writer.md").unlink()
        self.assertAchado("agente 'writer' do contrato")

    def test_08_auditoria_com_skill_inexistente(self):
        self.write("metodologia.yaml", METODOLOGIA + "auditorias:\n  - perfil: entrada\n    skill: intellix:sumiu\n")
        self.assertAchado("auditoria 'entrada' aponta para skill que não carrega: 'intellix:sumiu'")

    def test_20_hook_de_contexto_async(self):
        hooks = {"hooks": {"UserPromptSubmit": [{"matcher": "*", "hooks": [
            {"type": "command", "command": "bash x.sh", "async": True}]}]}}
        self.write("hooks/hooks.json", json.dumps(hooks), self.ix)
        self.assertAchado("hook de UserPromptSubmit com async:true")

    def test_20_hook_de_ferramenta_async_e_aceito(self):
        hooks = {"hooks": {"PostToolUse": [{"matcher": "*", "hooks": [
            {"type": "command", "command": "bash x.sh", "async": True}]}]}}
        self.write("hooks/hooks.json", json.dumps(hooks), self.ix)
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def _instalar_copia(self):
        import shutil
        cache = self.root / "plugins/cache/intellix-plugin/intellix/1.0.0"
        shutil.copytree(self.ix, cache)
        inst = {"version": 2, "plugins": {"intellix@intellix-plugin": [
            {"version": "1.0.0", "installPath": str(cache)}]}}
        self.write("plugins/installed_plugins.json", json.dumps(inst))
        return cache

    def test_05_copia_instalada_identica_passa(self):
        self._instalar_copia()
        rc, out = run_doctor(self.root)
        self.assertEqual(rc, 0, out)

    def test_05_copia_instalada_desatualizada(self):
        self._instalar_copia()
        self.write("skills/alpha/SKILL.md", "---\nname: alpha\n---\nmudou\n", self.ix)
        self.assertAchado("difere do fonte em 1 arquivo(s)")

    def test_05_versao_antiga_sem_registro(self):
        cache = self._instalar_copia()
        (cache.parent / "0.9.0").mkdir()
        self.assertAchado("versões antigas sem registro")

    def test_08_fase_aponta_para_skill_inexistente(self):
        self.write("metodologia.yaml", METODOLOGIA.replace("skill: alpha", "skill: omega"))
        self.assertAchado("fase 00 aponta para skill inexistente no plugin intellix: 'omega'")


@unittest.skipUnless(os.environ.get("INTELLIX_DOCTOR_LIVE") == "1",
                     "integração com a máquina real: INTELLIX_DOCTOR_LIVE=1")
class TestAmbienteReal(unittest.TestCase):
    def test_ambiente_real_limpo(self):
        r = subprocess.run([sys.executable, str(DOCTOR), "--strict"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, f"doctor achou deriva:\n{r.stdout}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
