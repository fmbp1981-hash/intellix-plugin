# IntelliX framework kernel

This directory is the executable, vendor-neutral engineering contract.

## Start a project

1. Copy `templates/PROJECT.yaml` to `intellix.yaml` and configure it.
2. Copy the Codex and Claude adapter templates to `AGENTS.md` and `CLAUDE.md`.
3. Create product, architecture, SPEC and ADR artifacts referenced by the project.
4. Copy `templates/TASK.yaml` to `tasks/TASK-NNN.yaml` for each unit of work.
5. Validate with `python3 framework/validate.py --all`.

## Validate

```bash
python3 framework/validate.py --framework
python3 framework/validate.py --project intellix.yaml
python3 framework/validate.py --task tasks/TASK-001.yaml
python3 framework/validate.py --tasks-dir tasks
```

The `.yaml` contracts use JSON-compatible YAML deliberately, so the validator
has no third-party dependency. Unknown fields fail closed. See
`docs/architecture/MULTIAGENT-FRAMEWORK.md` for the operating model and
`docs/MULTIAGENT-FRAMEWORK-MIGRATION.md` for incremental adoption.
