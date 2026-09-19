# Manual Mestre de Implementação do IntelliX Engineering Framework

## Instrução definitiva para execução no Codex

**Versão:** 1.0

**Data:** 17 de setembro de 2026

**Status:** Diretriz de implementação para aprovação e execução controlada

**Repositório:** `https://github.com/fmbp1981-hash/intellix-plugin`

**Branch do programa:** `feat/intellix-multiagent-framework`

**Executor principal:** Codex

**Arquiteto e revisor independente padrão:** Claude Code

**Autoridade final:** responsável humano da IntelliX.AI

## 1 Finalidade deste manual

Este documento instrui o Codex a construir, validar e preparar para adoção o IntelliX Engineering Framework, uma plataforma profissional de desenvolvimento de software orientada por artefatos, contratos, risco e evidências. O framework deve funcionar com Claude Code, Codex, integração contínua e controle humano sem depender semanticamente de um único fornecedor de inteligência artificial.

O objetivo não é acumular prompts, agentes ou documentos. O objetivo é estabelecer um sistema operacional de engenharia que produza software organizado, seguro, testável, observável, reversível e auditável. O framework deve orientar desde a definição do produto até a entrega em produção, mantendo uma separação clara entre intenção de negócio, decisão arquitetural, especificação, execução, revisão e liberação.

O Codex deve usar este manual como carta de execução do programa. Cada alteração concreta continua subordinada ao Task Contract correspondente, ao fileset autorizado, às políticas normativas e aos gates aplicáveis. Este documento não autoriza merge na branch principal, deploy, acesso a segredos, alteração de permissões ou qualquer ação irreversível.

## 2 Resultado esperado

Ao final do programa, a IntelliX.AI deve possuir um framework que:

- mantenha uma única fonte normativa versionada;
- separe PRD, Architecture, ADR, SPEC e Task Contract;
- use `AGENTS.md` como entrada vendor-neutral e `CLAUDE.md` como adaptador fino;
- permita que Codex e Claude executem papéis substituíveis, sem incorporar fornecedores ao kernel;
- use Codex como executor principal de implementação, testes e refatoração;
- use Claude como arquiteto, investigador e revisor independente por padrão;
- trate CI como árbitro de evidências determinísticas para um commit exato;
- selecione especialidades dinamicamente conforme domínio, risco e superfície alterada;
- impeça conflito de fileset e escrita concorrente não coordenada;
- isole mudanças relevantes em branches e worktrees;
- aplique controles DevSecOps desde o planejamento;
- mantenha rastreabilidade entre requisito, decisão, código, teste, revisão, release e operação;
- ofereça perfis proporcionais para projetos `micro`, `standard` e `regulated`;
- preserve compatibilidade de projetos Claude-only durante a migração;
- prove o fluxo completo em um projeto piloto antes de propor merge ou adoção ampla.

O framework somente poderá ser considerado pronto quando esses resultados forem demonstrados por testes, validações negativas, evidência de CI e revisão independente. A existência de arquivos ou documentação, isoladamente, não comprova operação.

## 3 Estado inicial conhecido

O trabalho deve ocorrer no clone local:

```text
/Users/felipemaranhao/Documents/Codex/2026-09-16/referenced-chatgpt-conversation-this-is-an/work/intellix-plugin
```

Branch autorizada:

```text
feat/intellix-multiagent-framework
```

Baseline arquitetural mínimo esperado:

```text
59d0d3e docs: consolidate multi-agent target architecture
```

O commit pode ser posterior, mas `59d0d3e` deve permanecer no histórico da branch. O repositório já contém um kernel inicial em `framework/`, schemas, policies, roles, adapters, documentos arquiteturais, ADRs e cinco Task Contracts sequenciais. Esses ativos devem ser evoluídos, não substituídos por uma nova árvore metodológica paralela.

Antes de qualquer alteração, o Codex deve confirmar:

```bash
cd /Users/felipemaranhao/Documents/Codex/2026-09-16/referenced-chatgpt-conversation-this-is-an/work/intellix-plugin
git fetch origin
git switch feat/intellix-multiagent-framework
git pull --ff-only origin feat/intellix-multiagent-framework
git status --short
git log --oneline -5
git merge-base --is-ancestor 59d0d3e HEAD
```

O Codex deve parar se estiver no diretório errado, na branch errada, diante de alterações locais desconhecidas, divergência que impeça fast-forward ou ausência do baseline no histórico.

## 4 Princípios obrigatórios

### 4.1 Artefatos versionados governam o trabalho

