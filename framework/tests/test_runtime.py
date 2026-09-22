import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime  # noqa: E402
import sync  # noqa: E402
import validate  # noqa: E402


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = Path(__file__).parent / "fixtures/projects/valid"

    def project(self, parent: Path):
        target = parent / "consumer"
        shutil.copytree(self.fixture, target)
        sync.install_snapshot(validate.CODE_ROOT, target)
        context = validate.build_context(target)
        task_path = target / "tasks/TASK-101.yaml"
        task = validate.load(task_path)
        task["status"] = "READY"
        task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        return context, task_path

    def test_transition_writes_schema_valid_durable_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task_path = self.project(Path(temporary))
            event = runtime.transition(
                context,
                task_path,
                "IN_PROGRESS",
                reason="unit test",
                selected_adapter="codex",
                resolution="task-explicit",
            )
            self.assertEqual(event["to"], "IN_PROGRESS")
            record = validate.load(
                Path(temporary) / "consumer/.intellix/runtime/TASK-101.json"
            )
            schema = validate.load(context.root / "framework/schemas/runtime.schema.json")
            self.assertEqual(validate.validate_schema(record, schema), [])
            self.assertEqual(record["state"], "IN_PROGRESS")
            self.assertEqual(
                record["events"][0]["decision_context"]["domain_role"],
                "platform-engineer",
            )
            self.assertEqual(validate.load(task_path)["status"], "IN_PROGRESS")

    def test_illegal_transition_is_rejected_without_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task_path = self.project(Path(temporary))
            with self.assertRaisesRegex(validate.ValidationError, "illegal task transition"):
                runtime.transition(context, task_path, "IN_REVIEW", reason="forbidden")
            self.assertFalse(
                (Path(temporary) / "consumer/.intellix/runtime/TASK-101.json").exists()
            )

    def test_contract_change_invalidates_existing_runtime_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            context, task_path = self.project(Path(temporary))
            runtime.transition(context, task_path, "IN_PROGRESS", reason="first")
            task = validate.load(task_path)
            task["objective"] += " changed"
            task_path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(validate.ValidationError, "task digest drift"):
                runtime.transition(context, task_path, "IN_REVIEW", reason="second")


if __name__ == "__main__":
    unittest.main()
