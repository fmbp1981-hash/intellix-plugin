# Security Rules — Padrão IntelliX

> Extraído de MASTER-ARCHITECTURE.md — índice em [§13–17](../MASTER-ARCHITECTURE.md).
> Consulte ao implementar autenticação, autorização, middleware, headers de segurança ou qualquer rota pública.

## 13. Segurança — Checklist por Nível

### Nível BÁSICO (Landing Pages, Sites Estáticos)
- [ ] Sem variáveis de ambiente sensíveis com `NEXT_PUBLIC_`
- [ ] Headers de segurança básicos no `next.config.ts`
- [ ] Sem `console.log` com dados em produção

### Defense in Depth — 4 Camadas Obrigatórias

As 4 camadas abaixo devem coexistir. **Nenhuma confia na anterior.** Se uma falhar, as outras seguram.

```
1. Middleware Next.js     → bloqueia rotas sem sessão válida
2. Server Action / Route  → valida input com Zod (schema obrigatório)
3. Server Action / Route  → re-valida permissões consultando DB (não confiar no client)
4. Supabase RLS Policy    → última linha de defesa no banco de dados
```

> **Anti-pattern crítico:** `if (user.isAdmin)` no client é contornável com DevTools em 30 segundos.
> Role/permission check SEMPRE no server, consultando o banco — nunca confiando em variável enviada pelo client.

---

### Nível COMPLETO (SaaS, CRM, APIs, Auth)
- [ ] Autenticação validada no servidor em toda operação sensível
- [ ] Rate limiting em todas as rotas públicas
- [ ] Input sanitizado e validado no servidor (Zod) antes de qualquer operação
- [ ] RLS ativo em todas as tabelas Supabase
- [ ] Secrets apenas em variáveis server-side (nunca `NEXT_PUBLIC_` para dados sensíveis)
- [ ] Stack traces nunca expostos para o cliente
- [ ] RBAC validado no servidor, nunca no cliente
- [ ] Headers de segurança completos (CSP, HSTS, X-Frame-Options)
- [ ] Logs sem dados sensíveis (PII, tokens, passwords)

```typescript
// next.config.ts — headers de segurança completos
const nextConfig = {
  async headers() {
    return [{
      source: '/(.*)',
      headers: [
        { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-XSS-Protection', value: '1; mode=block' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        {
          key: 'Content-Security-Policy',
          value: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        },
      ],
    }]
  },
}
```
