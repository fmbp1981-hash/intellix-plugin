import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate  # noqa: E402


class FrameworkValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__file__).parent / "fixtures/projects/valid"
        cls.validator = validate.CODE_ROOT / "framework/validate.py"

    def external_project(self, parent: Path) -> Path:
        project = parent / "consumer"
        shutil.copytree(self.fixture, project)
        framework = project / "framework"
        framework.mkdir()
        shutil.copy2(validate.FRAMEWORK / "framework.yaml", framework / "framework.yaml")
        for directory in ("policies", "roles", "schemas"):
            shutil.copytree(validate.FRAMEWORK / directory, framework / directory)
        return project

    def context_and_task(self, parent: Path):
        project = self.external_project(parent)
        context = validate.build_context(project)
        task_path = project / "tasks/TASK-101.yaml"
        task = validate.load(task_path)
        return project, context, task_path, task

    def write_json(self, path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def run_validator(self, *arguments: str, cwd: Path | None = None):
        return subprocess.run(
            [sys.executable, str(self.validator), *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_repository_framework_is_valid(self):
        context = validate.build_context(validate.CODE_ROOT)
        self.assertEqual(validate.validate_framework(context), [])
        self.assertEqual(validate.validate_project(context=context), [])
        self.assertEqual(validate.validate_authority(context), [])

    def test_external_project_validates_from_explicit_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.external_project(Path(temporary))
            result = self.run_validator("--root", str(project), "--all", cwd=Path(temporary))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_validation_is_independent_of_shell_working_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            project = self.external_project(parent)
            unrelated = parent / "unrelated"
            unrelated.mkdir()
            result = self.run_validator("--root", str(project), "--all", cwd=unrelated)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_no_silent_plugin_root_fallback_outside_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_validator("--all", cwd=Path(temporary))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--root is required", result.stdout)

    def test_nonexistent_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing"
            result = self.run_validator("--root", str(missing), "--all", cwd=Path(temporary))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("project root does not exist", result.stdout)

    def test_framework_source_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.external_project(Path(temporary))
            manifest = validate.load(project / "intellix.yaml")
            manifest["framework"]["source"] = "../framework/framework.yaml"
            self.write_json(project / "intellix.yaml", manifest)
            result = self.run_validator("--root", str(project), "--all", cwd=project)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("path traversal is forbidden", result.stdout)

    def test_task_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["scope"]["create"] = ["../escape.py"]
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("path traversal is forbidden" in error for error in errors))

    def test_forbidden_absolute_contract_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["scope"]["modify"] = ["/tmp/escape.py"]
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("absolute paths are forbidden" in error for error in errors))

    def test_windows_absolute_contract_path_is_rejected_on_posix(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["scope"]["modify"] = ["C:\\outside\\escape.py"]
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("absolute paths are forbidden" in error for error in errors))

    def test_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            project, context, task_path, task = self.context_and_task(parent)
            outside = parent / "outside"
            outside.mkdir()
            (outside / "escaped.py").write_text("# outside\n", encoding="utf-8")
            (project / "linked").symlink_to(outside, target_is_directory=True)
            task["scope"]["modify"] = ["linked/escaped.py"]
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("path escapes project root" in error for error in errors))

    def test_unknown_domain_role_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["ownership"]["domain_role"] = "imaginary-engineer"
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("unknown domain role" in error for error in errors))

    def test_task_id_must_match_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["id"] = "TASK-999"
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("requires filename 'TASK-999.yaml'" in error for error in errors))

    def test_missing_task_sources_are_named(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["source"]["prd"] = "docs/missing-prd.md"
            task["source"]["spec"] = "docs/missing-spec.md"
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            joined = "\n".join(errors)
            self.assertIn("docs/missing-prd.md", joined)
            self.assertIn("docs/missing-spec.md", joined)

    def test_missing_project_sources_are_all_named(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.external_project(Path(temporary))
            manifest = validate.load(project / "intellix.yaml")
            manifest["documents"]["prd"] = "docs/missing-prd.md"
            manifest["documents"]["spec"] = "docs/missing-spec.md"
            self.write_json(project / "intellix.yaml", manifest)
            context = validate.build_context(project)
            joined = "\n".join(validate.validate_project(context=context))
            self.assertIn("docs/missing-prd.md", joined)
            self.assertIn("docs/missing-spec.md", joined)

    def test_framework_version_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.external_project(Path(temporary))
            manifest = validate.load(project / "intellix.yaml")
            manifest["framework"]["version"] = "9.9.9"
            self.write_json(project / "intellix.yaml", manifest)
            context = validate.build_context(project)
            errors = validate.validate_project(context=context)
            self.assertTrue(any("does not match kernel framework_version" in error for error in errors))

    def test_kernel_contains_no_vendor_adapter_or_plugin_version_facts(self):
        context = validate.build_context(validate.CODE_ROOT)
        self.assertNotIn("plugin_version", context.framework)
        self.assertFalse(validate.VENDOR_DEFAULTS.intersection(context.framework["defaults"]))
        roles = (context.root / context.framework["roles_directory"]).glob("*.yaml")
        for role_path in roles:
            self.assertNotIn("preferred_adapter", validate.load(role_path), role_path.name)

    def test_repository_to_installation_direction_is_enforced(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.external_project(Path(temporary))
            adapter = project / "global-config/metodologia.yaml"
            adapter.parent.mkdir()
            adapter.write_text(
                "framework_source: framework/framework.yaml\n"
                "framework_version: 1.0.0\n"
                "sync_direction: installation_to_repository\n",
                encoding="utf-8",
            )
            errors = validate.validate_authority(validate.build_context(project))
            self.assertTrue(any("repository_to_installation" in error for error in errors))

    def test_same_executor_and_reviewer_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["ownership"]["reviewer"] = task["ownership"]["executor"]
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("independent" in error for error in errors))

    def test_high_risk_requires_gates_and_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["risk"]["level"] = "high"
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("requires gates" in error for error in errors))
            self.assertTrue(any("rollback" in error for error in errors))

    def test_forbidden_overlap_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, task = self.context_and_task(Path(temporary))
            task["scope"]["create"] = ["infra/production/main.tf"]
            self.write_json(task_path, task)
            _, errors = validate.validate_task(task_path, context)
            self.assertTrue(any("overlaps forbidden" in error for error in errors))

    def test_active_fileset_collision_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, left = self.context_and_task(Path(temporary))
            left.update(id="TASK-101", status="READY")
            right = copy.deepcopy(left)
            right.update(id="TASK-102", status="IN_PROGRESS")
            right["scope"]["create"] = []
            right["scope"]["modify"] = ["src/example.py"]
            self.write_json(task_path, left)
            self.write_json(project / "tasks/TASK-102.yaml", right)
            errors = validate.validate_tasks(project / "tasks", context)
            self.assertTrue(any("fileset collision" in error for error in errors))

    def test_approved_task_releases_fileset_for_dependent_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, context, task_path, completed = self.context_and_task(Path(temporary))
            completed.update(id="TASK-101", status="APPROVED")
            dependent = copy.deepcopy(completed)
            dependent.update(id="TASK-102", status="READY")
            dependent["dependencies"] = ["TASK-101"]
            self.write_json(task_path, completed)
            self.write_json(project / "tasks/TASK-102.yaml", dependent)
            errors = validate.validate_tasks(project / "tasks", context)
            self.assertFalse(any("fileset collision" in error for error in errors))

    def test_legacy_phase_gate_accepts_task_contract(self):
        gate = validate.CODE_ROOT / "hooks/scripts/phase-gate.sh"
        template = validate.load(validate.FRAMEWORK / "templates/TASK.yaml")
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".intellix-phase").write_text("dev\n", encoding="utf-8")
            (project / "references").mkdir()
            (project / "references/architecture.md").write_text("# Approved\n", encoding="utf-8")
            (project / "tasks").mkdir()
            self.write_json(project / "tasks/TASK-001.yaml", template)
            result = subprocess.run(
                ["bash", str(gate), "execute"],
                cwd=project,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
