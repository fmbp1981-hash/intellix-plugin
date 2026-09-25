---
name: intellix-decision-layer
description: Avalia, por projeto de cliente, se decisões semânticas tipadas sobre texto justificam uma camada própria. Use quando houver classificação, triagem ou roteamento em volume, tempo de resposta crítico ou restrição de residência. Não use para geração, cálculo, decisão irreversível nem no workflow de desenvolvimento IntelliX.
---

# Camada de decisão tipada

Esta skill governa uma decisão de arquitetura por projeto. Ela não instala motor,
não cria adapter e não escolhe fornecedor. O resultado pode ser **adotar**,
**não adotar** ou **não aplicável**, sempre registrado no ADR do projeto.

## Limite de uso

- Aplica-se somente a sistemas de clientes.
- Nunca participa da aprovação, do risco, dos gates ou da conclusão do framework IntelliX.
- Nunca reduz alerta, risco, gate ou aprovação já exigidos.
- Qualquer proposta de uso no workflow IntelliX exige outro ADR.
- Não autoriza ação irreversível, financeira, de permissão ou de produção.

## Fonte canônica

Antes de avaliar, leia integralmente:

`global-config/skills/intellix-decision-layer/references/decision-layer.md`

Esse arquivo é normativo. Nomes, versões, preços, limites e alegações de
fornecedores ficam exclusivamente na referência informativa datada:

`global-config/skills/intellix-decision-layer/references/engines-2026-09.md`

Fatos informativos devem ser reverificados na data de uso e nunca substituem o
piloto do projeto.

## Fluxo

1. Identifique as decisões automatizadas sobre texto e suas consequências.
2. Esgote regras determinísticas antes de avaliar uma camada semântica.
3. Aplique os vetos e sinais do checklist normativo.
4. Registre no ADR do projeto `não aplicável`, `não adotado` ou `adotado`.
5. Se adotado, declare classe de risco, abstenção, fallback, residência e porta
   proporcional antes de qualquer código.
6. Exija piloto em sombra, calibração aprovada e cadeia segura de fallback antes
   do modo ativo.

## Saída mínima

```text
decisão: <nome>
resultado: não aplicável | não adotado | adotado
consequência concreta: <efeito de um erro>
classe: A | B | C | D | n/a
residência: <restrição documentada>
fallback: <cadeia permitida>
port: criar | não criar
motivo: <evidência do checklist>
gate humano: <quando obrigatório>
```

Se faltar evidência, registre a pendência. Não presuma compatibilidade entre
motores, não invente limiar e não transforme probabilidade em autorização.
