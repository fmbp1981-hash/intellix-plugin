import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import dispatch  # noqa: E402
import sync  # noqa: E402
import validate  # noqa: E402


class DispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__file__).parent / "fixtures/projects/valid"

    def project(self, parent: Path):
        target = parent / "consumer"
        shutil.copytree(self.fixture, target)
        sync.install_snapshot(validate.CODE_ROOT, target)
        task_path = target / "tasks/TASK-101.yaml"
        task = validate.load(task_path)
        task["status"] = "READY"
        task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        return target, task_path, task

    def write(self, path: Path, value: dict):
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_explicit_executor_is_selected_and_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, _ = self.project(Path(temporary))
            event = dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(event["selected_adapter"], "codex")
            self.assertEqual(event["resolution"], "task-explicit")

    def test_project_default_is_used_without_explicit_executor(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["ownership"].pop("executor")
            self.write(task_path, task)
            event = dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(event["resolution"], "project-default")

    def test_legacy_claude_only_fallback_is_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["ownership"].pop("executor")
            task["ownership"]["reviewer"] = "human-reviewer"
            self.write(task_path, task)
            event = dispatch.dispatch(
                project,
                task_path,
                available={"claude"},
                current_adapter="claude",
            )
            self.assertEqual(event["selected_adapter"], "claude")
            self.assertEqual(event["resolution"], "current-adapter-fallback")

    def test_missing_explicit_adapter_blocks_with_durable_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, _ = self.project(Path(temporary))
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "not installed"):
                dispatch.dispatch(project, task_path, available={"claude"})
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")
            record = validate.load(project / ".intellix/runtime/TASK-101.json")
            self.assertIn("not installed", record["events"][-1]["reason"])

    def test_unresolved_dependency_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            dependency = dict(task)
            dependency["id"] = "TASK-102"
            dependency["status"] = "DRAFT"
            dependency["scope"] = {"create": ["src/other.py"], "modify": [], "forbidden": []}
            self.write(project / "tasks/TASK-102.yaml", dependency)
            task["dependencies"] = ["TASK-102"]
            self.write(task_path, task)
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "not satisfied"):
                dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")

    def test_fileset_collision_blocks_with_durable_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            conflicting = dict(task)
            conflicting["id"] = "TASK-102"
            self.write(project / "tasks/TASK-102.yaml", conflicting)
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "fileset collision"):
                dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")
            record = validate.load(project / ".intellix/runtime/TASK-101.json")
            self.assertIn("fileset collision", record["events"][-1]["reason"])

    def test_missing_risk_gate_blocks_with_durable_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["gates"].remove("tests")
            self.write(task_path, task)
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "requires gates"):
                dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")

    def test_claude_fallback_cannot_self_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["ownership"].pop("executor")
            self.write(task_path, task)
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "not independent"):
                dispatch.dispatch(
                    project,
                    task_path,
                    available={"claude"},
                    current_adapter="claude",
                )
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")

    def test_review_findings_return_to_in_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["status"] = "IN_REVIEW"
            self.write(task_path, task)
            event = dispatch.dispatch(
                project,
                task_path,
                available={"codex"},
                target_state="IN_PROGRESS",
                reason="review findings",
            )
            self.assertEqual(event["from"], "IN_REVIEW")
            self.assertEqual(event["to"], "IN_PROGRESS")

    def test_illegal_transition_becomes_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["status"] = "DRAFT"
            self.write(task_path, task)
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "illegal task transition"):
                dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")

    def test_guarded_transition_does_not_mutate_or_block_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, _ = self.project(Path(temporary))
            with self.assertRaisesRegex(
                dispatch.DispatchBlocked, "dedicated completion path"
            ):
                dispatch.dispatch(
                    project,
                    task_path,
                    available=set(),
                    target_state="APPROVED",
                )
            self.assertEqual(validate.load(task_path)["status"], "READY")
            self.assertFalse(
                (project / ".intellix/runtime/TASK-101.json").exists()
            )

    def test_medium_risk_dispatch_transitions_inside_dedicated_worktree(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path, task = self.project(Path(temporary))
            task["risk"]["level"] = "medium"
            task["gates"].extend(["fileset", "worktree"])
            self.write(task_path, task)
            subprocess.run(["git", "init", "-b", "feat/test"], cwd=project, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=project, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=project, check=True)
            subprocess.run(["git", "add", "."], cwd=project, check=True)
            subprocess.run(["git", "commit", "-m", "fixture"], cwd=project, check=True, capture_output=True)
            destination = Path(temporary) / "consumer-TASK-101"
            event = dispatch.dispatch(
                project,
                task_path,
                available={"codex"},
                worktree_destination=destination,
            )
            self.assertEqual(event["to"], "IN_PROGRESS")
            self.assertEqual(
                validate.load(destination / "tasks/TASK-101.yaml")["status"],
                "IN_PROGRESS",
            )
            self.assertEqual(validate.load(task_path)["status"], "READY")
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "rerun with --root"):
                dispatch.dispatch(
                    project,
                    task_path,
                    available={"codex"},
                    target_state="IN_PROGRESS",
                )
            self.assertEqual(validate.load(task_path)["status"], "READY")


if __name__ == "__main__":
    unittest.main()
