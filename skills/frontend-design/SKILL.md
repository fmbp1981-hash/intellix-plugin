---
name: frontend-design-workflow
description: >
  Use esta skill sempre que o projeto envolver criação ou melhoria de qualquer interface
  de usuário — dashboard, landing page, SaaS, módulos de UI, componentes, redesign ou
  qualquer tela do sistema. Esta é a Fase 02 do fluxo IntelliX — executada após
  architecture (Fase 01) e antes de agent-creation/dev-standards. Também ativa quando
  o usuário mencionar: "criar interface", "construir UI", "design do sistema", "tela de",
  "painel", "dashboard", "landing page", "componentes visuais", "mobile-first".
user-invocable: false
---

# Fase 02 — Frontend Design

Orquestrador de UI/UX. Garante que nenhum componente seja escrito sem design system
definido. Executa 6 skills em sequência obrigatória antes de qualquer implementação visual.

> **PRÉ-REQUISITO:** A Fase 01 (architecture) deve estar concluída — rotas, tipos e
> schema definidos. Esta fase define O QUE e COMO parece antes da Fase 04 implementar.

---

## Quando executar esta fase

```
Projeto tem qualquer interface de usuário? → SEMPRE executar
Projeto é API-only sem UI? → PULAR
Projeto existente com UI já implementada sendo melhorada? → executar a partir do Passo 2
```

---

## Workflow — 6 Skills em Sequência Obrigatória

Anuncie cada fase para o usuário antes de executar:
```
[Fase 02 — X/6] Nome da skill — descrição do que está sendo feito...
```

---

### Passo 1 — Arquitetura de UI `vibestack-architect`

**Invoke:** `Skill("vibestack-architect")`

Antes de qualquer pixel, defina a estrutura:

**Para projetos novos:**
- Stack visual: Next.js 15 + Tailwind + Shadcn/UI (padrão IntelliX)
- Estrutura de componentes: `src/components/ui/` (primitivos) + `src/components/[feature]/` (compostos)
- Roteamento visual: grupos `(auth)`, `(dashboard)`, páginas públicas
- Layout architecture: root layout, dashboard layout, auth layout
- Scaffolding de componentes principais por feature

**Para projetos existentes (melhoria):**
- Mapear componentes existentes e suas dependências
- Identificar escopo exato da mudança
- Garantir compatibilidade com arquitetura atual
- Listar apenas o que será modificado

**Entregável obrigatório antes do Passo 2:**
Decisões de estrutura confirmadas. Lista dos componentes a criar/modificar.

---

### Passo 2 — Design System `ui-ux-pro-max`

**Invoke:** `Skill("ui-ux-pro-max")`

Define o sistema visual completo antes de escrever uma linha de CSS:

**Para projetos novos — gerar design system com:**
```bash
# Script da skill ui-ux-pro-max
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<tipo> <industria>" --design-system -p "<Nome>"
```

**Deve produzir:**
- Paleta de cores com variáveis CSS (primary, secondary, accent, background, foreground, muted, destructive)
- Tipografia: fonte display + fonte body (NUNCA Inter/Roboto/system-ui genérico)
- Escala de espaçamento e border-radius
- Estilo visual comprometido: minimalismo, glassmorphism, brutalism, dark luxury, etc.
- Padrões de layout: card, table, form, modal, sidebar
- Estados visuais: hover, focus, loading, error, empty state

**Para projetos existentes:**
- Verificar se existe `design-system/MASTER.md` ou equivalente
- Se existe: seguir regras definidas, não reinventar
- Se não existe: extrair design system do visual atual, depois propor melhorias

**Entregável obrigatório antes do Passo 2b:**
Design system documentado em `docs/design-system.md` — cores, fontes, tokens, anti-patterns visuais.

---

### Passo 2b — Tokens e Infraestrutura Tailwind `design-system-patterns`

**Invoke:** `Skill("design-system-patterns")`

Converte o design system conceitual do Passo 2 em infraestrutura real de tokens e tema:

- Criar tokens CSS primitivos → semânticos → de componente no `globals.css`
- Configurar tema Tailwind em `tailwind.config.ts` com as cores e fontes definidas
- Implementar sistema de dark/light mode via `next-themes` + CSS custom properties
- Definir escala de espaçamento, border-radius, sombras como tokens reutilizáveis
- Criar tipos TypeScript para os tokens (`theme.ts`) — zero magic strings
- Definir compound components patterns para os elementos principais da UI

