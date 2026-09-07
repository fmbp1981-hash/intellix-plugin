#!/bin/bash
# IntelliX Skill Router Hook (UserPromptSubmit)
# Lê o prompt do usuário via stdin e sugere skills relevantes.
# IntelliX Engineering Plugin v2.0 — 11 fases

PROMPT=$(cat)

suggest() {
  echo "SKILL RECOMMENDATION: Use a skill intellix:$1 antes de responder."
}

# Fase 00b — Code Audit (sistemas existentes — checar ANTES do kickoff)
echo "$PROMPT" | grep -qiE "revisar código|auditar|refatorar|reorganizar|código legado|melhorar qualidade|padronizar código|código bagunçado|dívida técnica|technical debt|enquadrar no padrão|código existente|qualidade do código" && suggest "code-audit"

# Fase 00 — Project Kickoff
echo "$PROMPT" | grep -qiE "novo projeto|criar projeto|iniciar projeto|scaffolding|estrutura inicial|começar sistema|onboarding projeto|criar do zero" && suggest "project-kickoff"

# Fase 01 — Architecture
echo "$PROMPT" | grep -qiE "arquitetura|schema|banco de dados|tabelas|modelagem|erd|rotas da aplicação|estrutura de pastas|design de sistema|repository|service layer|data layer|api design|paginação|rbac|decisão técnica" && suggest "architecture"

# Fase 02 — Frontend Design
echo "$PROMPT" | grep -qiE "interface|criar tela|criar página|criar componente|design system|design do sistema|dashboard|landing page|visual|layout|mobile.first|ui|ux|frontend|shadcn|tailwind|estilo|cores|tipografia|tema" && suggest "frontend-design-workflow"

# Fase 03 — Agent Creation
echo "$PROMPT" | grep -qiE "agente|agent|multi.?agent|whatsapp bot|chatbot|assistente de ia|automação de atendimento|blueprint de agente|nossoagent|bot de atendimento|criar bot|agente de vendas|agente de suporte|gptmaker|gpt maker" && suggest "agent-creation"

# Fase 04 — Dev Standards
echo "$PROMPT" | grep -qiE "typescript|tipagem|interface ts|padrão de código|naming|naming convention|eslint|linting|prettier|estrutura de componente|boas práticas|server action|tanstack|react query|zustand|zod|validação|caching|cache" && suggest "dev-standards"

# Fase 05 — Integration
echo "$PROMPT" | grep -qiE "evolution api|whatsapp|n8n|webhook|supabase.*(função|function|edge)|integração|z-api|waha|mensagem automática|enviar mensagem|anthropic sdk|openai sdk|api externa|rest api|realtime" && suggest "integration"

# Fase 06 — Security & Observability
echo "$PROMPT" | grep -qiE "segurança|security|vulnerabilidade|rate limit|rate.?limiting|sentry|auditoria de seg|owasp|lgpd|auth token|observabilidade|monitoramento|logs estruturado|csp|content security|csrf|headers de segurança|npm audit" && suggest "security-observability"

# Fase 07 — Test E2E
echo "$PROMPT" | grep -qiE "test|teste|e2e|playwright|cypress|jest|vitest|cobertura|qa|qualidade|smoke test|stress test|regressão|validar sistema|encontrar bugs|tdd|test.driven" && suggest "test-e2e"

# Fase 08 — Deploy & DevOps
echo "$PROMPT" | grep -qiE "deploy|vercel|dns|domínio|cloudflare|variável de ambiente|env|produção|release|publicar|colocar no ar|configurar domínio|ci.?cd|github actions|pipeline|devops|rollback|staging|feature flag|runbook|incidente|health check" && suggest "deploy"

# Fase 09 — Handoff
echo "$PROMPT" | grep -qiE "documentação final|readme|entregar|handoff|cliente|finalizar projeto|concluir projeto|débito técnico documentar|projeto pronto|adr|decisão de arquitetura|entregar para o cliente" && suggest "handoff"

# Fase 10 — Live Chat (opcional)
echo "$PROMPT" | grep -qiE "live chat|chat ao vivo|inbox|painel de atendimento|omnichannel|webchat|chat widget|atendimento humano|handoff humano|transferir para atendente|chat de suporte|helpdesk|inbox unificado|atendimento multicanal|atendimento ao vivo" && suggest "live-chat"

exit 0
