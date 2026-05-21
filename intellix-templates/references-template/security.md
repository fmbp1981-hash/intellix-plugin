# Checklist de Segurança — {{PROJECT_NAME}}

> Validar ANTES de cada PR/merge. Zero exceções.
> Gerado em: {{CREATED_AT}}

## Defense in Depth — 4 Camadas Obrigatórias

```
1. Middleware Next.js     → bloqueia rotas sem sessão válida
2. Server Action / Route  → valida input com Zod (schema obrigatório)
3. Server Action / Route  → re-valida permissões consultando DB
4. Supabase RLS Policy    → última linha de defesa no banco
```

Nenhuma camada confia na anterior. Se uma falhar, as outras seguram.

## Pré-PR Checklist

- [ ] Nenhuma API key em código client ou em arquivo commitado
- [ ] Toda server action valida sessão no início (`await supabase.auth.getUser()`)
- [ ] RLS habilitado em toda tabela Supabase nova
- [ ] Rate limiting em endpoints públicos
- [ ] Inputs sanitizados com Zod antes de qualquer operação
- [ ] Erros não expõem stack trace ao client
- [ ] CORS configurado restritivamente (nunca `*`)
- [ ] Secrets apenas em variáveis server-side (nunca `NEXT_PUBLIC_` para dados sensíveis)
- [ ] Nenhuma lógica de role/permissão no client

## Anti-patterns Críticos

```typescript
// ❌ NUNCA — validação de role no client
if (user.isAdmin) { /* hacker muda em 30s no DevTools */ }

// ✅ SEMPRE — buscar no banco no server action
const { data: profile } = await supabase
  .from('profiles')
  .select('role')
  .eq('id', user.id)
  .single()
if (profile.role !== 'admin') return unauthorized()
```

```typescript
// ❌ NUNCA — service role key no client
const supabase = createClient(url, process.env.NEXT_PUBLIC_SERVICE_ROLE_KEY!)

// ✅ SEMPRE — service role apenas em server (sem NEXT_PUBLIC_)
const supabase = createClient(url, process.env.SUPABASE_SERVICE_ROLE_KEY!)
```