Conversas, prompts e memória de agentes podem ajudar na análise, mas não são estado oficial. Toda decisão durável deve existir em artefato versionado e verificável. Um novo executor deve conseguir reconstruir a intenção, o escopo e o estado do trabalho sem depender do histórico de conversa.

### 4.2 Um fato possui uma autoridade

Cada tipo de informação deve ter uma única fonte canônica. Documentos explicativos e arquivos de adapter podem referenciar ou projetar essa informação, mas não podem redefini-la. Quando duas fontes discordarem, o Codex deve aplicar o modelo de precedência e registrar o conflito; não deve escolher silenciosamente a versão mais conveniente.

### 4.3 O kernel é independente de fornecedor

O kernel define contratos, papéis, gates, lifecycle e policies. Ele não deve conter preferências por Claude, Codex ou outro executor. Preferências de projeto e capacidade de adapters pertencem ao binding do projeto e à camada de adapters.

### 4.4 O contrato limita a execução

Cada alteração não trivial deve estar ligada a um Task Contract. O contrato define resultado, risco, fileset, dependências, executor, revisor, gates, critérios de aceite, comandos de verificação e rollback. O executor não pode ampliar o escopo porque encontrou uma oportunidade de melhoria.

### 4.5 Risco determina a cerimônia

Projetos e tarefas de maior risco exigem mais evidência, isolamento e aprovação. O framework deve evitar burocracia uniforme. Uma correção documental de baixo risco e uma migration destrutiva não podem receber o mesmo tratamento.

### 4.6 Segurança começa no planejamento

Threat modeling, classificação de dados, controle de acesso, gestão de segredos, dependências, logs, rollback e abuso devem ser considerados antes do código. A revisão de segurança não pode ser um checklist aplicado apenas no fim.

### 4.7 Quem implementa não aprova sozinho

O executor pode verificar o próprio trabalho, mas essa verificação não substitui revisão independente quando o risco ou a policy a exigir. O revisor não deve alterar silenciosamente a worktree do executor. Ele registra achados, severidade e evidência; o executor corrige em novo ciclo.

### 4.8 CI verifica fatos objetivos

CI deve validar schema, lint, tipos, testes, segurança e outros critérios automatizáveis para o commit exato revisado. Uma LLM não substitui esses checks. Ao mesmo tempo, CI não decide se uma arquitetura é adequada ou se uma regra de negócio corresponde à intenção do produto.

### 4.9 Reversibilidade faz parte do design

Mudanças de dados, API, infraestrutura, autenticação, permissões e deploy precisam de estratégia de rollback ou contenção antes da implementação. A ausência de rollback em tarefa de risco alto ou crítico impede o estado `READY`.

### 4.10 Automação deve falhar de forma fechada

Ausência, inconsistência ou indeterminação em fonte, identidade, CI, fileset, dependência ou aprovação obrigatória deve bloquear a progressão. O framework não pode interpretar “não foi possível verificar” como sucesso.

## 5 Fonte normativa e modelo de precedência

No MVP, o kernel canônico permanece neste repositório, dentro de `framework/`. Essa permanência reduz risco de migração prematura. O desenho deve continuar preparado para extração futura, sem dependência de `${CLAUDE_PLUGIN_ROOT}`, versão do plugin ou caminhos globais de fornecedor.

O mapa de autoridade é:

| Informação | Fonte canônica | Consumidores derivados |
| --- | --- | --- |
| Contratos, lifecycle, papéis e gates | `framework/framework.yaml` e schemas/policies referenciados | validadores, generators e adapters |
| Perfis, comandos e defaults do projeto | `intellix.yaml` no projeto consumidor | dispatcher e CI |
| Decisões arquiteturais | ADRs aceitos do projeto | Architecture, SPEC e tasks |
| Comportamento de produto | PRD e SPEC aprovados | Task Contracts e testes |
| Unidade executável de trabalho | `tasks/TASK-NNN.yaml` | runtime, worktree, PR e handoff |
| Resultado determinístico | CI para o SHA exato | elegibilidade de revisão e merge |
| Aprovação humana | ação autenticada externa | referência local de auditoria |
| Merge, release e deploy | GitHub e provedor de entrega | relatórios e handoff |
| Operação do Claude | `global-config/metodologia.yaml` como fonte do adapter | instalação em `~/.claude` |

Precedência para resolução de conflitos:

1. política organizacional versionada;
2. waiver válido e autenticado, quando a policy permitir exceção;
3. ADR aceito e aplicável;
4. Architecture aprovada;
5. SPEC aprovada;
6. Task Contract aprovado;
7. configuração do projeto;
8. instrução do adapter;
9. mensagem da sessão.

