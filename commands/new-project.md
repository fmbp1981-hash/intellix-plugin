---
description: >
  Inicia um projeto novo pelo workflow IntelliX (Fase 00). Entrada única: roda o
  intellix:project-kickoff no modo "projeto novo" — diagnóstico, estrutura canônica,
  references/, DESIGN.md, DevSecOps scaffold, .env e package.json.
disable-model-invocation: false
---

Use a skill `intellix:project-kickoff` agora, no **modo projeto novo**.

Ela executa:
1. Diagnóstico e briefing (tipo de sistema, integrações, IA, dados pessoais, nome, cliente, cores).
2. Estrutura canônica + `intellix.yaml`, snapshot/lock versionado e adapters gerados `AGENTS.md`/`CLAUDE.md`; também `CLAUDE.local.md`, `.claude/settings.json` e `.gitignore`.
3. Bootstrap técnico (`skills/project-kickoff/references/bootstrap-projeto-novo.md`):
   `references/` (architecture, security, stack, workflow), `DESIGN.md` semente,
   `tasks/`, `intellix.yaml`, adapters `AGENTS.md`/`CLAUDE.md` e `issues/` legado,
   `.github/workflows/security.yml`, `.env.example`/`.env.local`, `package.json` (versões
   verificadas antes) e `npm install` com sua confirmação.
4. Sincronização unidirecional do kernel e geração dos adapters pelos CLIs versionados em `framework/`.
5. Verificação: `python3 framework/validate.py --root . --all` e `python3 ~/.claude/scripts/scaffold-check.py . --fase kickoff`.

Os agentes do `/execute` vêm do plugin — nada é copiado para o projeto.
Ao final: `.intellix-phase = arch` e handover para `intellix:architecture`.

Pré-requisito: `superpowers:brainstorming` e `superpowers:writing-plans` concluídos.
