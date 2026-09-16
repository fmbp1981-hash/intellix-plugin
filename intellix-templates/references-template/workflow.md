# Workflow para Agentes IA — {{PROJECT_NAME}}

> Regras operacionais para Claude Code e subagentes neste projeto.
> Gerado em: {{CREATED_AT}}

## Antes de QUALQUER mudança

1. Ler `references/architecture.md` deste projeto
2. Ler a issue completa (caminho feliz + edge + erros + "Files to NOT Touch")
3. Listar os arquivos que vai tocar
4. Confirmar com o usuário ANTES de executar

## Durante a execução

- Nunca criar arquivo fora dos paths declarados na issue
- Nunca modificar arquivo listado em "Files to NOT Touch"
- Se precisar de novo arquivo não previsto → parar e perguntar ao usuário
- Context window > 60%? → fazer /clear e retomar com plano carregado

## Depois de cada issue

- Rodar: `npm run type-check` (tsc --noEmit)
- Rodar testes relacionados à issue
- Confirmar que nenhum arquivo fora da lista foi tocado
- Reportar arquivos criados/modificados

## /clear entre fases (obrigatório)

Execute /clear nos seguintes momentos:
- Após /plan aprovado → antes de /execute
- Após pesquisa de codebase (Frente 1) ou docs (Frente 2) → antes de escrever código
- Ao trocar de uma issue para outra
- Quando context window ultrapassar 60%

## Agentes por tipo de arquivo

Os agentes vêm do plugin IntelliX (não ficam neste repositório):

| Tipo | Agente |
|------|--------|
| Migrations + RLS, tipos, repositories | `intellix:model-writer` |
| Server Actions, route handlers, services, integrações | `intellix:action-writer` |
| Páginas, componentes, modais, hooks de UI | `intellix:component-writer` |
| Testes | `intellix:test-writer` |
| Reviews (estágios 2 e 3 do /execute) | `intellix:spec-reviewer`, `intellix:code-quality-reviewer` |