Uma camada inferior não pode enfraquecer uma superior. `AGENTS.md`, `CLAUDE.md`, skills e comandos devem ser entradas operacionais curtas. Eles não podem duplicar integralmente as policies nem se apresentar como nova fonte normativa.

## 6 Arquitetura alvo

```text
Humano e Product Owner
        │
        ▼
Artefatos de produto e arquitetura
PRD → Architecture → ADRs → SPEC
        │
        ▼
Kernel IntelliX vendor neutral
contracts · schemas · roles · policies · lifecycle
        │
        ▼
Control plane determinístico
validate · plan · dispatch · ownership · evidence
        │
        ├─────────────┬─────────────┐
        ▼             ▼             ▼
Claude adapter   Codex adapter   CI adapter
architect/review implementation deterministic checks
        │             │             │
        └─────────────┴─────────────┘
                      │
                      ▼
             PR e decisão humana
                      │
                      ▼
             release e operação
```

### 6.1 Kernel

O kernel contém apenas regras portáveis. Schemas devem ser validados automaticamente. Policies devem usar IDs canônicos. Papéis devem declarar permissões, entradas, saídas e gates, sem selecionar fornecedor preferido.

### 6.2 Control plane

O control plane deve permanecer pequeno. Suas responsabilidades são validar um projeto por raiz explícita, confirmar dependências, controlar lifecycle, detectar colisões de fileset, resolver um executor permitido, reservar ownership, registrar evidências e bloquear transições inválidas. Ele não deve se tornar um workflow engine genérico nem tomar decisões de produto ou arquitetura.

### 6.3 Adapters

Adapters traduzem o contrato do kernel para a ferramenta concreta. O adapter do Codex deve instruir leitura, execução, testes e handoff. O adapter do Claude deve suportar arquitetura, investigação, execução quando atribuída e revisão independente. O adapter de CI deve vincular jobs ao SHA exato. Adapters são substituíveis e não possuem autoridade para redefinir o kernel.

### 6.4 Binding do projeto

Cada projeto consumidor deve declarar perfil, comandos, caminhos, versão e digest do kernel, adapters permitidos e defaults. O projeto deve consumir um snapshot ou pacote fixado. Alterar uma cópia gerada deve produzir drift detectável.

## 7 Orquestração multiagente

A IntelliX deve usar orquestração dinâmica, não uma hierarquia permanente de Tech Lead, banco, backend e frontend.

O papel de orquestração consiste em:

- ler o Task Contract e as dependências;
- identificar o domínio predominante;
- adicionar especialistas apenas quando acionados por risco ou superfície;
- escolher um executor instalado e autorizado;
- garantir independência do revisor;
- limitar contexto e fileset;
- coordenar handoff por artefatos;
- deixar fatos objetivos para CI;
- escalar decisões não autorizadas ao humano.

Os papéis canônicos incluem `architect`, `product-spec-author`, `database-engineer`, `backend-engineer`, `frontend-engineer`, `integration-engineer`, `platform-engineer`, `test-engineer`, `security-reviewer`, `accessibility-reviewer`, `observability-reviewer` e `release-manager`.

Esses papéis representam capacidades. Eles não precisam corresponder a processos ou agentes permanentes. Uma tarefa vertical pequena pode ser implementada por um único executor com um papel principal e dois gates especializados. Uma migration de autenticação pode ativar database, backend e security. Um ajuste visual pode ativar frontend e accessibility. O framework deve evitar ativar todos os papéis por padrão.

Resolução de executor:

1. executor explícito no Task Contract;
2. default permitido do projeto;
3. adapter atual em projeto legado, quando a policy autorizar;
4. bloqueio e solicitação de escolha explícita.

Se Claude implementar, Claude não pode satisfazer sozinho o gate de revisão independente. Se Codex implementar, Claude é o revisor padrão recomendado. A policy deve permitir outros pares desde que identidade, capacidade e independência sejam comprovadas.

## 8 Cadeia de artefatos

### 8.1 PRD

O PRD define problema, usuários, objetivos, requisitos, regras de negócio, métricas, restrições e critérios de sucesso. Ele não distribui tarefas entre agentes nem descreve detalhes de implementação.

### 8.2 Architecture

Architecture define boundaries, componentes, integrações, modelo de dados, confiança, segurança, disponibilidade, observabilidade, ambientes e decisões de plataforma. Mudanças significativas devem ser sustentadas por ADR.

### 8.3 ADR

