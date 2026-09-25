import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "global-config/skills/intellix-decision-layer"
SKILL = SKILL_DIR / "SKILL.md"
NORMATIVE = SKILL_DIR / "references/decision-layer.md"
INFORMATIVE = SKILL_DIR / "references/engines-2026-09.md"
CANONICAL_PATH = "global-config/skills/intellix-decision-layer/SKILL.md"
PHASE_SKILLS = (
    ROOT / "global-config/skills/ai-project-brainstorm/SKILL.md",
    ROOT / "skills/architecture/SKILL.md",
    ROOT / "global-config/skills/intellix-agent-creation/SKILL.md",
)


class DecisionLayerIntegrationTests(unittest.TestCase):
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_canonical_files_are_tracked_and_phase_references_resolve(self):
        expected = (SKILL, NORMATIVE, INFORMATIVE)
        for path in expected:
            self.assertTrue(path.is_file(), path)
            relative = path.relative_to(ROOT).as_posix()
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", relative],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr or relative)

        for phase_skill in PHASE_SKILLS:
            text = self.read(phase_skill)
            self.assertIn("intellix-decision-layer", text)
            self.assertIn(CANONICAL_PATH, text)
            cited_paths = re.findall(
                r"`(global-config/skills/intellix-decision-layer/[^`]+)`", text
            )
            self.assertTrue(cited_paths, phase_skill)
            for cited in cited_paths:
                self.assertTrue((ROOT / cited).is_file(), cited)

    def test_location_frontmatter_and_installation_boundary_are_canonical(self):
        frontmatter = self.read(SKILL).split("---", 2)[1]
        match = re.search(r"(?m)^name:\s*(\S+)\s*$", frontmatter)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), SKILL_DIR.name)
        self.assertFalse((ROOT / "skills/intellix-decision-layer").exists())

        repository_text = "\n".join(
            self.read(path)
            for path in (
                SKILL,
                NORMATIVE,
                INFORMATIVE,
                *PHASE_SKILLS,
                ROOT / "global-config/metodologia.yaml",
                ROOT / "global-config/README.md",
            )
        )
        self.assertNotIn("intellix:intellix-decision-layer", repository_text)
        readme = self.read(ROOT / "global-config/README.md")
        self.assertIn(
            'cp -R "$PLUGIN/global-config/skills/intellix-decision-layer"', readme
        )
        self.assertIn("ação humana explícita", readme)
        self.assertIn("nunca copiam automaticamente", readme)

    def test_normative_files_have_no_volatile_vendor_facts(self):
        normative = f"{self.read(SKILL)}\n{self.read(NORMATIVE)}"
        lowered = normative.casefold()
        for forbidden in (
            "laya",
            "jev",
            "typesafe",
            "huggingface",
            "pypi.org",
            "http://",
            "https://",
            "benchmark",
            "latência",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIsNone(re.search(r"\b\d+\.\d+\.\d+\b", normative))
        self.assertIsNone(re.search(r"(?:R\$|US\$|\$)\s*\d", normative))
        self.assertIn("Defaults configuráveis, nunca universais", normative)
        self.assertIn("Pontos de partida configuráveis", normative)

        informative = self.read(INFORMATIVE)
        self.assertIn("2026-09-24", informative)
        self.assertIn("reverificar tudo na data de uso", informative)
        self.assertIn("não ordena, recomenda nem escolhe motor", informative)
        self.assertRegex(informative, r"não\s+é evidência de produção")
        self.assertRegex(informative, r"(?i)documentação oficial|alegação do autor")
        self.assertIn(
            "global-config/skills/intellix-decision-layer/references/engines-2026-09.md",
            self.read(SKILL),
        )

    def test_skill_is_methodology_only(self):
        files = tuple(path for path in SKILL_DIR.rglob("*") if path.is_file())
        self.assertEqual({path.suffix for path in files}, {".md"})
        text = "\n".join(self.read(path) for path in files)
        for forbidden_pattern in (
            r"(?i)\b(?:CREATE|ALTER|DROP)\s+TABLE\b",
            r"(?i)\b(?:API_KEY|ACCESS_TOKEN|CLIENT_SECRET|DATABASE_URL)\b",
            r"\b(?:process\.env|os\.environ|getenv)\b",
            r"(?m)^\s*(?:pip|npm|pnpm|yarn|docker|curl)\s+(?:install|run|build|pull)",
        ):
            self.assertIsNone(re.search(forbidden_pattern, text), forbidden_pattern)
        self.assertIn("não cria adapter", self.read(SKILL))
        self.assertIn("nunca a esta metodologia global", self.read(NORMATIVE))

    def test_methodology_registration_and_versions_are_consistent(self):
        methodology = self.read(ROOT / "global-config/metodologia.yaml")
        author_skills = methodology.split("skills_autorais_globais:", 1)[1].split(
            "\n\n", 1
        )[0]
        dependencies = methodology.split("dependencias_globais:", 1)[1].split(
            "\n\n", 1
        )[0]
        self.assertIn("- intellix-decision-layer", author_skills)
        self.assertNotIn("intellix-decision-layer", dependencies)

        plugin_version = json.loads(
            self.read(ROOT / ".claude-plugin/plugin.json")
        )["version"]
        marketplace_version = json.loads(
            self.read(ROOT / ".claude-plugin/marketplace.json")
        )["plugins"][0]["version"]
        methodology_version = re.search(
            r'(?m)^\s+intellix:\s+"([^"]+)"$', methodology
        ).group(1)
        self.assertEqual(
            (plugin_version, marketplace_version, methodology_version),
            ("3.2.0", "3.2.0", "3.2.0"),
        )

    def test_doctor_accepts_fixture_with_real_skill_directory(self):
        doctor_tests = ROOT / "global-config/scripts/tests/test_doctor.py"
        spec = importlib.util.spec_from_file_location("intellix_test_doctor", doctor_tests)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temporary:
            fixture = module.build_root(Path(temporary))
            target = fixture / "skills/intellix-decision-layer"
            shutil.copytree(SKILL_DIR, target)
            methodology_path = fixture / "metodologia.yaml"
            methodology = methodology_path.read_text(encoding="utf-8").replace(
                "skills_autorais_globais:\n  - beta\n",
                "skills_autorais_globais:\n  - beta\n  - intellix-decision-layer\n",
            )
            methodology_path.write_text(methodology, encoding="utf-8")
            returncode, output = module.run_doctor(fixture, "--quiet")
            self.assertEqual(returncode, 0, output)
            self.assertNotIn("Traceback", output)


if __name__ == "__main__":
    unittest.main()
