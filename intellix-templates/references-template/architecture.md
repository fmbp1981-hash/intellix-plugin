# Arquitetura — {{PROJECT_NAME}}

> Gerado em: {{CREATED_AT}} | Template: IntelliX SDD v{{TEMPLATE_VERSION}}
> Regras inegociáveis do projeto. Consulte ANTES de qualquer /plan.

## 1. Compartimentação de Behaviors

- Cada comportamento tem sua própria pasta dentro da rota
- Comportamento NUNCA importa de outro comportamento irmão
- Compartilhamento apenas via `lib/` ou `components/shared/`
- Estrutura: `app/(grupo)/rota/nome-do-behavior/`

## 2. Thin Client / Fat Server

- Toda regra de negócio em server actions (`action.ts`)
- Client apenas captura input e renderiza output recebido
- Re-validar permissões no server SEMPRE (consultar DB, não confiar no client)
- NUNCA validar role/permissão via variável JS no client

## 3. Estrutura Obrigatória por Behavior

```
nome-do-behavior/
├── action.ts      # server action — valida sessão + Zod + lógica
├── schema.ts      # Zod schema do input
└── form.tsx       # client component — captura input, exibe feedback
```

## 4. Imports Proibidos

- Client → server libs (use 'use server' para server actions)
- Behavior A → Behavior B (compartilhar via `lib/` apenas)
- Supabase queries diretas em componentes (usar via server action ou repository)

## 5. Informações do Projeto

- **Cliente:** {{CLIENT_NAME}}
- **Stack preset:** {{STACK_PRESET}}
- **Criado em:** {{CREATED_AT}}
- **Supabase project:** {{SUPABASE_PROJECT_ID}}
