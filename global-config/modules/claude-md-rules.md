## Regra Inviolável — Handoff pós-superpowers:writing-plans

Quando `superpowers:writing-plans` terminar e o usuário **aprovar o plano**, a próxima ação é SEMPRE determinada pelo estado IntelliX do projeto:

```
Plano aprovado
      │
      ├─ .intellix-phase NÃO existe ou é "init"
      │    └─ OBRIGATÓRIO: intellix:project-kickoff → fases IntelliX → /spec
      │
      └─ .intellix-phase é "arch", "dev" ou além
           └─ PODE: Epic Workflow /spec → /break → /plan → /execute
```

**PROIBIDO:** ir direto para `superpowers:subagent-driven-development` ou `superpowers:executing-plans` sem antes executar as fases IntelliX (FASE 00 a 02 mínimo).

---

## Regra Inviolável — Verificação de Estrutura no Início de Sessão

Ao iniciar qualquer sessão em um projeto (`package.json` ou equivalente detectado pelo hook `intellix-project-check.py`):

1. **Se `[INTELLIX-CHECK]` aparecer no contexto da sessão** → apresentar os gaps ao usuário e perguntar:
   > "O projeto **[nome]** tem **N gap(s)** em relação ao padrão IntelliX (score: X/100). Quer adaptar agora com `intellix:project-kickoff` ou continuar sem adaptar por enquanto?"

2. **Nunca ignorar silenciosamente** o aviso do `[INTELLIX-CHECK]`.

3. **Esse aviso se repete a cada sessão** enquanto o projeto não seguir os padrões.

4. **Se o usuário escolher adaptar** → invocar `intellix:project-kickoff` imediatamente.

5. **Se o usuário escolher "mais tarde"** → registrar a decisão e continuar, mas repetir na próxima sessão.

---

## Os 7 Níveis de CLAUDE.md (hierarquia de contexto)

| # | Nível | Path | Escopo |
|---|-------|------|--------|
| 01 | Global User | `~/.claude/CLAUDE.md` | Você, em todo projeto |
| 02 | Enterprise | `/etc/claude/managed/` | Política da empresa |
| 03 | Projeto | `./CLAUDE.md` | Repo (vai pro git) |
| 04 | Projeto Local | `./CLAUDE.local.md` | Só seu (gitignore) |
| 05 | @imports | `@modulo.md` | Modular dentro dos outros |
| 06 | Subagent User | `~/.claude/agents/` | Agent global |
| 07 | Subagent Proj | `./.claude/agents/` | Agent do repo |

**Precedência:** subagent > local > projeto > enterprise > user

**Regras:**
- Nível 03 (`./CLAUDE.md`): stack, arquitetura, convenções — NUNCA secrets
- Nível 04 (`./CLAUDE.local.md`): DB local, paths absolutos, branches ativas — gitignored
- Nível 05: use `@modules/arquivo.md` para quebrar monolitos
