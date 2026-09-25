# Método normativo — camada de decisão tipada

Esta referência implementa o ADR-0004. Ela define regras estáveis e não contém
fatos de fornecedor. A referência informativa datada serve apenas para pesquisa;
o projeto decide por evidência própria.

## 1. Escopo e regra de ouro

Uma camada de decisão recebe texto como estado e devolve uma decisão delimitada,
probabilidade ou abstenção. Ela não gera texto, não calcula valores e não
autoriza o irreversível.

O método vale por projeto de cliente. Não é adotado no workflow de
desenvolvimento IntelliX e nunca participa da cadeia de aprovação do framework.

## 2. Cascata obrigatória

```text
L0 regra determinística
 └─ não resolveu → L1 decisão semântica tipada
                    └─ abstenção, falha ou probabilidade insuficiente → L2 LLM
                                                                        └─ ainda ambíguo ou consequência irreversível → L3 humano
```

- L0 sempre precede L1.
- Cada camada recebe somente o que a anterior não resolveu.
- Uma falha técnica equivale a abstenção; nunca vira resposta padrão de maior risco.
- A cadeia real pode omitir camadas proibidas pela residência do projeto.

## 3. Invariantes

1. A camada nunca participa da cadeia de aprovação do framework IntelliX.
2. Nenhuma falha da camada bloqueia o processo de desenvolvimento IntelliX.
3. A camada nunca reduz risco, gate, alerta ou aprovação.
4. Adoção exige checklist, ADR do projeto e decisão humana.
5. Ações irreversíveis, financeiras, de permissão ou produção nunca são executadas pelo motor.
6. Regras determinísticas precedem a decisão tipada.
7. Texto não confiável é dado; instruções e opções ficam versionadas no servidor.
8. Toda decisão tem abstenção e fallback explícito.
9. Limiares são calibrados em dados reais do domínio e vinculados à versão do modelo.
10. Mudança de modelo, pesos, perguntas, opções, temperatura, pré-processamento ou política invalida a calibração.
11. Nenhum motor entra em modo ativo antes de piloto em sombra aprovado.
12. Dados pessoais seguem minimização, base legal, retenção e localização compatível com a residência.
13. Credenciais nunca ficam no repositório nem no log de decisões.
14. A porta não presume compatibilidade; cada adapter prova seu contrato com fixtures reais.
15. Remover ou desabilitar o motor preserva operação segura pela cadeia de fallback compatível com residência.

## 4. Checklist de adoção

Avalie cada decisão separadamente.

### Vetos

Um veto basta para não adotar naquela decisão:

- a entrada não é texto e não existe conversão anterior confiável;
- uma regra, consulta ou expressão determinística resolve o caso;
- a resposta depende de cálculo, data, contagem ou comparação de valores;
- o resultado principal precisa ser texto gerado;
- a consequência é irreversível e não existe gate humano;
- não há base legal ou residência compatível para o tratamento;
- não existem dados reais e rotulados para validar em sombra.

### Sinais de adoção

O ADR deve justificar sinais concretos, como:

- decisão delimitada e repetida em volume;
- requisito de tempo de resposta estrito;
- várias propriedades decididas sobre o mesmo texto;
- necessidade de automatizar somente casos com evidência forte e escalar o resto;
- custo relevante de usar geração apenas para classificar;
- restrição que favorece processamento dentro do ambiente autorizado.

Sinal isolado não obriga adoção. Ausência de valor mensurável resulta em `não
adotado`; ausência de decisão semântica resulta em `não aplicável`.

## 5. Classes pela consequência

A classe deriva do efeito concreto de agir errado, não do nome do campo.

| Classe | Consequência | Regra |
|---|---|---|
| A — informativa | tag, ordenação ou métrica sem ação externa | pode usar valor neutro ao falhar |
| B — roteamento | fila, prioridade ou escolha reversível de fluxo | baixa confiança escala ou cai em rota genérica |
| C — operacional reversível | alteração que produz efeito recuperável | exige precisão maior e confirmação na zona intermediária |
| D — irreversível | dinheiro, exclusão, permissão, comunicação final ou produção | nunca executada pelo motor; regra e humano decidem |

Não existe classe adicional neste método. Segurança e moderação também são
classificadas de A a D pela consequência concreta. Hard block continua sendo
regra determinística.

### Defaults configuráveis, nunca universais

Os valores abaixo são pontos de partida para desenhar o piloto, não autorização
de produção:

