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
2. Estrutura canônica + `AGENTS.md`, `CLAUDE.md`, `CLAUDE.local.md`, `.claude/settings.json`, `.gitignore`.
3. Bootstrap técnico (`skills/project-kickoff/references/bootstrap-projeto-novo.md`):
   `references/` (architecture, security, stack, workflow), `DESIGN.md` semente, `issues/`,
   `.github/workflows/security.yml`, `.env.example`/`.env.local`, `package.json` (versões
   verificadas antes) e `npm install` com sua confirmação.
4. Verificação: `python3 ~/.claude/scripts/scaffold-check.py . --fase kickoff`.

Os agentes do `/execute` vêm do plugin — nada é copiado para o projeto.
Ao final: `.intellix-phase = arch` e handover para `intellix:architecture`.

Pré-requisito: `superpowers:brainstorming` e `superpowers:writing-plans` concluídos.
