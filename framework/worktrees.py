#!/usr/bin/env python3
"""Fail-closed worktree setup and exclusive fileset reservations."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import adapters
import runtime
import validate

ACTIVE_STATES = {"reserving", "reserved"}


def git(root: Path, *arguments: str) -> str:
    forbidden = {"--force", "reset", "clean"}
    if forbidden.intersection(arguments):
        raise validate.ValidationError("destructive Git operation is forbidden")
    result = subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise validate.ValidationError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def reservation_path(context: validate.ValidationContext, task_id: str) -> Path:
    return adapters.artifact_path(context, "reservations", task_id)


def active_reservations(context: validate.ValidationContext) -> list[dict[str, Any]]:
    directory = reservation_path(context, "TASK-000").parent
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("TASK-*.json")):
        value = validate.load(path)
        if not isinstance(value, dict):
            raise validate.ValidationError(f"{path}: reservation must be an object")
        if value.get("state") in ACTIVE_STATES:
            records.append(value)
    return records


def reserve(
    context: validate.ValidationContext,
    task: dict[str, Any],
    worktree_path: Path,
    branch: str,
    base_commit: str,
    owner: str,
) -> Path:
    writable = task.get("scope", {}).get("create", []) + task.get("scope", {}).get("modify", [])
    for existing in active_reservations(context):
        if existing.get("task_id") == task["id"]:
            raise validate.ValidationError(f"task {task['id']} already has an active reservation")
        if any(
            validate.patterns_overlap(left, right)
            for left in writable
            for right in existing.get("writable_globs", [])
        ):
            raise validate.ValidationError(
                f"fileset reservation collision with {existing.get('task_id')}"
            )
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "schema_version": "1.0.0",
        "task_id": task["id"],
        "task_digest": runtime.task_digest(task),
        "repository": str(context.root),
        "worktree_path": str(worktree_path),
        "branch": branch,
        "base_commit": base_commit,
        "writable_globs": writable,
        "owner": owner,
        "state": "reserving",
        "created_at": now,
        "updated_at": now,
        "reason": None,
    }
    path = reservation_path(context, task["id"])
    adapters.write_validated(context, "reservation", path, record)
    return path
