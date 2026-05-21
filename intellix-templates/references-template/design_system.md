# Design System — {{PROJECT_NAME}}

> Gerado em: {{CREATED_AT}}

## Tokens de Cor

- **Primária:** `{{PRIMARY_COLOR}}` — ações principais, CTAs, botões primary
- **Secundária:** `{{SECONDARY_COLOR}}` — destaques, badges, estados de sucesso
- **Fundo:** `#FFFFFF` (light) / `#0F0F0F` (dark)
- **Texto:** `#111827` (light) / `#F9FAFB` (dark)
- **Bordas:** `#E5E7EB`
- **Destrutivo:** `#EF4444`

Definir em `tailwind.config.ts` — nunca hardcode hex nos componentes.

## Tipografia

- **Sans:** Inter (padrão Shadcn/UI)
- **Mono:** JetBrains Mono (código, refs, badges técnicos)
- Escala: 12 / 14 / 16 / 18 / 20 / 24 / 30 / 36 / 48

## Componentes

- **Primitivos:** SEMPRE de `@/components/ui` (Shadcn/UI)
- NUNCA criar Button, Input, Dialog, Card do zero — customizar via `variants` (cva)
- Componentes de negócio em `components/shared/`

## Spacing

- Múltiplos de 4 (Tailwind scale padrão)
- Padding de cards: `p-6`
- Gap entre elementos relacionados: `gap-4`
- Gap entre seções: `gap-8`
- Margin de containers: `mx-auto max-w-7xl px-4 sm:px-6 lg:px-8`

## Acessibilidade

- Contraste mínimo: 4.5:1 (WCAG AA)
- Focus ring visível em todos os elementos interativos
- Todo ícone clicável sem texto visível: `aria-label` obrigatório
- Suporte a `prefers-reduced-motion` em animações
