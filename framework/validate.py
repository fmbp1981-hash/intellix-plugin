#!/usr/bin/env python3
"""Dependency-free validator for IntelliX framework artifacts.

The canonical .yaml files intentionally use the JSON subset of YAML, allowing
validation in CI and fresh worktrees without bootstrapping a package manager.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "framework"
ACTIVE = {
    "READY_FOR_ARCH_REVIEW", "READY", "IN_PROGRESS", "BLOCKED",
    "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED",
}


class ValidationError(Exception):
    pass


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"{path}: file not found") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"{path}:{exc.lineno}:{exc.colno}: expected JSON-compatible YAML ({exc.msg})"
        ) from exc


def type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, True)


def validate_schema(value: Any, schema: dict[str, Any], at: str = "$") -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        options = expected if isinstance(expected, list) else [expected]
        if not any(type_matches(value, option) for option in options):
            return [f"{at}: expected {' or '.join(options)}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{at}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{at}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{at}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{at}: must be >= {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{at}: must be <= {schema['maximum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{at}: requires at least {schema['minItems']} items")
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True) for item in value]
            if len(encoded) != len(set(encoded)):
                errors.append(f"{at}: items must be unique")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, f"{at}[{index}]"))
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{at}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{at}: unexpected property {key!r}")
        for key, child in value.items():
            if key in properties:
                errors.extend(validate_schema(child, properties[key], f"{at}.{key}"))
    return errors


def validate_file(path: Path, schema_path: Path) -> tuple[Any, list[str]]:
    value = load(path)
    schema = load(schema_path)
    return value, [f"{path}: {error}" for error in validate_schema(value, schema)]


def patterns_overlap(left: str, right: str) -> bool:
    return left == right or fnmatch.fnmatch(left, right) or fnmatch.fnmatch(right, left)


def semantic_task_errors(task: dict[str, Any], path: Path, framework: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = str(path)
    scope = task.get("scope", {})
    writable = scope.get("create", []) + scope.get("modify", [])
    forbidden = scope.get("forbidden", [])
    for allowed in writable:
        for denied in forbidden:
            if patterns_overlap(allowed, denied):
                errors.append(f"{prefix}: writable path {allowed!r} overlaps forbidden {denied!r}")
    ownership = task.get("ownership", {})
    if ownership.get("executor") == ownership.get("reviewer"):
        errors.append(f"{prefix}: executor and reviewer must be independent")
    risk = task.get("risk", {}).get("level")
    required = set(framework.get("risk_gates", {}).get(risk, []))
    actual = set(task.get("gates", []))
    missing = sorted(required - actual)
    if missing:
        errors.append(f"{prefix}: risk {risk!r} requires gates {missing}")
    if risk in {"high", "critical"} and not task.get("rollback"):
        errors.append(f"{prefix}: risk {risk!r} requires a rollback plan")
    return errors


def validate_framework() -> list[str]:
    errors: list[str] = []
    canonical = load(FRAMEWORK / "framework.yaml")
    if not canonical.get("normative"):
        errors.append("framework/framework.yaml: canonical source must be normative")
    for category in ("policies", "schemas"):
        for name, relative in canonical.get(category, {}).items():
            if not (ROOT / relative).is_file():
                errors.append(f"framework.yaml: missing {category}.{name} target {relative}")
    role_schema = FRAMEWORK / "schemas/role.schema.json"
    roles = sorted((FRAMEWORK / "roles").glob("*.yaml"))
    if not roles:
        errors.append("framework/roles: no roles registered")
    seen: set[str] = set()
    for role_path in roles:
        role, role_errors = validate_file(role_path, role_schema)
        errors.extend(role_errors)
        role_id = role.get("id") if isinstance(role, dict) else None
        if role_id in seen:
            errors.append(f"{role_path}: duplicate role id {role_id!r}")
        if role_id:
            seen.add(role_id)
    plugin = load(ROOT / ".claude-plugin/plugin.json")
    marketplace = load(ROOT / ".claude-plugin/marketplace.json")
    versions = {
        canonical.get("plugin_version"), plugin.get("version"),
        marketplace.get("plugins", [{}])[0].get("version"),
    }
    if len(versions) != 1:
        errors.append(f"plugin version drift detected: {sorted(str(v) for v in versions)}")
    return errors


def validate_project(path: Path) -> list[str]:
    project, errors = validate_file(path, FRAMEWORK / "schemas/project.schema.json")
    if isinstance(project, dict):
        source = project.get("framework", {}).get("source")
        if source and not (ROOT / source).is_file():
            errors.append(f"{path}: framework source does not exist: {source}")
    return errors


def validate_task(path: Path, framework: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str]]:
    task, errors = validate_file(path, FRAMEWORK / "schemas/task.schema.json")
    if isinstance(task, dict):
        errors.extend(semantic_task_errors(task, path, framework or load(FRAMEWORK / "framework.yaml")))
        return task, errors
    return {}, errors


def validate_tasks(directory: Path) -> list[str]:
    errors: list[str] = []
    framework = load(FRAMEWORK / "framework.yaml")
    active: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(directory.glob("TASK-*.yaml")):
        task, task_errors = validate_task(path, framework)
        errors.extend(task_errors)
        if task.get("status") in ACTIVE:
            active.append((path, task))
    for index, (left_path, left) in enumerate(active):
        left_paths = left.get("scope", {}).get("create", []) + left.get("scope", {}).get("modify", [])
        for right_path, right in active[index + 1:]:
            right_paths = right.get("scope", {}).get("create", []) + right.get("scope", {}).get("modify", [])
            collisions = sorted({(a, b) for a in left_paths for b in right_paths if patterns_overlap(a, b)})
            if collisions:
                errors.append(f"fileset collision: {left_path.name} vs {right_path.name}: {collisions}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", action="store_true")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--task", type=Path)
    parser.add_argument("--tasks-dir", type=Path)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not any((args.framework, args.project, args.task, args.tasks_dir, args.all)):
        parser.error("select --framework, --project, --task, --tasks-dir or --all")
    errors: list[str] = []
    try:
        if args.framework or args.all:
            errors.extend(validate_framework())
        if args.project:
            errors.extend(validate_project(args.project))
        if args.task:
            _, task_errors = validate_task(args.task)
            errors.extend(task_errors)
        if args.tasks_dir:
            errors.extend(validate_tasks(args.tasks_dir))
        if args.all:
            errors.extend(validate_project(ROOT / "intellix.yaml"))
            errors.extend(validate_tasks(ROOT / "tasks"))
    except ValidationError as exc:
        errors.append(str(exc))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"FAILED: {len(errors)} validation error(s)")
        return 1
    print("OK: IntelliX framework artifacts are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
