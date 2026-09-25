import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adapters  # noqa: E402
import ci  # noqa: E402
import runtime  # noqa: E402
import sync  # noqa: E402
import validate  # noqa: E402


REVISION = "c" * 40


class PortablePilotTests(unittest.TestCase):
    fixture = Path(__file__).parent / "fixtures/projects/valid"
    profiles = Path(__file__).parent / "fixtures/pilot"
    validator = validate.CODE_ROOT / "framework/validate.py"
    dispatcher = validate.CODE_ROOT / "framework/dispatch.py"
    ci_command = validate.CODE_ROOT / "framework/ci.py"

    def write_json(self, path, value):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def project(self, parent, profile):
        root = parent / f"pilot-{profile['governance_profile']}"
        shutil.copytree(self.fixture, root)
        manifest_path = root / "intellix.yaml"
        manifest = validate.load(manifest_path)
        manifest["project"]["governance_profile"] = profile["governance_profile"]
        self.write_json(manifest_path, manifest)
        sync.install_snapshot(validate.CODE_ROOT, root)
        task_path = root / "tasks/TASK-101.yaml"
        task = validate.load(task_path)
        task["status"] = "READY"
        task["gates"] = profile["task_gates"]
        self.write_json(task_path, task)
        return root, task_path

    def github_success(self, request):
        self.assertIn("/repos/example/external-consumer/commits/", request.full_url)
        check = {
            "name": "project-ci",
            "head_sha": REVISION,
            "status": "completed",
            "conclusion": "success",
            "details_url": "https://github.example/check/pilot",
            "completed_at": "2026-09-18T12:00:00Z",
        }
        return 200, {}, json.dumps({"total_count": 1, "check_runs": [check]}).encode()

    def checkpoint(self, root):
        return {
            "schema_version": "1.0.0",
            "task": "TASK-101",
            "state": "IN_PROGRESS",
            "context": "portable end-to-end pilot",
            "last_command": "dispatch --root <pilot>",
            "last_result": "PASS",
            "stop_point": "implementation handoff prepared",
            "open_risks": ["authenticated human channel is not provisioned"],
            "active_plan": "obtain independent review and external human decision",
            "next_actions": ["review handoff", "query exact-revision CI"],
            "branch": "feat/pilot",
            "worktree": str(root),
            "commit": REVISION,
            "recovery_command": f"python3 framework/validate.py --root {root} --all",
            "timestamp": "2026-09-18T12:00:00Z",
        }

    def handoff(self, context):
        task = validate.load(context.root / "tasks/TASK-101.yaml")
        return {
            "task": "TASK-101",
            "task_digest": runtime.task_digest(task),
            "commit": REVISION,
            "diff_ref": "git diff base..head",
            "from": "executor",
            "to": "reviewer",
            "from_identity": "codex-pilot",
            "to_identity": "claude-pilot",
            "access": "read-only",
            "status": "ready",
            "summary": "Portable pilot is ready for bounded independent review.",
            "changed_files": ["src/example.py"],
            "evidence": ["explicit-root validation", "exact-revision CI query"],
            "open_risks": ["authenticated human merge approval remains external"],
            "next_action": "perform independent review",
            "checkpoint_ref": ".intellix/runtime/checkpoints/TASK-101.json",
        }

    def test_clean_project_profiles_run_portably_from_unrelated_cwd(self):
        for fixture in sorted(self.profiles.glob("*.json")):
            profile = validate.load(fixture)
            with self.subTest(profile=profile["governance_profile"]):
                with tempfile.TemporaryDirectory() as temporary:
                    parent = Path(temporary)
                    unrelated = parent / "unrelated"
                    unrelated.mkdir()
                    root, task_path = self.project(parent, profile)
                    context = validate.build_context(root)
                    self.assertEqual(
                        context.framework["governance_profiles"][profile["governance_profile"]]["minimum_gates"],
                        profile["minimum_gates"],
                    )

                    validation = subprocess.run(
                        [sys.executable, str(self.validator), "--root", str(root), "--all"],
                        cwd=unrelated,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

                    dispatch = subprocess.run(
                        [
                            sys.executable,
                            str(self.dispatcher),
                            "--root",
                            str(root),
                            "--task",
                            str(task_path),
                            "--available-adapter",
                            "codex",
                        ],
                        cwd=unrelated,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(dispatch.returncode, 0, dispatch.stdout + dispatch.stderr)
                    self.assertEqual(validate.load(task_path)["status"], "IN_PROGRESS")

                    context = validate.build_context(root)
                    self.assertTrue(adapters.write_checkpoint(context, self.checkpoint(root)).is_file())
                    self.assertTrue(adapters.write_handoff(context, self.handoff(context)).is_file())
                    evidence = ci.evaluate(context, REVISION, "pilot-token", self.github_success)
                    self.assertEqual(evidence["decision"], "eligible")

                    environment = os.environ.copy()
                    environment.pop("GITHUB_TOKEN", None)
                    ci_result = subprocess.run(
                        [
                            sys.executable,
                            str(self.ci_command),
                            "--root",
                            str(root),
                            "--revision",
                            REVISION,
                        ],
                        cwd=unrelated,
                        env=environment,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(ci_result.returncode, 0)
                    self.assertIn("credential is unavailable", ci_result.stdout)

                    escaped_output = subprocess.run(
                        [
                            sys.executable,
                            str(self.ci_command),
                            "--root",
                            str(root),
                            "--revision",
                            REVISION,
                            "--output",
                            "../outside.json",
                        ],
                        cwd=unrelated,
                        env=environment,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(escaped_output.returncode, 0)
                    self.assertIn("path traversal is forbidden", escaped_output.stdout)

                    policy = validate.load(root / "framework/policies/git.yaml")["rules"]
                    self.assertFalse(policy["local_ci_evidence_authoritative"])
                    self.assertFalse(policy["local_approval_authoritative"])
                    self.assertEqual(
                        policy["human_approval_assurance"], "external-separate-credential"
                    )

    def test_workflow_has_portable_matrix_exact_checkout_and_stable_gate(self):
        workflow = (validate.CODE_ROOT / ".github/workflows/framework-ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("os: [ubuntu-latest, macos-latest]", workflow)
        self.assertIn("github.event.pull_request.head.sha || github.sha", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('test "$(git rev-parse HEAD)" = "$EXPECTED_SHA"', workflow)
        self.assertIn("name: framework-validation", workflow)
        self.assertIn('test "$MATRIX_RESULT" = "success"', workflow)


if __name__ == "__main__":
    unittest.main()
