import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import completion  # noqa: E402
import dispatch  # noqa: E402
import runtime  # noqa: E402
import sync  # noqa: E402
import validate  # noqa: E402


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)

    def __call__(self, _request):
        if not self.responses:
            raise AssertionError("unexpected GitHub request")
        return self.responses.pop(0)


def check_response(revision: str, conclusion: str = "success"):
    check = {
        "name": "project-ci",
        "head_sha": revision,
        "status": "completed",
        "conclusion": conclusion,
        "details_url": "https://github.example/check/1",
        "completed_at": "2026-09-23T12:00:00Z",
    }
    return 200, {}, json.dumps({"total_count": 1, "check_runs": [check]}).encode()


def reviewed_ci_evidence(revision: str):
    return {
        "schema_version": "1.0.0",
        "provider": "github",
        "source": "github-api",
        "repository": "example/external-consumer",
        "revision": revision,
        "required_checks": ["project-ci"],
        "observed_checks": [
            {
                "name": "project-ci",
                "head_sha": revision,
                "status": "completed",
                "conclusion": "success",
                "details_url": "https://github.example/check/1",
                "completed_at": "2026-09-23T12:00:00Z",
            }
        ],
        "decision": "eligible",
        "reasons": [],
        "queried_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    }


class CompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__file__).parent / "fixtures/projects/valid"

    @staticmethod
    def git(root: Path, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)
        return result.stdout.strip()

    @staticmethod
    def write(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def repository(self, parent: Path):
        source = parent / "consumer"
        worktree = parent / "consumer-TASK-101"
        remote = parent / "remote.git"
        shutil.copytree(self.fixture, source)
        sync.install_snapshot(validate.CODE_ROOT, source)
        task_path = source / "tasks/TASK-101.yaml"
        task = validate.load(task_path)
        task["status"] = "IN_REVIEW"
        task["scope"] = {
            "create": [
                "src/example.py",
                "tasks/evidence/TASK-101.review.json",
                "tasks/evidence/TASK-101.approval.json",
            ],
            "modify": ["tasks/TASK-101.yaml"],
            "forbidden": [".env*", "infra/production/**"],
        }
        self.write(task_path, task)
        self.git(source, "init", "-b", "feat/test")
        self.git(source, "config", "user.email", "test@example.com")
        self.git(source, "config", "user.name", "Test")
        subprocess.run(
            ["git", "init", "--bare", str(remote)], check=True, capture_output=True
        )
        github_origin = "https://github.com/example/external-consumer.git"
        self.git(source, "config", f"url.{remote}.insteadOf", github_origin)
        self.git(source, "remote", "add", "origin", github_origin)
        self.git(source, "add", ".")
        self.git(source, "commit", "-m", "initial review state")
        task["status"] = "IN_PROGRESS"
        self.write(task_path, task)
        self.git(source, "add", "tasks/TASK-101.yaml")
        self.git(source, "commit", "-m", "start completion phase")
        phase_base = self.git(source, "rev-parse", "HEAD")
        self.git(source, "switch", "--detach", phase_base)
        self.git(source, "worktree", "add", str(worktree), "feat/test")
        self.git(worktree, "config", "user.email", "test@example.com")
        self.git(worktree, "config", "user.name", "Test")
        implementation = worktree / "src/example.py"
        implementation.parent.mkdir(parents=True, exist_ok=True)
        implementation.write_text("VALUE = 1\n", encoding="utf-8")
        task_path = worktree / "tasks/TASK-101.yaml"
        task = validate.load(task_path)
        task["status"] = "IN_REVIEW"
        self.write(task_path, task)
        self.git(worktree, "add", "src/example.py", "tasks/TASK-101.yaml")
        self.git(worktree, "commit", "-m", "implementation revision R")
        revision = self.git(worktree, "rev-parse", "HEAD")
        self.git(worktree, "push", "-u", "origin", "feat/test")
        context = validate.build_context(worktree)
        return worktree, context, task_path, phase_base, revision

    def review(self, context, task_path, phase_base, revision):
        task = validate.load(task_path)
        files = completion.changed_files(context.root, phase_base, revision)
        return {
            "schema_version": "1.0.0",
            "task": task["id"],
            "task_digest": runtime.task_digest(task),
            "phase_base": phase_base,
            "reviewed_revision": revision,
            "branch": "feat/test",
            "diff_ref": f"{phase_base}..{revision}",
            "executor_identity": "codex",
            "reviewer_assignment": "claude-independent",
            "reviewer_identity": "claude-independent-session-1",
            "access": "read-only",
            "decision": "approved",
            "reviewed_files": files,
            "fileset_digest": completion._manifest_digest_at(
                context.root, revision, files
            ),
            "project_digest": completion._manifest_digest_at(
                context.root,
                revision,
                [context.project_path.relative_to(context.root).as_posix()],
            ),
            "source_digest": completion._manifest_digest_at(
                context.root, revision, completion.source_paths(task)
            ),
            "kernel_digest": completion._manifest_digest_at(
                context.root, revision, completion.kernel_paths(context)
            ),
            "control_plane_digest": completion._manifest_digest_at(
                context.root, revision, completion.control_plane_paths(context)
            ),
            "reviewed_at": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
            "evidence": ["independent read-only review approved R"],
            "limitations": ["Local reviewer identity is forgeable process evidence."],
        }

    @staticmethod
    def human_decision():
        return {
            "origin": "controlling-session",
            "reference": "explicit human technical-completion decision after R review and CI",
            "decided_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "limitations": "Technical completion only; no merge, release or production authority.",
        }

    def complete(self, context, task_path, review, revision):
        return completion.complete_technical_approval(
            context,
            task_path,
            review,
            reviewed_ci_evidence(revision),
            self.human_decision(),
            "test-token",
            transport=FakeTransport([check_response(revision)]),
        )

    def test_guarded_completion_and_exact_R_A_dependency_eligibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            worktree, context, task_path, phase_base, revision = self.repository(
                Path(temporary)
            )
            review = self.review(context, task_path, phase_base, revision)
            approval = self.complete(context, task_path, review, revision)
            self.assertEqual(validate.load(task_path)["status"], "APPROVED")
            self.assertEqual(approval["reviewed_revision"], revision)
            review_path, approval_path = completion.evidence_paths(context, "TASK-101")
            self.assertTrue(review_path.is_file())
            self.assertTrue(approval_path.is_file())
            self.assertFalse(validate.validate_completion_evidence(task_path.parent, context))
            self.git(worktree, "add", "tasks/TASK-101.yaml", "tasks/evidence")
            self.git(worktree, "commit", "-m", "record guarded approval A")
            status_revision = self.git(worktree, "rev-parse", "HEAD")
            self.git(worktree, "push", "origin", "feat/test")
            reasons = completion.dependency_eligibility(
                context,
                validate.load(task_path),
                "test-token",
                transport=FakeTransport(
                    [check_response(revision), check_response(status_revision)]
                ),
            )
            self.assertEqual(reasons, [])

    def test_dirty_worktree_and_self_review_block_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            worktree, context, task_path, phase_base, revision = self.repository(
                Path(temporary)
            )
            review = self.review(context, task_path, phase_base, revision)
            (worktree / "src/example.py").write_text("VALUE = 2\n", encoding="utf-8")
            with self.assertRaisesRegex(validate.ValidationError, "clean"):
                self.complete(context, task_path, review, revision)
            self.git(worktree, "restore", "src/example.py")
            review["reviewer_identity"] = "codex-session-2"
            with self.assertRaisesRegex(validate.ValidationError, "not independent"):
                self.complete(context, task_path, review, revision)
            review_path, approval_path = completion.evidence_paths(context, "TASK-101")
            self.assertFalse(review_path.exists())
            self.assertFalse(approval_path.exists())
            self.assertEqual(validate.load(task_path)["status"], "IN_REVIEW")

    def test_binding_drift_and_failed_A_CI_block_dependency_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            worktree, context, task_path, phase_base, revision = self.repository(
                Path(temporary)
            )
            review = self.review(context, task_path, phase_base, revision)
            self.complete(context, task_path, review, revision)
            self.git(worktree, "add", "tasks/TASK-101.yaml", "tasks/evidence")
            self.git(worktree, "commit", "-m", "record guarded approval A")
            status_revision = self.git(worktree, "rev-parse", "HEAD")
            self.git(worktree, "push", "origin", "feat/test")
            failed = completion.dependency_eligibility(
                context,
                validate.load(task_path),
                "test-token",
                transport=FakeTransport(
                    [check_response(revision), check_response(status_revision, "failure")]
                ),
            )
            self.assertTrue(any("exact-A CI" in reason for reason in failed))
            (worktree / "SPEC.md").write_text("# Changed source\n", encoding="utf-8")
            drift = completion.dependency_eligibility(
                context,
                validate.load(task_path),
                "test-token",
                transport=FakeTransport(
                    [check_response(revision), check_response(status_revision)]
                ),
            )
            self.assertTrue(any("source drift" in reason for reason in drift))
            (worktree / "SPEC.md").write_text(
                "# Specification\n\nThe consumer project validates against its own pinned framework source.\n",
                encoding="utf-8",
            )
            control_plane = worktree / "framework/ci.py"
            control_plane.write_text(
                control_plane.read_text(encoding="utf-8") + "\n# drift\n",
                encoding="utf-8",
            )
            control_drift = completion.dependency_eligibility(
                context,
                validate.load(task_path),
                "test-token",
                transport=FakeTransport(
                    [check_response(revision), check_response(status_revision)]
                ),
            )
            self.assertTrue(
                any("control-plane implementation drift" in reason for reason in control_drift)
            )

    def test_hand_edited_approved_label_without_evidence_is_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, context, task_path, _, _ = self.repository(Path(temporary))
            task = validate.load(task_path)
            task["status"] = "APPROVED"
            reasons = completion.dependency_eligibility(context, task, "test-token")
            self.assertTrue(any("evidence unavailable" in reason for reason in reasons))

    def test_dispatcher_requires_completion_evidence_for_approved_dependency(self):
        context = validate.build_context(validate.CODE_ROOT)
        dependent = {"dependencies": ["TASK-101"]}
        approved = {"id": "TASK-101", "status": "APPROVED"}
        with mock.patch.object(
            dispatch.completion,
            "dependency_eligibility",
            return_value=["status revision A is not eligible"],
        ):
            errors = dispatch.dependency_errors(
                context,
                dependent,
                {"TASK-101": approved},
                {"APPROVED"},
            )
        self.assertEqual(len(errors), 1)
        self.assertIn("status revision A", errors[0])

    def test_review_revision_and_fileset_binding_mismatches_block(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, context, task_path, phase_base, revision = self.repository(Path(temporary))
            base = self.review(context, task_path, phase_base, revision)
            cases = {
                "reviewed_revision": "0" * 40,
                "phase_base": "1" * 40,
                "branch": "feat/other",
                "reviewed_files": ["tasks/TASK-101.yaml"],
                "fileset_digest": "sha256:" + ("0" * 64),
                "project_digest": "sha256:" + ("0" * 64),
                "kernel_digest": "sha256:" + ("0" * 64),
                "control_plane_digest": "sha256:" + ("0" * 64),
            }
            for field, value in cases.items():
                with self.subTest(field=field):
                    review = copy.deepcopy(base)
                    review[field] = value
                    with self.assertRaises(validate.ValidationError):
                        self.complete(context, task_path, review, revision)


if __name__ == "__main__":
    unittest.main()
