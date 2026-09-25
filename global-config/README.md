# global-config/ — espelho da configuração global `~/.claude`

Este diretório **não é carregado pelo Claude Code como parte do plugin**
(não aparece em `.claude-plugin/plugin.json`, não é uma skill/agent/command
instalável). É um **espelho versionado** dos arquivos globais que fazem o
método IntelliX funcionar de verdade em `~/.claude`, mas que nunca tinham
backup em lugar nenhum: o repositório `~/.claude` do usuário não tem remote
configurado (não é enviado a nenhum GitHub).

Sem esses arquivos, o `intellix-plugin` sozinho não reproduz o comportamento
real do método — faltam a fonte normativa, os hooks de sessão e as regras
globais que o CLAUDE.md do usuário importa.

## O que tem aqui

| Caminho aqui | Caminho real em produção | O que é |
|---|---|---|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Instruções globais do usuário (idioma, stack, imports) |
| `metodologia.yaml` | `~/.claude/metodologia.yaml` | **Fonte normativa** — fases, IDs de skill, stack, gates, artefatos. Vence em conflito com qualquer markdown |
| `RTK.md` | `~/.claude/RTK.md` | Referência do proxy `rtk` |
| `settings.json` | `~/.claude/settings.json` | Wiring dos hooks (SessionStart/UserPromptSubmit/PreToolUse/PostToolUse → scripts/), plugins habilitados |
| `modules/*.md` | `~/.claude/modules/*.md` | Módulos importados pelo CLAUDE.md (dev-rules, session, context7, perplexity, gatilhos de skill, regras de CLAUDE.md) |
| `scripts/*.py` + `scripts/tests/` | `~/.claude/scripts/` | Os 16 hooks que rodam a cada mensagem/tool call (doctor.py, roteador de skills, monitor de contexto, gate de fase, etc.) e os testes de regressão deles |
| `skills/ai-project-brainstorm/` | `~/.claude/skills/ai-project-brainstorm/` | Skill autoral do pré-desenvolvimento (PRD) — fica fora do pacote do plugin por convenção deste projeto |
| `skills/intellix-agent-creation/` | `~/.claude/skills/intellix-agent-creation/` | Skill autoral da Fase 03b (blueprints de agente de IA) — mesma convenção |
| `skills/intellix-decision-layer/` | `~/.claude/skills/intellix-decision-layer/` | Skill autoral e vendor-neutral para decidir, por projeto, se uma camada semântica dedicada deve ser adotada |

**O que fica de fora de propósito:** `settings.local.json` (permissões/env
locais da máquina), `plugins/` (cache de plugins de terceiros — não é
conteúdo autoral, cada máquina reinstala pelo marketplace), `sessions/`,
`history/`, arquivos de cache do MCP, `security/` — nada disso é "o método",
é estado de runtime ou de terceiros.

## Como restaurar em uma máquina nova

```bash
PLUGIN=~/.claude/plugins/marketplaces/intellix-plugin   # ajuste se o caminho for outro
cp "$PLUGIN/global-config/CLAUDE.md"        ~/.claude/CLAUDE.md
cp "$PLUGIN/global-config/RTK.md"           ~/.claude/RTK.md
cp "$PLUGIN/global-config/metodologia.yaml" ~/.claude/metodologia.yaml
cp "$PLUGIN/global-config/settings.json"    ~/.claude/settings.json   # revise antes: plugins habilitados podem diferir por máquina
cp -R "$PLUGIN/global-config/modules"       ~/.claude/modules
cp -R "$PLUGIN/global-config/scripts"       ~/.claude/scripts
cp -R "$PLUGIN/global-config/skills/ai-project-brainstorm"    ~/.claude/skills/
cp -R "$PLUGIN/global-config/skills/intellix-agent-creation"  ~/.claude/skills/
cp -R "$PLUGIN/global-config/skills/intellix-decision-layer"  ~/.claude/skills/
python3 ~/.claude/scripts/doctor.py --strict   # confirma que ficou consistente
```

Essa restauração é uma ação humana explícita, executada somente depois da
revisão do diff. O plugin e seus scripts nunca copiam automaticamente este
espelho para `~/.claude`.

## Como manter atualizado

Este espelho **não sincroniza sozinho**. Depois de qualquer mudança real em
`~/.claude` (novo módulo, hook corrigido, `metodologia.yaml` atualizado),
repita a cópia para cá, revise o diff e commit — do mesmo jeito que uma
mudança normal no plugin (subir a versão em `.claude-plugin/plugin.json` e
rodar `claude plugin update`).

Instantâneo tirado em 2026-09-16, ao final da remediação da estrutura de
desenvolvimento IntelliX.AI.
