import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ci  # noqa: E402
import dispatch  # noqa: E402
import runtime  # noqa: E402
import sync  # noqa: E402
import validate  # noqa: E402


REVISION = "a" * 40


class CompletionGuardTests(unittest.TestCase):
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
        self.write(task_path, task)
        return target, task_path

    @staticmethod
    def write(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def mutate_kernel(self, project: Path, mutation) -> validate.ValidationContext:
        framework_path = project / "framework/framework.yaml"
        framework = validate.load(framework_path)
        mutation(framework)
        self.write(framework_path, framework)
        return validate.build_context(project)

    def test_canonical_registries_are_nonempty_known_and_nested(self):
        context = validate.build_context(validate.CODE_ROOT)
        satisfying = runtime.dependency_satisfying_states(context)
        guarded = runtime.guarded_transition_states(context)
        self.assertTrue(satisfying)
        self.assertTrue(guarded)
        self.assertLessEqual(satisfying, guarded)
        self.assertLessEqual(guarded, set(context.framework["task_lifecycle"]))

    def test_kernel_validation_rejects_invalid_runtime_registries(self):
        mutations = {
            "missing": lambda framework: framework["runtime"].pop(
                "dependency_satisfying_states"
            ),
            "empty": lambda framework: framework["runtime"].update(
                dependency_satisfying_states=[]
            ),
            "duplicate": lambda framework: framework["runtime"].update(
                dependency_satisfying_states=["APPROVED", "APPROVED"]
            ),
            "unknown": lambda framework: framework["runtime"].update(
                dependency_satisfying_states=["UNKNOWN"]
            ),
            "not-guarded": lambda framework: framework["runtime"].update(
                dependency_satisfying_states=["APPROVED"],
                guarded_transition_states=["MERGED"],
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                project, _ = self.project(Path(temporary))
                context = self.mutate_kernel(project, mutation)
                self.assertTrue(validate.validate_framework(context))

    def test_runtime_rejects_guarded_target_even_if_edge_exists(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path = self.project(Path(temporary))

            def add_edge(framework):
                framework["runtime"]["transitions"]["READY"].append("APPROVED")

            context = self.mutate_kernel(project, add_edge)
            with self.assertRaisesRegex(
                validate.ValidationError, "dedicated completion path"
            ):
                runtime.transition(context, task_path, "APPROVED", reason="bypass")
            self.assertEqual(validate.load(task_path)["status"], "READY")
            self.assertFalse(
                (project / ".intellix/runtime/TASK-101.json").exists()
            )

    def test_dispatch_rejects_guarded_target_before_operational_activity(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path = self.project(Path(temporary))
            with mock.patch.object(
                dispatch.worktrees,
                "active_reservation",
                side_effect=AssertionError("worktree activity must not occur"),
            ), mock.patch.object(
                dispatch,
                "resolve_executor",
                side_effect=AssertionError("adapter activity must not occur"),
            ):
                with self.assertRaisesRegex(
                    dispatch.DispatchBlocked, "dedicated completion path"
                ):
                    dispatch.dispatch(
                        project,
                        task_path,
                        available={"codex"},
                        target_state="APPROVED",
                    )
            self.assertEqual(validate.load(task_path)["status"], "READY")
            self.assertFalse(
                (project / ".intellix/runtime/TASK-101.json").exists()
            )

    def test_malformed_dependency_registry_has_no_code_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path = self.project(Path(temporary))
            self.mutate_kernel(
                project,
                lambda framework: framework["runtime"].update(
                    dependency_satisfying_states=[]
                ),
            )
            with self.assertRaisesRegex(
                dispatch.DispatchBlocked, "dependency_satisfying_states"
            ):
                dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(validate.load(task_path)["status"], "READY")
            self.assertFalse(
                (project / ".intellix/runtime/TASK-101.json").exists()
            )

    def test_dispatch_reads_dependency_satisfaction_from_kernel(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, task_path = self.project(Path(temporary))
            task = validate.load(task_path)
            dependency = copy.deepcopy(task)
            dependency["id"] = "TASK-102"
            dependency["status"] = "APPROVED"
            dependency["scope"] = {
                "create": ["src/dependency.py"],
                "modify": [],
                "forbidden": [],
            }
            self.write(project / "tasks/TASK-102.yaml", dependency)
            task["dependencies"] = ["TASK-102"]
            self.write(task_path, task)
            self.mutate_kernel(
                project,
                lambda framework: framework["runtime"].update(
                    dependency_satisfying_states=["VERIFIED"]
                ),
            )
            with self.assertRaisesRegex(dispatch.DispatchBlocked, "not satisfied"):
                dispatch.dispatch(project, task_path, available={"codex"})
            self.assertEqual(validate.load(task_path)["status"], "BLOCKED")

    def test_invalid_required_check_sets_are_indeterminate_without_query(self):
        base = validate.build_context(validate.CODE_ROOT)
        cases = [None, [], [""], ["framework-validation", "framework-validation"]]
        for required in cases:
            with self.subTest(required=required):
                project = copy.deepcopy(base.project)
                if required is None:
                    project["quality"]["ci"].pop("required_checks", None)
                else:
                    project["quality"]["ci"]["required_checks"] = required
                context = validate.ValidationContext(
                    root=base.root,
                    project_path=base.project_path,
                    project=project,
                    framework_path=base.framework_path,
                    framework_dir=base.framework_dir,
                    framework=base.framework,
                )
                requests = []

                def unexpected_transport(request):
                    requests.append(request)
                    raise AssertionError("GitHub must not be queried")

                evidence = ci.evaluate(
                    context,
                    REVISION,
                    "secret-for-test",
                    unexpected_transport,
                )
                self.assertEqual(evidence["decision"], "indeterminate")
                self.assertEqual(requests, [])


if __name__ == "__main__":
    unittest.main()
