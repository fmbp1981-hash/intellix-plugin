import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adapters  # noqa: E402
import sync  # noqa: E402
import validate  # noqa: E402


class AdapterArtifactTests(unittest.TestCase):
    fixture = Path(__file__).parent / "fixtures/projects/valid"

    def context(self, parent: Path):
        root = parent / "consumer"
        shutil.copytree(self.fixture, root)
        sync.install_snapshot(validate.CODE_ROOT, root)
        return validate.build_context(root)

    def checkpoint(self):
        return {
            "schema_version": "1.0.0", "task": "TASK-101", "state": "IN_PROGRESS",
            "context": "adapter tests", "last_command": "python -m unittest",
            "last_result": "PASS", "stop_point": "after artifacts", "open_risks": [],
            "active_plan": "continue tests", "next_actions": ["review"],
            "branch": "feat/test", "worktree": "/tmp/worktree", "commit": "a" * 40,
            "recovery_command": "git status", "timestamp": "2026-09-17T00:00:00Z"
        }

    def test_checkpoint_requires_complete_structured_context(self):
        with tempfile.TemporaryDirectory() as temporary:
            context = self.context(Path(temporary))
            path = adapters.write_checkpoint(context, self.checkpoint())
            self.assertTrue(path.is_file())
            incomplete = self.checkpoint(); incomplete.pop("active_plan")
            with self.assertRaisesRegex(validate.ValidationError, "active_plan"):
                adapters.write_checkpoint(context, incomplete)

    def test_handoff_is_read_only_and_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            context = self.context(Path(temporary))
            value = {
                "task": "TASK-101", "task_digest": "sha256:" + "0" * 64,
                "commit": "a" * 40, "diff_ref": "git diff base..head",
                "from": "executor", "to": "reviewer", "from_identity": "codex-1",
                "to_identity": "claude-1", "access": "read-only", "status": "ready",
                "summary": "Ready for bounded independent review.", "changed_files": ["x.py"],
                "evidence": ["tests pass"], "open_risks": [], "next_action": "review",
                "checkpoint_ref": ".intellix/runtime/checkpoints/TASK-101.json"
            }
            self.assertTrue(adapters.write_handoff(context, value).is_file())
            value["to_identity"] = "codex-2"
            with self.assertRaisesRegex(validate.ValidationError, "not independent"):
                adapters.write_handoff(context, value)
            value["to_identity"] = "claude-1"; value["access"] = "write"
            with self.assertRaisesRegex(validate.ValidationError, "read-only"):
                adapters.write_handoff(context, value)


if __name__ == "__main__": unittest.main()