Cada ADR registra contexto, decisão, alternativas, consequências, estado e data. Somente decisão humana explícita pode promover uma mudança arquitetural proposta para `Accepted`. O Codex pode preparar o ADR, analisar alternativas e implementar uma decisão já aceita; não pode declarar sua própria proposta como aprovada.

### 8.4 SPEC

A SPEC transforma intenção em comportamento testável. Deve conter precondições, happy path, edge cases, error cases, entradas, saídas, contratos e requisitos não funcionais aplicáveis. Não deve ser uma lista de arquivos nem uma ordem de agente.

### 8.5 Task Contract

O Task Contract é a menor unidade auditável de implementação. Deve declarar objetivo verificável, fontes, risco, ownership, fileset, dependências, critérios de aceite, verificações, gates, rollback e evidências de handoff.

Estados canônicos:

```text
DRAFT → READY → IN_PROGRESS → IN_REVIEW → DONE
                    ↘ BLOCKED ↗
IN_REVIEW → IN_PROGRESS quando houver correções
```

Merge, release, deploy e verificação operacional são estados derivados dos sistemas externos. Eles não devem ser duplicados como verdade editável no Task Contract.

## 9 Definição de Ready

Uma tarefa somente passa de `DRAFT` para `READY` quando:

- suas fontes existem sob a raiz declarada do projeto;
- o ID corresponde ao nome do arquivo;
- objetivo e critérios de aceite são verificáveis;
- riscos e ações irreversíveis estão classificados;
- papéis existem no Role Registry;
- executor e revisor são instalados, permitidos e independentes;
- filesets são relativos ao repositório, limitados e sem colisão ativa;
- dependências são válidas, acíclicas e satisfeitas;
- gates atendem ou superam a policy de risco;
- tarefa de risco alto ou crítico possui rollback;
- decisões arquiteturais necessárias estão aceitas;
- comandos de verificação são executáveis no ambiente previsto;
- nenhuma pergunta em aberto muda materialmente a solução.

Falhar qualquer condição mantém a tarefa em `DRAFT` ou `BLOCKED`. O Codex não deve usar alteração de status para contornar falta de informação.

## 10 Protocolo de execução do Codex

Para cada tarefa, o Codex deve seguir esta sequência.

### 10.1 Descoberta

1. Confirmar repositório, branch, worktree e estado limpo.
2. Ler `AGENTS.md`, `CLAUDE.md`, `intellix.yaml` quando existir, kernel, policies, sources e Task Contract.
3. Executar baseline de validação antes das alterações.
4. Inspecionar código e testes relevantes com busca direcionada.
5. Registrar inconsistências ou lacunas que possam invalidar o plano.

### 10.2 Planejamento

1. Revalidar objetivo e critérios de aceite.
2. Confirmar o fileset exato.
3. Mapear teste para cada critério de aceite.
4. Identificar threat scenarios e riscos de regressão.
5. Confirmar rollback e dependências.
6. Promover a tarefa para `READY` somente se a Definition of Ready estiver satisfeita.

### 10.3 Isolamento

- risco baixo: branch curta obrigatória; worktree opcional conforme perfil;
- risco médio, alto ou crítico: branch e worktree dedicados;
- um owner ativo por fileset gravável;
- nenhuma limpeza forçada de worktree suja;
- nenhuma mudança fora do fileset sem novo plano e autorização.

Enquanto o programa usar a branch única autorizada, o procedimento de linked worktree definido em `docs/adr/0002-operational-orchestrator.md` deve ser seguido. O Codex deve interromper a preparação se não conseguir preservar alterações do usuário.

### 10.4 Implementação

1. Alterar o estado para `IN_PROGRESS`.
2. Fazer a menor mudança coerente que satisfaça o contrato.
3. Manter lógica de negócio e controles de autorização no servidor.
4. Não inserir segredos, tokens ou dados reais em código, fixtures ou logs.
5. Criar ou atualizar testes durante a implementação.
6. Executar verificações focadas após cada unidade significativa.
7. Não instalar dependências sem previsão no contrato e análise de risco.
8. Parar se a solução exigir arquivo proibido, mudança arquitetural ou escopo adicional.

### 10.5 Verificação

1. Rodar todos os comandos declarados no contrato.
2. Rodar testes negativos relevantes.
3. Confirmar que o diff contém apenas arquivos permitidos.
4. Executar verificação de whitespace, compilação, lint e tipos aplicáveis.
5. Reexecutar validação completa do framework.
6. Guardar resultados vinculados ao commit.

