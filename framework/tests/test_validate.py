import copy
import json
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
        cls.template = validate.load(validate.FRAMEWORK / "templates/TASK.yaml")
        cls.framework = validate.load(validate.FRAMEWORK / "framework.yaml")

    def write_task(self, directory: Path, task: dict, name: str = "TASK-001.yaml") -> Path:
        path = directory / name
        path.write_text(json.dumps(task, indent=2), encoding="utf-8")
        return path

    def test_repository_framework_is_valid(self):
        self.assertEqual(validate.validate_framework(), [])

    def test_valid_task_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_task(Path(temporary), self.template)
            _, errors = validate.validate_task(path, self.framework)
            self.assertEqual(errors, [])

    def test_same_executor_and_reviewer_fails(self):
        task = copy.deepcopy(self.template)
        task["ownership"]["reviewer"] = task["ownership"]["executor"]
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_task(Path(temporary), task)
            _, errors = validate.validate_task(path, self.framework)
            self.assertTrue(any("independent" in error for error in errors))

    def test_high_risk_requires_gates_and_rollback(self):
        task = copy.deepcopy(self.template)
        task["risk"]["level"] = "high"
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_task(Path(temporary), task)
            _, errors = validate.validate_task(path, self.framework)
            self.assertTrue(any("requires gates" in error for error in errors))
            self.assertTrue(any("rollback" in error for error in errors))

    def test_forbidden_overlap_fails(self):
        task = copy.deepcopy(self.template)
        task["scope"]["create"] = ["infra/production/main.tf"]
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_task(Path(temporary), task)
            _, errors = validate.validate_task(path, self.framework)
            self.assertTrue(any("overlaps forbidden" in error for error in errors))

    def test_active_fileset_collision_fails(self):
        left = copy.deepcopy(self.template)
        right = copy.deepcopy(self.template)
        left.update(id="TASK-101", status="READY")
        right.update(id="TASK-102", status="IN_PROGRESS")
        right["scope"]["create"] = []
        right["scope"]["modify"] = ["src/example.ts"]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.write_task(directory, left, "TASK-101.yaml")
            self.write_task(directory, right, "TASK-102.yaml")
            errors = validate.validate_tasks(directory)
            self.assertTrue(any("fileset collision" in error for error in errors))

    def test_legacy_phase_gate_accepts_task_contract(self):
        gate = validate.ROOT / "hooks/scripts/phase-gate.sh"
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".intellix-phase").write_text("dev\n", encoding="utf-8")
            (project / "references").mkdir()
            (project / "references/architecture.md").write_text("# Approved\n", encoding="utf-8")
            (project / "tasks").mkdir()
            self.write_task(project / "tasks", self.template)
            result = subprocess.run(
                ["bash", str(gate), "execute"], cwd=project,
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
