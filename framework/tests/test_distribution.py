import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate  # noqa: E402


class FrameworkDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__file__).parent / "fixtures/projects/valid"
        cls.sync = validate.CODE_ROOT / "framework/sync.py"
        cls.generator = validate.CODE_ROOT / "framework/generate_adapters.py"
        cls.validator = validate.CODE_ROOT / "framework/validate.py"

    def consumer(self, parent: Path, name: str = "consumer") -> Path:
        target = parent / name
        shutil.copytree(self.fixture, target)
        return target

    def run_script(self, script: Path, *arguments: str, cwd: Path | None = None):
        return subprocess.run(
            [sys.executable, str(script), *arguments],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    def sync_consumer(self, target: Path):
        return self.run_script(
            self.sync,
            "--source-root",
            str(validate.CODE_ROOT),
            "--target-root",
            str(target),
            cwd=target,
        )

    def validate_consumer(self, target: Path):
        return self.run_script(
            self.validator, "--root", str(target), "--all", cwd=target
        )

    def test_fresh_consumer_receives_valid_pinned_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            result = self.sync_consumer(target)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            lock = validate.load(target / "intellix.lock.json")
            self.assertRegex(lock["kernel"]["digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(lock["kernel"]["version"], "1.0.0")
            self.assertIn("framework/framework.yaml", lock["kernel"]["files"])
            self.assertIn("framework/dispatch.py", lock["control_plane"]["files"])
            self.assertIn("framework/runtime.py", lock["control_plane"]["files"])
            self.assertIn("framework/worktrees.py", lock["control_plane"]["files"])
            self.assertIn("framework/adapters.py", lock["control_plane"]["files"])
            self.assertIn("framework/ci.py", lock["control_plane"]["files"])
            self.assertIn("framework/completion.py", lock["control_plane"]["files"])
            self.assertTrue((target / "framework/dispatch.py").is_file())
            self.assertTrue((target / "framework/runtime.py").is_file())
            self.assertTrue((target / "framework/worktrees.py").is_file())
            self.assertTrue((target / "framework/adapters.py").is_file())
            self.assertTrue((target / "framework/ci.py").is_file())
            self.assertTrue((target / "framework/completion.py").is_file())
            self.assertTrue((target / "framework/schemas/ci-evidence.schema.json").is_file())
            self.assertTrue((target / "framework/schemas/review-evidence.schema.json").is_file())
            self.assertIn(
                ".intellix/runtime/",
                (validate.CODE_ROOT / "intellix-templates/root-template/.gitignore").read_text(encoding="utf-8"),
            )
            validation = self.validate_consumer(target)
            self.assertEqual(
                validation.returncode, 0, validation.stderr + validation.stdout
            )

    def test_missing_lock_blocks_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            (target / "intellix.lock.json").unlink()
            result = self.validate_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("framework.lock", result.stdout)
            self.assertIn("required source is missing", result.stdout)

    def test_tampered_kernel_blocks_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            role = target / "framework/roles/platform-engineer.yaml"
            role.write_text(role.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            result = self.validate_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("kernel.digest drift", result.stdout)

    def test_tampered_control_plane_blocks_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            dispatcher = target / "framework/dispatch.py"
            dispatcher.write_text(
                dispatcher.read_text(encoding="utf-8") + "\n", encoding="utf-8"
            )
            result = self.validate_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("control_plane.digest drift", result.stdout)

    def test_stale_lock_version_blocks_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            lock_path = target / "intellix.lock.json"
            lock = validate.load(lock_path)
            lock["kernel"]["version"] = "0.9.0"
            lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
            result = self.validate_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("kernel.version drift", result.stdout)

    def test_unknown_digest_algorithm_blocks_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            lock_path = target / "intellix.lock.json"
            lock = validate.load(lock_path)
            lock["kernel"]["digest"] = "md5:" + ("0" * 32)
            lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
            result = self.validate_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match", result.stdout)

    def test_symlinked_kernel_role_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            target = self.consumer(parent)
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            outside = parent / "outside-role.yaml"
            outside.write_text(
                (target / "framework/roles/platform-engineer.yaml").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            role = target / "framework/roles/platform-engineer.yaml"
            role.unlink()
            role.symlink_to(outside)
            result = self.validate_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("path escapes project root", result.stdout)

    def test_lock_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            manifest_path = target / "intellix.yaml"
            manifest = validate.load(manifest_path)
            manifest["framework"]["lock"] = "../intellix.lock.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            result = self.sync_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("path traversal is forbidden", result.stdout)

    def test_nul_in_lock_path_returns_structured_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            manifest_path = target / "intellix.yaml"
            manifest = validate.load(manifest_path)
            manifest["framework"]["lock"] = "bad\x00lock.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            result = self.sync_consumer(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NUL bytes are forbidden", result.stdout)
            self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_digest_is_deterministic_for_identical_snapshots(self):
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            left = self.consumer(parent, "left")
            right = self.consumer(parent, "right")
            self.assertEqual(self.sync_consumer(left).returncode, 0)
            self.assertEqual(self.sync_consumer(right).returncode, 0)
            left_lock = validate.load(left / "intellix.lock.json")
            right_lock = validate.load(right / "intellix.lock.json")
            self.assertEqual(left_lock, right_lock)

    def test_sync_never_mutates_repository_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            source_context = validate.build_context(validate.CODE_ROOT)
            before = hashlib.sha256()
            for path in validate.kernel_manifest(source_context):
                before.update(path.read_bytes())
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            target_role = target / "framework/roles/platform-engineer.yaml"
            target_role.write_text("tampered\n", encoding="utf-8")
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            after = hashlib.sha256()
            for path in validate.kernel_manifest(source_context):
                after.update(path.read_bytes())
            self.assertEqual(before.digest(), after.digest())

    def test_generated_adapters_are_short_links_not_policy_copies(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            result = self.run_script(
                self.generator,
                "--source-root",
                str(validate.CODE_ROOT),
                "--target-root",
                str(target),
                cwd=target,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            for name in ("AGENTS.md", "CLAUDE.md"):
                content = (target / name).read_text(encoding="utf-8")
                self.assertIn("Generated by IntelliX", content)
                self.assertIn("framework/framework.yaml", content)
                self.assertLess(len(content), 700)
                self.assertNotIn("risk_gates", content)
                self.assertNotIn("human_approval_for", content)
            check = self.run_script(
                self.generator,
                "--source-root",
                str(validate.CODE_ROOT),
                "--target-root",
                str(target),
                "--check",
                cwd=target,
            )
            self.assertEqual(check.returncode, 0, check.stderr + check.stdout)

    def test_generator_refuses_unmarked_adapter_without_force(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = self.consumer(Path(temporary))
            self.assertEqual(self.sync_consumer(target).returncode, 0)
            user_content = (
                "# User-owned file\n\n"
                "<!-- Generated by IntelliX; edit the source template, not this file. -->\n"
            )
            (target / "AGENTS.md").write_text(user_content, encoding="utf-8")
            result = self.run_script(
                self.generator,
                "--source-root",
                str(validate.CODE_ROOT),
                "--target-root",
                str(target),
                cwd=target,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to overwrite", result.stdout)
            self.assertEqual(
                (target / "AGENTS.md").read_text(encoding="utf-8"),
                user_content,
            )


if __name__ == "__main__":
    unittest.main()