### 10.6 Revisão e handoff

1. Alterar o estado para `IN_REVIEW`.
2. Produzir handoff com digest do contrato, SHA, diff, testes, riscos e questões abertas.
3. Entregar ao revisor independente acesso de leitura, sem ownership da worktree.
4. Classificar achados por severidade e evidência.
5. Retornar a `IN_PROGRESS` quando houver correções.
6. Limitar o ciclo normal a três rodadas; depois disso, escalar causa estrutural ao humano.

### 10.7 Conclusão

A tarefa somente pode alcançar `DONE` quando critérios de aceite, verificações, gates e evidências estiverem completos. `DONE` não autoriza merge ou deploy. O Codex deve criar commit focado e pode fazer push apenas para a branch explicitamente autorizada.

## 11 DevSecOps obrigatório

### 11.1 Threat modeling proporcional

Durante o planejamento, classificar pelo menos:

- ativos protegidos;
- atores e boundaries de confiança;
- entradas não confiáveis;
- ameaças de spoofing, tampering, repudiation, disclosure, denial of service e privilege escalation quando aplicáveis;
- abuso de regras de negócio;
- impacto multi-tenant;
- riscos de supply chain;
- riscos de modelo, prompt injection e tool abuse em sistemas com IA.

Tarefas de risco alto ou crítico devem registrar ameaças e mitigação no contrato, ADR ou artefato de segurança referenciado.

### 11.2 Identidade e autorização

- negar por padrão;
- validar autorização no servidor em cada operação sensível;
- separar autenticação, autorização e tenancy;
- aplicar menor privilégio;
- impedir IDOR e acesso cross-tenant;
- usar RLS quando a plataforma de dados a suportar, sem tratá-la como único controle;
- testar usuários, organizações, papéis e estados não autorizados;
- registrar mudanças de privilégios em trilha de auditoria.

### 11.3 Dados e privacidade

- classificar dados públicos, internos, confidenciais e regulados;
- coletar somente o necessário;
- cifrar em trânsito e em repouso conforme o risco;
- impedir PII e segredos em logs;
- definir retenção e descarte;
- usar dados sintéticos em testes;
- documentar subprocessadores e transferências quando aplicável;
- incorporar requisitos de LGPD ao projeto regulado.

### 11.4 Segredos

- nunca versionar segredo;
- usar gestores de segredo e credenciais temporárias quando disponíveis;
- escanear repositório e artefatos;
- rotacionar imediatamente qualquer segredo exposto;
- separar credenciais de executor, aprovador e produção;
- não aceitar texto `actor: human` como prova de identidade.

### 11.5 Supply chain

- fixar versões e lockfiles;
- avaliar nova dependência antes da instalação;
- executar análise de vulnerabilidade e licenças;
- gerar SBOM quando o perfil ou cliente exigir;
- proteger workflows contra execução de código não confiável com credenciais;
- limitar permissões de tokens de CI;
- assinar ou atestar artefatos quando a maturidade do projeto justificar.

### 11.6 Segurança de código e runtime

- validação de entrada e encoding de saída;
- queries parametrizadas;
- proteção contra SSRF, CSRF, XSS, injection e path traversal;
- timeouts, limites de payload e rate limiting;
- idempotência em operações repetíveis;
- tratamento seguro de erros;
- logs estruturados sem informação sensível;
- configuração segura por padrão;
- headers e cookies apropriados;
- dependências e imagens mínimas.

### 11.7 Infraestrutura e deploy

- infraestrutura como código quando houver recursos persistentes;
- ambientes separados;
- mudanças de produção revisadas e rastreáveis;
- plano de rollout, rollback e verificação;
- migrations compatíveis com expansão e contração para mudanças críticas;
- backup e restore testados quando dados persistentes estiverem em risco;
- nenhuma alteração de produção por credencial compartilhada do executor.

## 12 Estratégia de testes e qualidade

Cada critério de aceite deve possuir uma ou mais evidências. O conjunto proporcional inclui:

- testes unitários para regras e transformações;
- testes de contrato para APIs e integrações;
- testes de integração para boundaries reais;
- testes de migration e rollback;
- testes de autorização e isolamento de tenant;
- testes E2E para jornadas críticas;
- testes de acessibilidade para interfaces;
- testes de desempenho quando houver SLO ou volume relevante;
- testes de resiliência para timeout, retry, circuit breaking e indisponibilidade;
- análise estática, dependency scanning e secret scanning;
- testes negativos do próprio framework.

