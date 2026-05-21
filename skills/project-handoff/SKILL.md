---
name: handoff
description: >
  Use esta skill sempre que o usuário mencionar: documentação final,
  README, entregar projeto, handoff, cliente, "projeto concluído",
  "preparar para o cliente", documentar decisões, "o que foi feito",
  débitos técnicos, "próximos passos após entrega".
  Esta é a Fase 07 — última fase do fluxo IntelliX.
---

# Fase 07 — Project Handoff

Gera a documentação final do projeto e prepara a entrega ao cliente.

## Workflow

### Passo 1 — README técnico

Gere o `README.md` seguindo o template IntelliX:

```markdown
# [Nome do Projeto]

> [Descrição em uma linha]

## Stack
- **Frontend**: Next.js 15 App Router + TypeScript + Tailwind + Shadcn/UI
- **Backend**: Supabase (PostgreSQL + Auth + Edge Functions)
- **Deploy**: Vercel
- **Integrações**: [listar: n8n, Evolution API, etc]

## Setup local

### Pré-requisitos
- Node.js 20+
- npm ou pnpm
- Conta Supabase
- [Outras contas necessárias]

### Instalação
\`\`\`bash
git clone [repo-url]
cd [projeto]
npm install
cp .env.example .env.local
# Preencher variáveis no .env.local
npm run dev
\`\`\`

### Variáveis de ambiente
Veja `.env.example` para todas as variáveis necessárias.

## Arquitetura
[Breve descrição das camadas do sistema]

## Comandos úteis
\`\`\`bash
npm run dev          # desenvolvimento
npm run build        # build de produção
npm run test         # testes unitários
npm run test:e2e     # testes E2E (Playwright)
npm run test:all     # todos os testes
\`\`\`

## Estrutura de pastas
\`\`\`
[Árvore de pastas resumida com comentários]
\`\`\`

## Decisões técnicas
[Por que Next.js App Router? Por que Supabase? Outras decisões importantes]

## Débitos técnicos conhecidos
- [ ] [Item 1 — prioridade: alta/média/baixa]
- [ ] [Item 2]

## Próximos passos sugeridos
1. [Feature sugerida 1]
2. [Feature sugerida 2]

## Contato e suporte
IntelliX.AI — [contato]
```

### Passo 2 — Checklist de entrega

- [ ] README.md completo e atualizado
- [ ] `.env.example` com todas as variáveis (sem valores reais)
- [ ] Todos os segredos removidos do histórico Git
- [ ] Branch `main` com último build passando
- [ ] Deploy de produção funcionando
- [ ] Credenciais de produção transferidas ao cliente
- [ ] Acesso ao repositório configurado para o cliente
- [ ] Acesso ao Vercel/Supabase configurado para o cliente

### Passo 3 — Documento de decisões (ADR resumido)

Para projetos maiores, gere um `docs/decisions.md`:

```markdown
# Decisões de Arquitetura

## [Data] — [Decisão]
**Contexto**: [Por que essa decisão foi necessária]
**Decisão**: [O que foi decidido]
**Consequências**: [Impactos positivos e negativos]
```

Atualize `.intellix-phase` para `done`.

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| Finalizar branch, decidir merge strategy e criar PR | `superpowers:finishing-a-development-branch` |
| Solicitar code review formal antes de entregar | `superpowers:requesting-code-review` |
| Revisar PR contra plano original e padrões | `code-review:code-review` |

---

## Armadilhas comuns
- ❌ README genérico sem instruções reais de setup → cliente não consegue rodar
- ❌ Variáveis reais no `.env.example` → vazar credenciais
- ❌ Débitos técnicos não documentados → surpresas futuras para o cliente
