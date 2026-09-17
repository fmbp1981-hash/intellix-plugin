# Claude Code adapter

Follow `AGENTS.md`. Claude is the default architect and independent reviewer.
Implement only when the Task Contract explicitly assigns Claude as executor,
and never approve the same implementation. Existing IntelliX skills and hooks
are adapters; they do not override contracts or CI.
