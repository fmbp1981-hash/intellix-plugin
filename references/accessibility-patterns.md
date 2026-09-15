# Accessibility Patterns — Padrão IntelliX

> Extraído de uma remediação real de WCAG 2.2 (achados Critical+Serious) em produção.
> Consulte ao criar qualquer diálogo/painel customizado (slide-over, modal), componente
> de seleção customizado (`Select`/dropdown), botão apenas-ícone ou campo de busca.

## Por que existe

Times constroem `SlideOver`/`Dialog`/`Select` do zero (CSS custom, sem lib) porque é
rápido — e esquecem que um `<div>` com `position: fixed` não é, por padrão, um diálogo
para tecnologia assistiva: não tem nome acessível, não trava o foco, não fecha com
Escape de forma confiável, e pode continuar exposto no DOM mesmo "fechado" visualmente.
Todo achado abaixo foi um bug real encontrado numa auditoria, não um exercício teórico.

**Regra de ouro:** se o projeto já usa uma primitiva real de diálogo (Radix, base-ui,
`<dialog>` nativo), ela já implementa focus trap e `role="dialog"` — não reimplemente
nada disto. Este padrão é para quando o time optou por markup customizado.

---

## 1. Hook compartilhado `useFocusTrap`

Um único hook cobre: foco inicial no primeiro elemento focável, ciclo de Tab/Shift+Tab
dentro do painel, `Escape` chamando `onClose`, e restauração do foco ao elemento anterior
ao fechar — **incluindo arbitragem entre diálogos aninhados** (um painel que abre outro
por cima, ex.: detalhe → composer de envio).

```ts
// src/hooks/use-focus-trap.ts
'use client';

import { useEffect, useRef } from 'react';

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface UseFocusTrapOptions {
  active: boolean;
  onClose: () => void;
}

// Pilha global de containers com trap ativo — permite diálogos aninhados sem que o
// listener do painel externo "roube" o Tab/Escape do painel interno mais recente.
const activeTrapStack: HTMLElement[] = [];

export function useFocusTrap<T extends HTMLElement>({ active, onClose }: UseFocusTrapOptions) {
  const containerRef = useRef<T>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!active) return;

    previousFocusRef.current = document.activeElement as HTMLElement | null;

    const container = containerRef.current;
    if (container) activeTrapStack.push(container);

    const raf = requestAnimationFrame(() => {
      const focusable = container?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      (focusable?.[0] ?? container)?.focus();
    });

    function handleKeyDown(e: KeyboardEvent) {
      // Só o trap mais interno (topo da pilha) reage — evita dois diálogos abertos
      // disputando o mesmo Escape/Tab.
      if (!container || activeTrapStack[activeTrapStack.length - 1] !== container) return;

      if (e.key === 'Escape') {
        onCloseRef.current();
        return;
      }
      if (e.key !== 'Tab') return;

      const focusable = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      cancelAnimationFrame(raf);
      document.removeEventListener('keydown', handleKeyDown);
      if (container) {
        const idx = activeTrapStack.lastIndexOf(container);
        if (idx !== -1) activeTrapStack.splice(idx, 1);
      }
      previousFocusRef.current?.focus();
    };
  }, [active]);

  return containerRef;
}
```

**Nota de ambiente (jsdom):** `el.offsetParent` é sempre `null` em jsdom (sem layout
engine) — não use `.filter((el) => el.offsetParent !== null)` para excluir elementos
ocultos da lista de focáveis se os testes rodam em Vitest/Jest + jsdom, ou todo teste de
Tab-cycling quebra. Filtre por visibilidade real só se o projeto tiver testes E2E
(Playwright, browser real) cobrindo esse caso.

---

## 2. Padrão de diálogo customizado (slide-over / modal)

```tsx
'use client';

import { useId } from 'react';
import { X } from 'lucide-react';
import { useFocusTrap } from '@/hooks/use-focus-trap';

export function SlideOver({ open, onClose, title, children }: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  const titleId = useId();
  const panelRef = useFocusTrap<HTMLDivElement>({ active: open, onClose });

  return (
    <>
      <div aria-hidden="true" onClick={onClose} className="fixed inset-0 ..." />

      <div
        ref={panelRef}
        {...(open && { role: 'dialog', 'aria-modal': true, 'aria-labelledby': titleId })}
        aria-hidden={!open}
        className="fixed top-0 right-0 ..."
      >
        <h2 id={titleId}>{title}</h2>
        <button onClick={onClose} aria-label="Fechar" tabIndex={open ? undefined : -1}>
          <X className="w-4 h-4" />
        </button>
        {children}
      </div>
    </>
  );
}
```

**Checklist obrigatório para todo painel/diálogo customizado:**

- [ ] `role="dialog"` + `aria-modal="true"` no elemento do painel — **condicionais a
      `open`**, nunca fixos. Um painel "fechado" que só é transladado via CSS
      (`translate-x-full`, `opacity-0`) continua no DOM — se `role="dialog"` for
      permanente, a página expõe um diálogo modal invisível, sem nome, o tempo todo.
      Achado real: dois módulos de um SaaS em produção carregavam um diálogo
      `aria-modal="true"` sem título toda vez que nenhum item estava selecionado —
      o estado *padrão* das duas telas.
