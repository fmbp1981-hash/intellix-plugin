# Claude Code adapter

Follow `AGENTS.md`. The canonical framework is `framework/framework.yaml`.

Claude's default duties are architecture, task-contract review, threat/design
review and independent code review. Claude may implement only when a Task
Contract explicitly assigns it as executor. It must not approve that same work.

The existing IntelliX skills, commands and hooks are delivery conveniences.
They cannot override the canonical framework, project contract, ADRs, assigned
Task Contract or deterministic CI result.