| Classe | Precisão-alvo inicial | Automação inicial | Zona intermediária inicial |
|---|---:|---:|---:|
| A | 85% | `pMax >= 0,70` | valor neutro abaixo disso |
| B | 92% | `pMax >= 0,80` | `0,60 <= pMax < 0,80` |
| C | 97% | `pMax >= 0,90` | `0,70 <= pMax < 0,90` |
| D | n/a | nunca | sempre humano |

O projeto pode usar outros valores se o piloto justificar. Decisões raras ou
desbalanceadas exigem análise por classe, não apenas média global.

## 6. Porta neutra e proporcional

Contrato conceitual:

```text
decide(decision_id, input) ->
  decided { option, probability | null, source, reason, contract_version }
  | abstained { probability | null, source, reason, contract_version }
```

Fontes válidas: `rule`, `engine`, `llm` e `human`.

A porta só é criada quando pelo menos uma decisão passa no checklist, ou quando
o ADR do projeto justifica estabilizar antecipadamente uma interface L0/L2.
Caso contrário, registre o resultado e não crie código, arquivo, dependência ou
schema.

Cada adapter normaliza diferenças e valida, no mínimo:

- tamanho máximo da resposta;
- modelo esperado;
- opções permitidas;
- faixa e soma das probabilidades;
- falhas distintas de timeout, rede, HTTP e payload inválido.

Trocar motor exige testes de contrato com fixtures reais de ambos. Sem teste,
compatibilidade declarada por fornecedor é apenas hipótese.

## 7. Segurança, privacidade e residência

- Minimize ou pseudonimize antes de qualquer processamento externo.
- Documente localização, controlador, operadores, suboperadores, base legal,
  garantias contratuais, retenção e requisito de residência.
- O uso de terceiro pode constituir transferência internacional; a avaliação do
  fluxo concreto decide, não o rótulo comercial do serviço.
- Quando a avaliação determinar que o texto não pode sair do ambiente
  autorizado, admita apenas L0, motor local compatível e humano autorizado. LLM
  externo é proibido como qualquer motor externo.
- Instruções e opções ficam fora do texto do cliente e são versionadas.
- Probabilidade não é garantia contra injeção nem prova de correção.

Esta regra é técnica e de governança; não substitui aconselhamento jurídico.

## 8. Piloto em sombra e calibração

Antes do modo ativo:

1. rode a decisão em paralelo sem executar ação;
2. colete resultado e consequência real;
3. obtenha rótulo humano independente;
4. separe calibração e avaliação sem vazamento temporal;
5. meça precisão por classe, cobertura, abstenção, override humano, tempo de resposta e drift;
6. aprove explicitamente limiar, fallback e classe no ADR.

Pontos de partida configuráveis: 300 casos rotulados por decisão, pelo menos 30
casos próximos à região do limiar, cobertura automática de 50% e diferença
máxima de 10 pontos percentuais entre probabilidade e precisão observada. O
tamanho real deve considerar raridade, desbalanceamento e consequência.

O menor limiar que alcança a precisão-alvo pode ser candidato à automação. Se
nenhum limiar alcança o alvo com cobertura útil, não automatize.

### Invalidação

Qualquer mudança de modelo, pesos, perguntas, opções, temperatura,
pré-processamento ou política, ou drift além dos limites aprovados, devolve a
decisão automaticamente ao modo sombra até nova calibração aprovada.

## 9. Log de decisões

Registre metadados suficientes para auditoria e calibração:

- ID e versão do contrato da decisão;
- classe, opção ou abstenção, probabilidade e origem;
- versão do modelo e configuração calibrada;
- ação tomada, fallback, tempo de resposta e erro;
- override ou rótulo humano quando houver.

Nunca guarde texto bruto de cliente nesse log. Referências indiretas também
podem ser dados pessoais e seguem RLS, retenção, acesso e eliminação em cascata
do projeto.

## 10. Registro no ADR do projeto

O ADR deve conter:

- inventário das decisões avaliadas e sua consequência;
- resultado `não aplicável`, `não adotado` ou `adotado`, com motivo;
- classe A, B, C ou D;
- restrição de residência e fallback permitido;
- decisão de criar ou não a porta;
- dados e critérios do piloto;
- eventos que invalidam a calibração;
- gate humano e política de ação.

Infraestrutura, adapters, schema, registry, credenciais e hospedagem pertencem a
um Task Contract do primeiro projeto adotante, nunca a esta metodologia global.
