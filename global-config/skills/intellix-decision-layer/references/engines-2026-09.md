# Motores avaliados — referência informativa de 2026-09

**Natureza:** informativa, não normativa.
**Verificação:** 2026-09-24.
**Regra:** reverificar tudo na data de uso. Alegação de fornecedor ou autor não
é evidência de produção; somente o piloto do projeto decide adoção.

Este documento não ordena, recomenda nem escolhe motor. Ele registra opções que
motivaram o ADR-0004 e diferenças que um projeto pode precisar testar.

## Laya

| Fato datado | Classificação da fonte |
|---|---|
| Pesos sob Apache 2.0 e execução na infraestrutura escolhida pelo projeto | documentação/model card oficial |
| Pacote PyPI `laya` 0.3.20 publicado em 2026-09-24; Python 3.10+ | registro oficial do PyPI |
| Checkpoints em inglês, multilíngue e decisões tipadas; contextos e parâmetros variam por checkpoint | model card oficial |
| O checkpoint multilíngue declara suporte a mais de 100 idiomas e até 8.192 tokens quando configurado; não há garantia específica de qualidade em português | alegação do autor no model card |
| O servidor declara compatibilidade de request/response com `POST /v1/systemone` | alegação do autor; exige teste de contrato |
| Benchmarks, calibração e latência publicados no model card foram produzidos pelo autor, em hardware e conjuntos específicos | alegação do autor; não é SLA nem prova para o projeto |
| O ajuste fino com dados do domínio é suportado e altera a calibração | documentação oficial; exige novo piloto |

Riscos a reverificar: maturidade recente, qualidade no idioma e domínio reais,
memória e hardware, segurança do serviço local, origem e hash dos pesos,
manutenção operacional e mudança rápida do pacote.

## Jev

| Fato datado | Classificação da fonte |
|---|---|
| Modelo versionado documentado: `jev-1.13.0`; aliases móveis apontavam para essa versão na data | documentação oficial |
| Endpoint: `POST https://api.typesafe.ai/v1/systemone` | documentação oficial |
| Primitivas documentadas: `noul`, `choice` e `score`; `choice` aceita até 255 opções e `score` até 10 níveis | documentação oficial |
| Contexto documentado: 64 mil tokens por requisição e 32 mil para estado mais a pergunta mais longa | documentação oficial |
| Preço documentado: US$ 0,042 por milhão de tokens de entrada; saída sem cobrança | documentação oficial; reverificar antes de estimar custo |
| Inglês é o idioma primário; outros idiomas são aceitos, mas a documentação manda testar no conteúdo real | documentação oficial |
| O fornecedor declara não treinar com requests/responses; oferece DPA e zero data retention para clientes enterprise | documentação oficial/legal; confirmar contrato aplicável |
| `confidence` deriva da distribuição; o projeto deve calibrar sua própria política | documentação oficial; não é probabilidade garantida de acerto |

Riscos a reverificar: residência e suboperadores, contrato/DPA e retenção do plano,
dependência do serviço, limites e preço, comportamento da versão fixada e
qualidade em português e no domínio real.

## Comparação não prescritiva

| Dimensão a testar | Alternativa self-hosted | API hospedada |
|---|---|---|
| residência | pode permanecer no ambiente autorizado, conforme implantação | depende do fluxo e contrato do fornecedor |
| operação | projeto assume runtime, disponibilidade e atualizações | fornecedor assume a operação do endpoint |
| adaptação | pode permitir ajuste de pesos | configuração ocorre por request |
| contexto e cardinalidade | variam por checkpoint e configuração | limites publicados pelo endpoint |
| custo | infraestrutura, operação e rotulagem | consumo segundo preço vigente |

Nenhuma linha escolhe automaticamente uma alternativa. O ADR do projeto deve
considerar residência, operação, fixtures reais, piloto em sombra e custo total.

## Fontes oficiais consultadas

Laya:

- https://huggingface.co/convaiinnovations/laya
- https://huggingface.co/convaiinnovations/laya-multilingual
- https://huggingface.co/convaiinnovations/laya-typed-decisions
- https://pypi.org/project/laya/

Jev/TypeSafe:

- https://docs.typesafe.ai/models.md
- https://docs.typesafe.ai/api.md
- https://docs.typesafe.ai/confidence.md
- https://docs.typesafe.ai/legal.md

URLs, versões e números acima pertencem somente a esta referência informativa.
