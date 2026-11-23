# Fluxo de validação do pagamento de bolsas

Resumo do cenário de `validar_pagamento_bolsas`. Toda bolsa tem parcelas mensais de
R$ 700. Uma parcela passa por três estados: **prevista** → **alocada** (reservada no
saldo da unidade) → **paga** (Lista SIAFI). Os dados de teste são revertidos ao final.

## Preparo

```mermaid
flowchart LR
    A["Centro recebe R$ 14700 no ano corrente"] --> B["Cria 4 empenhos: 8400, 4200, 1260 e 840"]
    B --> C["Distribui R$ 14700 para a unidade"]
```

## Caso 1: bolsa de 12 meses, um único ano fiscal

```mermaid
flowchart LR
    A["Bolsa jan a dez<br/>12 parcelas, todas no ano corrente"] --> B["Unidade tem saldo<br/>→ 12 parcelas alocadas"]
    B --> C["Uma Lista SIAFI por mês<br/>paga do empenho 1"]
    C --> D["Empenho 1 zerado"]
```

## Caso 2: bolsa de 12 meses, atravessa dois anos fiscais

```mermaid
flowchart TB
    A["Bolsa jul a jun<br/>6 parcelas no ano corrente + 6 no próximo"]
    A --> B["Ano corrente: 6 parcelas alocadas e pagas"]
    A --> C{"Próximo ano<br/>já tem orçamento?"}
    C -- "Não" --> D["Alocação recusada<br/>6 parcelas ficam PREVISTAS<br/>(compromisso futuro: R$ 4200)"]
    D --> E["Orçamento do próximo ano chega<br/>creditar, empenhar e distribuir"]
    E --> F["6 parcelas alocadas e pagas<br/>compromisso futuro zerado"]
```

## Caso 3: parcela paga com dois empenhos

Os empenhos têm finalidades diferentes, mas a mesma natureza.

```mermaid
flowchart LR
    P["Parcela mensal<br/>R$ 700 (monitoria)"] --> E3["Empenho 3<br/>finalidade monitoria<br/>R$ 420"]
    P --> E4["Empenho 4<br/>finalidade extensão<br/>R$ 280"]
    E3 --> L["Lista SIAFI do mês<br/>(divisão soma R$ 700)"]
    E4 --> L
```

Se a divisão não somar o valor da parcela, o pagamento é recusado.

## Resultado esperado

| Caso | Resultado |
|------|-----------|
| 1 | 12 parcelas pagas; empenho 1 zerado |
| 2 | Sem orçamento no próximo ano, 6 parcelas ficam previstas; depois do orçamento são pagas |
| 3 | 3 parcelas pagas, cada uma 420 + 280; empenhos 3 e 4 zerados |
| Final | Saldo da unidade e do centro zerados no ano corrente |