**Entregável obrigatório antes do Passo 3:**
`tailwind.config.ts` e `globals.css` com todos os tokens do design system implementados.

---

### Passo 3 — Implementação Visual `frontend-design-pro`

**Invoke:** `Skill("frontend-design-pro")`

Implementa a UI com qualidade de $50k+ agency, **respeitando rigorosamente** os Passos 1 e 2.

**Regras absolutas:**
- Mobile-first: breakpoints `sm → md → lg → xl`
- Usar APENAS as cores e fontes definidas no Passo 2
- Seguir a estrutura de componentes do Passo 1
- Cada componente: semantic HTML + WCAG AA/AAA
- Nenhum `style={{}}` inline — apenas classes Tailwind
- Um signature detail obrigatório: grain, cursor customizado, mesh animado, split diagonal, etc.
- Assimetria, overlap e fluxo diagonal — quebrar o grid centrado genérico

**Estratégia de Motion/Animação (do `frontend-design`):**
- **Uma animação heroica e orquestrada** > dezenas de micro-interações dispersas
- Page load: staggered reveals com `animation-delay` por elemento
- Scroll: `IntersectionObserver` para entradas contextuais
- Hover: surpresa no estado — não apenas opacity/scale previsíveis
- React: usar `framer-motion` ou Motion library; HTML/CSS: CSS-only com `@keyframes`
- `prefers-reduced-motion`: SEMPRE — envolver animações em media query

**Perfect Images System (obrigatório):**
- Fotos reais (pessoas, produtos, texturas): URL direta Unsplash/Pexels
  `https://images.unsplash.com/photo-[ID]?w=1920&q=80`
- Hero/fundo/cenas conceituais: prompt detalhado para Flux/Midjourney v6
  Formato: `[IMAGE PROMPT START] ... --ar 16:9 --v 6 --q 2 [IMAGE PROMPT END]`
- NUNCA URLs inventadas, placeholders ou `image.jpg`

**Entregável obrigatório antes do Passo 3b:**
Componentes de página implementados, funcionais, com animações base e imagens reais.

---

### Passo 3b — Polish e Animações Avançadas `impeccable`

**Invoke:** `Skill("impeccable")`

Eleva o visual para nível production-grade com craft e detalhe excepcionais:

**Pré-requisito:** criar `PRODUCT.md` na raiz do projeto antes de invocar (se não existir):
```bash
node .claude/skills/impeccable/scripts/load-context.mjs
```
Se PRODUCT.md não existir, rode `/impeccable teach` para gerá-lo a partir de perguntas guiadas.

**Sub-comandos disponíveis (invocar conforme necessidade):**
- `/impeccable polish [componente]` — refinamento visual geral, hierarquia, espaçamento
- `/impeccable animate [componente]` — motion design, micro-interações, transições de página
- `/impeccable colorize [componente]` — sistema de cores, contraste, hierarquia cromática
- `/impeccable typeset [componente]` — tipografia, ritmo vertical, escalas de texto
- `/impeccable audit [página]` — análise completa de UI: cognitive load, UX copy, edge cases
- `/impeccable bolder [componente]` — design muito discreto? tornar mais assertivo
- `/impeccable quieter [componente]` — design muito lotado? simplificar

**Regras de aplicação:**
- Respeitar RIGOROSAMENTE os tokens e design system dos Passos 2/2b
- Usar `prefers-reduced-motion` em TODAS as animações
- Cada animação deve ter propósito — nenhum movimento cosmético sem função
- Framer Motion para React, CSS `@keyframes` para HTML puro

**Entregável obrigatório antes do Passo 4:**
Componentes polidos com animações de alta qualidade. `PRODUCT.md` atualizado com decisões de design.

---

### Passo 4 — Refinamento com Shadcn/UI `ckm-ui-styling`

**Invoke:** `Skill("ckm-ui-styling")`

Garante consistência e polimento com a biblioteca de componentes IntelliX:

- Substituir componentes customizados por equivalentes Shadcn/UI onde aplicável
- Configurar `components.json` do Shadcn alinhado com design system do Passo 2
- Aplicar variáveis CSS no `globals.css` para os tokens definidos
- Verificar acessibilidade: focus rings, aria-labels, keyboard navigation
- Padronizar loading states: `<Skeleton>` para conteúdo assíncrono
- Error states: `<Alert variant="destructive">` para erros de formulário