- [ ] `aria-labelledby` aponta para um `id` real, presente sempre que `open=true`.
      Se o título pode mudar de elemento (ex.: modo de edição substitui o `<h2>` por
      um `<input>`), garanta que o `id` migra junto — senão o diálogo perde o nome
      acessível a meio da interação.
- [ ] Botão de fechar com `aria-label="Fechar"` (ou texto visível) — ícone sozinho
      (`<X />`) não tem nome acessível.
- [ ] Overlay/backdrop com `aria-hidden="true"` — é decorativo, não deve ser
      anunciado como um alvo interativo nomeado.
- [ ] Painel fechado não deve deixar elementos focáveis alcançáveis por Tab — use
      `tabIndex={-1}` no(s) elemento(s) interativo(s) do painel quando fechado, ou
      não renderize `children` interativo nesse estado.
- [ ] Se dois diálogos deste tipo puderem abrir um dentro do outro (comum em fluxos
      "detalhe → ação"), use a versão do `useFocusTrap` com pilha (seção 1) — a versão
      ingênua sem pilha faz o painel externo "vencer" o Tab/Escape do painel interno.

---

## 3. Padrão de `Select`/listbox customizado (sem migrar para uma lib)

Quando o projeto já tem um `Select` customizado (posicionamento via portal, etc.) e
trocar por Radix/base-ui é risco demais para o momento, adicione navegação por teclado
**in-place** com o padrão ARIA `listbox`/`option` + `aria-activedescendant` — o foco do
DOM fica no container, não se move opção a opção (evita reescrever a lógica de
portal/posicionamento já existente):

```tsx
// No trigger:
<button
  aria-haspopup="listbox"
  aria-expanded={open}
  aria-controls={`${baseId}-listbox`}
  onKeyDown={(e) => {
    if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) {
      e.preventDefault();
      setOpen(true);
    }
  }}
>

// No container das opções (portal):
<div
  role="listbox"
  id={`${baseId}-listbox`}
  tabIndex={-1}
  aria-activedescendant={`${baseId}-opt-${activeIndex}`}
  onKeyDown={(e) => {
    if (e.key === 'Escape') { setOpen(false); triggerRef.current?.focus(); }
    if (e.key === 'ArrowDown') setActiveIndex((i) => Math.min(i + 1, items.length - 1));
    if (e.key === 'ArrowUp') setActiveIndex((i) => Math.max(i - 1, 0));
    if (e.key === 'Enter' || e.key === ' ') selectItem(items[activeIndex]);
  }}
>
  {items.map((item, i) => (
    <div key={item.value} id={`${baseId}-opt-${i}`} role="option" aria-selected={item.value === value}>
      {item.label}
    </div>
  ))}
</div>
```

**Checklist:** `role="listbox"` no container das opções; `role="option"` +
`aria-selected` em cada item; `aria-activedescendant` no container aponta pro `id` do
item ativo; trigger com `aria-haspopup="listbox"` + `aria-expanded`; setas/Enter/Escape
funcionam sem mover o foco real do DOM.

---

## 4. Nomes acessíveis — regras rápidas

- **Botão apenas-ícone** (`<button><X /></button>`, `<button><Trash2 /></button>`) sempre
  precisa de `aria-label` — o SR não lê SVG.
- **Checkbox de seleção em tabela** (linha ou "selecionar todos") sem texto visível ao
  lado precisa de `aria-label` descritivo: `aria-label="Selecionar {nome}"` por linha,
  `aria-label="Selecionar todos"` no header. `title` sozinho é fallback frágil — prefira
  `aria-label` mesmo mantendo `title` para o tooltip visual.
- **Campo de busca com só `placeholder`** não tem nome acessível confiável — o
  `placeholder` some ao digitar e não é garantidamente exposto como accessible name por
  toda combinação de browser/AT. Sempre adicionar `aria-label` com o mesmo texto (ou
  mais descritivo) do placeholder.

---

## 5. Auditoria rápida (grep)

```bash
# Painéis fixed sem role="dialog" (candidatos a slide-over/modal customizado)
grep -rln "fixed inset-0" src/ | xargs grep -L "role=\"dialog\""

# Botões com ícone e sem aria-label
grep -rn "<button" src/ --include="*.tsx" -A2 | grep -B2 "^\s*<[A-Z][a-zA-Z]* className" | grep -v "aria-label"

# Checkboxes sem aria-label nem <label> ao redor
grep -rn "type=\"checkbox\"" src/ --include="*.tsx" -B3 -A1 | grep -v "aria-label\|<label"

# Inputs com placeholder e sem aria-label
grep -rln "placeholder=" src/ --include="*.tsx" | xargs grep -L "aria-label"
```

Nenhum destes greps substitui a skill `accessibility` (auditoria completa WCAG 2.2) —
são um primeiro filtro rápido para achar candidatos antes de rodar a auditoria formal.