O Codex deve rejeitar testes que apenas reproduzem a implementação sem validar comportamento. Flakiness conhecida deve ser registrada e tratada; repetir testes até passarem não constitui evidência.

## 13 Integração contínua como árbitro determinístico

CI deve operar sobre o commit exato que foi revisado. O runtime precisa registrar repositório, branch, SHA, jobs obrigatórios e resultado. Checks ausentes, antigos, cancelados, falhos ou indeterminados bloqueiam progressão.

Pipeline mínimo recomendado:

1. validação de contratos e schemas;
2. verificação de fileset e artefatos gerados;
3. lint e formatação;
4. type checking e build;
5. testes unitários e integração;
6. security scanning e dependency audit;
7. testes específicos de policy;
8. empacotamento reproduzível quando aplicável;
9. evidência vinculada ao SHA.

O framework não deve usar a saída textual de uma LLM como check determinístico. Revisões semânticas podem ser registradas ao lado da CI, com proveniência separada.

## 14 Observabilidade e operação

Mudanças que criem ou alterem comportamento operacional devem definir:

- eventos e logs estruturados;
- métricas de negócio e técnicas;
- traces em boundaries distribuídos;
- correlation IDs;
- SLI e SLO quando necessários;
- alertas acionáveis, com owner e runbook;
- dashboards mínimos;
- sinal de sucesso pós-deploy;
- sinal de rollback;
- custo e retenção de telemetria.

O revisor de observabilidade deve ser acionado apenas quando a superfície exigir. O framework não deve criar telemetria ornamental sem decisão operacional associada.

## 15 Release deploy e handoff

### 15.1 Release

Release exige artefato versionado, changelog, compatibilidade, migration plan, rollback e evidência do SHA. Tarefas de implementação não concedem autoridade de release.

### 15.2 Deploy

Deploy exige autorização humana explícita e autenticada quando envolver produção. Estratégias possíveis incluem rolling, blue-green, canary e feature flags. A escolha deve refletir risco e capacidade real da plataforma.

### 15.3 Verificação pós deploy

Após deploy, verificar saúde, logs, métricas, jornada crítica, migrations e erros. A ausência de alerta não comprova sucesso. Registrar resultado no sistema de entrega, não apenas no chat.

### 15.4 Handoff

O pacote de handoff deve informar:

- objetivo e estado;
- commit e artefato exatos;
- mudanças de arquitetura e ADRs;
- comandos e resultados de verificação;
- riscos residuais;
- configuração e secrets necessários sem expor valores;
- migrations;
- dashboards e runbooks;
- rollback;
- limitações e próximos passos;
- owners operacionais.

## 16 Perfis de projeto

### 16.1 Micro

Adequado para protótipos e mudanças pequenas sem dados sensíveis ou operação crítica. Mantém contrato simplificado, fileset, risco, testes e revisão proporcional. Não elimina segurança básica nem rastreabilidade.

### 16.2 Standard

Perfil padrão para produtos e SaaS. Usa Task Contract completo, CI, revisão independente, policies de segurança, observabilidade e release controlado.

### 16.3 Regulated

Aplicável quando há requisitos legais, dados sensíveis, auditoria ou impacto relevante. Exige approvals autenticados, segregação de funções, retenção de evidência, gates de compliance, threat modeling e operação reforçada.

O perfil define mínimos. Uma tarefa pode exigir controles superiores ao perfil por causa do risco específico.

## 17 Plano de implementação em cinco tarefas

O programa deve seguir a ordem abaixo. Tasks posteriores não podem começar enquanto dependências e revisão da anterior estiverem pendentes.

### 17.1 TASK 001 Autoridade e raiz do projeto

Objetivo: consolidar a autoridade do framework e garantir validação fail-closed contra uma raiz explícita de projeto consumidor.

Entregas essenciais:

- opção explícita `--root`;
- separação entre raiz do plugin e raiz do projeto;
- remoção de fatos de fornecedor do kernel;
- detecção de traversal, paths absolutos indevidos, roles desconhecidos e IDs divergentes;
- fixtures externas positivas e negativas;
- direção explícita repositório para instalação;
- testes de execução a partir de diferentes diretórios.

### 17.2 TASK 002 Distribuição e adapters gerados

Objetivo: distribuir snapshot versionado e fixado do kernel para projetos consumidores, com geração dos adapters.

Entregas essenciais:

- versão e digest do kernel;
- sync/bootstrap unidirecional;
- detecção de drift e adulteração;
- geração de `AGENTS.md` e `CLAUDE.md` sem duplicar policies;
- fixtures de projeto novo, snapshot antigo e snapshot alterado;
- compatibilidade com instalação Claude existente.

