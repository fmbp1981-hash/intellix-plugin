import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync  # noqa: E402
import validate  # noqa: E402
import worktrees  # noqa: E402


class WorktreeTests(unittest.TestCase):
    fixture = Path(__file__).parent / "fixtures/projects/valid"

    def project(self, parent: Path):
        root = parent / "consumer"
        shutil.copytree(self.fixture, root)
        sync.install_snapshot(validate.CODE_ROOT, root)
        subprocess.run(["git", "init", "-b", "feat/test"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)
        context = validate.build_context(root)
        task = validate.load(root / "tasks/TASK-101.yaml")
        task["risk"]["level"] = "medium"
        task["gates"].extend(["fileset", "worktree"])
        return context, task

    def test_runtime_artifacts_do_not_dirty_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task = self.project(Path(temporary))
            worktrees.reserve(context, task, Path(temporary) / "wt", "feat/test", "a" * 40, "codex")
            self.assertEqual(worktrees.git(context.root, "status", "--porcelain"), "")

    def test_collision_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task = self.project(Path(temporary))
            worktrees.reserve(context, task, Path(temporary) / "one", "feat/test", "a" * 40, "codex")
            other = json.loads(json.dumps(task)); other["id"] = "TASK-102"
            with self.assertRaisesRegex(validate.ValidationError, "collision"):
                worktrees.reserve(context, other, Path(temporary) / "two", "feat/test", "a" * 40, "codex")

    def test_prepare_and_dirty_release_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task = self.project(Path(temporary))
            destination = Path(temporary) / "consumer-TASK-101"
            record = worktrees.prepare(context, task, "codex", destination)
            self.assertEqual(record["state"], "reserved")
            dirty = destination / "dirty.txt"; dirty.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(validate.ValidationError, "dirty"):
                worktrees.release(context, task["id"])
            self.assertTrue(destination.exists())
            dirty.unlink()
            released = worktrees.release(context, task["id"])
            self.assertEqual(released["state"], "released")
            self.assertFalse(destination.exists())

    def test_dirty_source_and_arbitrary_destination_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task = self.project(Path(temporary))
            with self.assertRaisesRegex(validate.ValidationError, "derived"):
                worktrees.prepare(context, task, "codex", Path(temporary) / "arbitrary")
            dirty = context.root / "dirty.txt"; dirty.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(validate.ValidationError, "dirty"):
                worktrees.prepare(context, task, "codex")

    def test_destructive_git_operations_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, _ = self.project(Path(temporary))
            with self.assertRaisesRegex(validate.ValidationError, "forbidden"):
                worktrees.git(context.root, "reset", "--hard")
            with self.assertRaisesRegex(validate.ValidationError, "forbidden"):
                worktrees.git(context.root, "worktree", "remove", "--force", "x")


if __name__ == "__main__": unittest.main()