---

### Passo 5 — Auditoria de Qualidade

Revisão final obrigatória em 3 camadas — executar as 3 skills em sequência:

**5a — Web Design Guidelines** `Skill("web-design-guidelines")`
- Conformidade com Web Interface Guidelines (Apple HIG, Material Design, etc.)
- Hierarquia visual, espaçamento, consistência de padrões
- Micro-interações e estados de loading/error/empty

**5b — Acessibilidade WCAG** `Skill("accessibility")`
- Conformidade WCAG 2.1 AA/AAA completa
- Contraste de cores (mínimo 4.5:1 para texto normal, 3:1 para texto grande)
- Navegação por teclado: focus order lógico, visible focus ring, skip links
- Screen readers: aria-labels, aria-live, roles semânticos
- Tamanho mínimo de touch targets: 44×44px
- Imagens com `alt` descritivo, vídeos com legendas
- Performance de animações: `prefers-reduced-motion` em TODOS os keyframes

**5c — SEO Técnico** `Skill("seo")`
- Meta tags: `<title>`, `<meta description>`, Open Graph, Twitter Card
- Estrutura de headings: H1 único por página, hierarquia correta H2→H3
- URLs semânticas, canonical tags, sitemap.xml
- Core Web Vitals: LCP, CLS, FID/INP — verificar antes do deploy
- Schema.org markup para páginas de produto/serviço/landing
- Imagens: `loading="lazy"`, `width`/`height` definidos, formatos modernos (WebP/AVIF)

**Entregável:** Lista de issues encontradas (separada por camada) e correções aplicadas.

> **Fluxo completo Fase 02:**
> `vibestack-architect` → `ui-ux-pro-max` → `design-system-patterns` → `frontend-design-pro` → `impeccable` → `ckm-ui-styling` → `web-design-guidelines` + `accessibility` + `seo`

---

## Padrões de Componentes IntelliX

```typescript
// Estrutura obrigatória de componente
// src/components/[feature]/contact-card.tsx

import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Contact } from '@/types'

interface ContactCardProps {
  contact: Contact
  onEdit?: (id: string) => void
}

export function ContactCard({ contact, onEdit }: ContactCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-foreground">{contact.name}</h3>
          <Badge variant="secondary">{contact.status}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* ... */}
      </CardContent>
    </Card>
  )
}
```

```typescript
// Loading state padrão IntelliX
import { Skeleton } from '@/components/ui/skeleton'

export function ContactCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-2/3" />
      </CardContent>
    </Card>
  )
}
```

```typescript
// Error boundary padrão
'use client'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
      <h2 className="text-lg font-semibold text-destructive">Algo deu errado</h2>
      <Button onClick={reset} variant="outline">Tentar novamente</Button>
    </div>
  )
}
```

---

## Handover para Fase 03 ou 04

Ao concluir, informe:
> "Design system e UI concluídos. Próxima fase: **intellix:agent-creation** (se houver agentes) ou **intellix:dev-standards** para implementação dos demais módulos."

Atualize `.intellix-phase` para `dev`.

---

## Skills Relacionadas

| Quando usar | Skill |
|-------------|-------|
| UI com design máximo e fotos reais integradas | `frontend-design-pro` |
| Tokens CSS, tema Tailwind, design system em código | `design-system-patterns` |
| Polish, animação e craft avançado de componentes | `impeccable` |
| Design system avançado com tokens e slide deck | `ckm-design-system` |
| Banners, assets visuais para marketing | `ckm-banner-design` |
| Auditoria completa WCAG AA/AAA | `accessibility` |
| SEO técnico, meta tags, Core Web Vitals | `seo` |
| Auditoria de UI contra Web Interface Guidelines | `web-design-guidelines` |
| Design system existente — auditoria e extensão | `design-system` |

---

## Armadilhas comuns
- Escrever componentes antes de definir o design system → resultado inconsistente
- Usar Inter/Roboto/system-ui → visual genérico de IA, sem identidade
- Hardcode de cores (`text-blue-500`) → usar variáveis CSS do design system
- Pular loading states → UX quebrada em conexões lentas
- Componentes sem `aria-label` em botões sem texto → acessibilidade comprometida