### 17.3 TASK 003 Dispatcher e lifecycle

Objetivo: implementar um dispatcher determinístico e pequeno.

Entregas essenciais:

- validação de `READY`;
- resolução de executor e fallback explícito;
- compatibilidade Claude-only;
- lifecycle mínimo;
- verificação de dependências, gates e filesets;
- registro durável de decisões e bloqueios;
- ausência de decisões arquiteturais autônomas.

### 17.4 TASK 004 Ownership worktrees e handoff

Objetivo: isolar execução e formalizar transferência entre adapters.

Entregas essenciais:

- reserva exclusiva de fileset;
- detecção de colisões de globs;
- proteção de worktree suja;
- worktree obrigatório por risco;
- handoff com contrato, SHA, diff e evidência;
- revisor independente sem ownership de escrita;
- bloqueio de autoaprovação.

### 17.5 TASK 005 CI por revisão e piloto

Objetivo: provar o método completo em um projeto limpo e ligar checks ao SHA revisado.

Entregas essenciais:

- workflow CI portátil;
- bloqueio de check ausente, antigo ou falho;
- fixtures para `micro`, `standard` e `regulated`;
- piloto end-to-end em macOS e Linux quando disponíveis;
- relatório de aceitação;
- documentação de migração;
- proposta de merge somente após revisão independente e decisão humana.

## 18 Política de commits branches e worktrees

- uma task deve produzir commits focados e explicáveis;
- commits não podem misturar refatorações oportunistas;
- a branch do programa permanece `feat/intellix-multiagent-framework` enquanto essa autorização estiver vigente;
- nenhuma branch principal pode receber merge automático;
- nenhuma operação destrutiva de Git é permitida;
- não usar `reset --hard`, limpeza forçada ou remoção de worktree suja;
- todo push deve ocorrer apenas para a branch autorizada;
- tags e releases exigem autorização separada;
- o Codex deve conferir o inventário de arquivos antes do commit;
- evidências devem citar o SHA final, não apenas o nome da branch.

## 19 Gates humanos e limites de autonomia

O Codex pode executar sem nova confirmação atividades reversíveis e previstas pelo Task Contract: leitura, edição do fileset, criação de testes, validação local, commit focado e push para a branch autorizada.

O Codex deve parar e solicitar decisão humana quando houver:

- mudança de objetivo ou requisito de produto;
- novo boundary arquitetural;
- ADR que precise ser aceito;
- ampliação de fileset;
- nova dependência significativa;
- waiver ou redução de controle;
- credencial, segredo ou permissão adicional;
- ação destrutiva ou irreversível;
- migration sem rollback seguro;
- alteração de branch protection;
- merge em branch principal;
- deploy ou alteração em produção;
- conflito entre fontes normativas;
- dúvida que altere materialmente a solução.

Uma aprovação local editável pode registrar a intenção durante desenvolvimento, mas não prova identidade para merge ou produção. O framework deve manter essa distinção explícita.

## 20 Anti padrões proibidos

- criar nova pasta metodológica paralela à estrutura existente;
- manter hierarquia permanente de Tech Lead, database, backend e frontend;
- ativar todos os especialistas para toda tarefa;
- usar prompts ou chats como fonte oficial;
- duplicar integralmente policies em `AGENTS.md`, `CLAUDE.md`, skills e commands;
- inserir `preferred_adapter` em roles do kernel;
- transformar o dispatcher em agente autônomo;
- permitir que LLM determine resultado de CI;
- exigir cross-model review de toda mudança trivial sem relação com risco;
- dispensar revisão independente em mudança crítica;
- tornar worktree obrigatório para alteração trivial em perfil que permita exceção;
- editar arquivos gerados como se fossem fonte;
- sincronizar alterações da instalação viva de volta para o repositório automaticamente;
- migrar indiscriminadamente todo o histórico de `issues/`;
- criar onze ou mais estados manuais para imitar GitHub e deploy;
- aceitar `actor: human` como autenticação;
- marcar ADR como aceito por decisão do próprio executor;
- ocultar falha de ferramenta, teste ou CI;
- corrigir fora do escopo sem atualizar o contrato;
- misturar merge ou deploy com conclusão técnica da task.

## 21 Critérios de conclusão do framework

O programa somente poderá ser proposto para merge quando:

