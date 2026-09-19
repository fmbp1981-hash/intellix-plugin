#!/usr/bin/env python3
"""Durable, fail-closed lifecycle records for IntelliX Task Contracts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def task_digest(task: dict[str, Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_bytes(task)).hexdigest()}"


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def record_path(context: validate.ValidationContext, task_id: str) -> Path:
    directory = validate.resolve_contract_path(
        context.root,
        context.project.get("runtime", {}).get("records_path"),
        "runtime.records_path",
        must_exist=False,
    )
    return validate.resolve_contract_path(
        context.root,
        str((directory / f"{task_id}.json").relative_to(context.root)),
        "runtime task record",
        must_exist=False,
    )


def load_record(path: Path, task: dict[str, Any]) -> dict[str, Any]:
    if path.exists():
        value = validate.load(path)
        if not isinstance(value, dict):
            raise validate.ValidationError(f"{path}: runtime record must be an object")
        if value.get("task_id") != task.get("id"):
            raise validate.ValidationError(f"{path}: runtime task identity drift")
        if value.get("state") != task.get("status"):
            raise validate.ValidationError(f"{path}: runtime state drift")
        if value.get("task_digest") != task_digest(task):
            raise validate.ValidationError(f"{path}: runtime task digest drift")
        return value
    return {
        "schema_version": "1.0.0",
        "task_id": task["id"],
        "task_digest": task_digest(task),
        "state": task["status"],
        "events": [],
    }


def permitted_transition(
    context: validate.ValidationContext, current: str, target: str
) -> bool:
    configured = context.framework.get("runtime", {}).get("transitions", {})
    return target in configured.get(current, [])


def transition(
    context: validate.ValidationContext,
    task_path: Path,
    target: str,
    *,
    reason: str,
    actor: str = "intellix-control-plane",
    selected_adapter: str | None = None,
    resolution: str | None = None,
    outcome: str = "transitioned",
    unblock_condition: str | None = None,
) -> dict[str, Any]:
    task = validate.load(task_path)
    if not isinstance(task, dict):
        raise validate.ValidationError(f"{task_path}: task must be an object")
    current = task.get("status")
    if not permitted_transition(context, current, target):
        raise validate.ValidationError(f"illegal task transition: {current} -> {target}")

    record_file = record_path(context, task["id"])
    record = load_record(record_file, task)
    event = {
        "sequence": len(record.get("events", [])) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "from": current,
        "to": target,
        "outcome": outcome,
        "reason": reason,
        "actor": actor,
        "decision_context": {
            "domain_role": task.get("ownership", {}).get("domain_role"),
            "risk_level": task.get("risk", {}).get("level"),
            "dependencies": task.get("dependencies", []),
            "writable_files": (
                task.get("scope", {}).get("create", [])
                + task.get("scope", {}).get("modify", [])
            ),
            "gates": task.get("gates", []),
        },
        "selected_adapter": selected_adapter,
        "resolution": resolution,
        "unblock_condition": unblock_condition,
    }
    updated_task = dict(task)
    updated_task["status"] = target
    record["events"].append(event)
    record["state"] = target
    record["task_digest"] = task_digest(updated_task)

    runtime_schema = validate.declared_path(context, "schemas", "runtime")
    schema = validate.load(runtime_schema)
    errors = validate.validate_schema(record, schema)
    if errors:
        raise validate.ValidationError("invalid runtime record: " + "; ".join(errors))

    atomic_json(record_file, record)
    try:
        atomic_json(task_path, updated_task)
    except BaseException:
        # The durable event remains evidence of an incomplete state write.
        raise
    return event


def block(
    context: validate.ValidationContext,
    task_path: Path,
    reason: str,
    *,
    unblock_condition: str,
    selected_adapter: str | None = None,
    resolution: str | None = None,
) -> dict[str, Any]:
    return transition(
        context,
        task_path,
        "BLOCKED",
        reason=reason,
        outcome="blocked",
        unblock_condition=unblock_condition,
        selected_adapter=selected_adapter,
        resolution=resolution,
    )
