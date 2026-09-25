#!/usr/bin/env python3
"""Bounded adapter handoff and resumable checkpoint artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import runtime
import validate


def same_identity(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    return left == right or left.split("-", 1)[0] == right.split("-", 1)[0]


def artifact_path(
    context: validate.ValidationContext, category: str, task_id: str
) -> Path:
    base = runtime.record_path(context, task_id).parent
    relative = (base / category / f"{task_id}.json").relative_to(context.root)
    return validate.resolve_contract_path(
        context.root, relative.as_posix(), f"runtime {category} artifact", must_exist=False
    )


def write_validated(
    context: validate.ValidationContext,
    schema_name: str,
    path: Path,
    value: dict[str, Any],
) -> Path:
    schema = validate.load(validate.declared_path(context, "schemas", schema_name))
    errors = validate.validate_schema(value, schema)
    if errors:
        raise validate.ValidationError("invalid artifact: " + "; ".join(errors))
    runtime.atomic_json(path, value)
    return path


def write_checkpoint(
    context: validate.ValidationContext, value: dict[str, Any]
) -> Path:
    return write_validated(
        context,
        "checkpoint",
        artifact_path(context, "checkpoints", value["task"]),
        value,
    )


def write_handoff(context: validate.ValidationContext, value: dict[str, Any]) -> Path:
    if same_identity(value.get("from_identity"), value.get("to_identity")):
        raise validate.ValidationError("executor and reviewer identities are not independent")
    if value.get("access") != "read-only":
        raise validate.ValidationError("reviewer handoff must be read-only")
    return write_validated(
        context,
        "handoff",
        artifact_path(context, "handoffs", value["task"]),
        value,
    )