- as cinco tasks estiverem `DONE` com evidência;
- todos os schemas e artefatos normativos validarem;
- testes positivos e negativos passarem;
- o kernel não depender de um fornecedor;
- projetos consumidores validarem por raiz explícita;
- snapshot e digest detectarem drift;
- adapters forem gerados ou validados a partir da autoridade;
- dispatcher respeitar lifecycle, risco, fileset e dependências;
- fallback Claude-only estiver testado;
- worktrees e ownership bloquearem conflitos com segurança;
- revisão independente não puder ser autoatribuída;
- CI estiver vinculada ao SHA exato;
- os três perfis tiverem cobertura;
- o piloto end-to-end passar em ambientes suportados;
- segurança, observabilidade, rollback e handoff forem demonstrados;
- documentação de adoção e migração estiver atualizada;
- riscos residuais forem apresentados com clareza;
- Claude concluir revisão independente sem achado bloqueante;
- o humano aprovar o merge.

## 22 Relatório obrigatório ao fim de cada tarefa

O Codex deve entregar um relatório com:

1. task e estado final;
2. branch, worktree e commit;
3. objetivo entregue;
4. inventário de arquivos criados e alterados;
5. decisões técnicas;
6. critérios de aceite e evidência associada;
7. comandos executados e resultados;
8. testes positivos e negativos adicionados;
9. análise de segurança;
10. riscos residuais;
11. divergências do contrato;
12. rollback confirmado;
13. itens para revisão independente;
14. confirmação de que a tarefa seguinte não foi iniciada;
15. decisão humana necessária, se houver.

Não usar frases genéricas como “tudo certo” ou “testes passaram” sem comando, resultado e escopo.

## 23 Ordem de ativação para o Codex

Ao receber este documento, o Codex deve:

1. localizar e verificar o repositório e a branch;
2. ler integralmente os artefatos normativos e arquiteturais;
3. executar o baseline atual;
4. comparar o estado real com este manual e com `tasks/TASK-001.yaml`;
5. não reescrever a arquitetura já consolidada;
6. revisar a Definition of Ready da `TASK-001`;
7. resolver apenas questões que já tenham resposta nas fontes autorizadas;
8. reportar qualquer decisão humana ainda aberta;
9. após confirmação da prontidão, executar somente a `TASK-001`;
10. concluir testes, commit, push e handoff;
11. parar no gate de revisão independente;
12. aguardar a revisão do Claude e a autorização para promover a próxima task.

Este procedimento se repete para cada task. “Ir construindo” significa avançar de forma contínua dentro de uma task aprovada, não executar todas as tasks sem gates.

## 24 Bloco de ativação para copiar no Codex

```text
Adote o arquivo INTELLIX_CODEX_MASTER_IMPLEMENTATION_MANUAL.md como carta de execução do programa IntelliX Engineering Framework.

Trabalhe exclusivamente no repositório:
/Users/felipemaranhao/Documents/Codex/2026-09-16/referenced-chatgpt-conversation-this-is-an/work/intellix-plugin

Use exclusivamente a branch:
feat/intellix-multiagent-framework

Confirme que o commit 59d0d3e pertence ao histórico. Leia integralmente AGENTS.md, CLAUDE.md, README.md, intellix.md ou intellix.yaml, framework/, docs/architecture/, os ADRs aplicáveis e tasks/TASK-001.yaml.

Execute o baseline antes de alterar arquivos. Valide a Definition of Ready e o fileset da TASK-001. Se não existir conflito material ou decisão humana pendente, implemente somente a TASK-001 conforme seu contrato e o manual mestre. Use worktree dedicado porque a tarefa é de risco alto. Faça testes positivos e negativos, revise o diff, crie commit focado e envie apenas para a branch autorizada.

Não implemente TASK-002 a TASK-005. Não faça merge, deploy, release, alteração de permissões, acesso a produção ou uso de segredos. Não edite ~/.claude nem clones em cache ou marketplace. Pare diante de alteração local desconhecida, conflito normativo, fileset insuficiente, decisão arquitetural não aprovada ou ação irreversível.

Ao terminar, entregue o relatório obrigatório definido no manual e pare no gate de revisão independente do Claude.
```

## 25 Decisão de governança

Este manual autoriza o Codex a construir o framework de forma incremental, dentro dos Task Contracts aprovados e da branch definida. Ele não transforma o Codex em autoridade de produto, arquitetura, aprovação, merge ou produção.

A qualidade pretendida depende da combinação correta de responsabilidades: artefatos orientam, contratos limitam, Codex implementa, Claude revisa, CI comprova fatos e o humano decide mudanças de direção e ações irreversíveis. Essa separação deve permanecer visível no código, nos documentos e nos registros operacionais do framework.
