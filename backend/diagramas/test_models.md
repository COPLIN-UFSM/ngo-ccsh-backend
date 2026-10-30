# Fluxo de validação de despesas

Este diagrama resume, em alto nível, quais entidades participam do cenário de
`test_models` e como os saldos mudam ao longo do exercício. Os valores representam
uma única natureza de recurso. O cenário termina com o exercício fechado e todos
os dados de teste revertidos.

```mermaid
flowchart TD
    Inicio([Início do teste])

    subgraph Preparacao["Entidades usadas no cenário"]
        ReferenciasSIE["Referências do SIE<br/>Tipo e situação da unidade"]
        PessoaUsuario["Pessoa + Usuário<br/>Responsável pelas operações"]
        CentroNatureza["Centro + Natureza<br/>Origem e classificação do recurso"]
        UnidadeFinalidade["Unidade + Finalidade<br/>Destino e classificação da despesa"]
        Empenho["Empenho<br/>Reserva recursos do centro"]
        Exercicio["Exercício do centro<br/>Aberto para o ano corrente"]
    end

    Inicio --> ReferenciasSIE
    Inicio --> PessoaUsuario
    Inicio --> CentroNatureza
    ReferenciasSIE --> UnidadeFinalidade
    CentroNatureza --> UnidadeFinalidade
    CentroNatureza --> Empenho
    CentroNatureza --> Exercicio

    subgraph Movimentacoes["Movimentações e saldos"]
        Credito["Crédito recebido<br/>Total do centro: R$ 1.000<br/>Livre no centro: R$ 1.000<br/>Empenho: R$ 0 · Unidade: R$ 0"]
        Reforco["Reserva no empenho<br/>Total do centro: R$ 1.000<br/>Livre no centro: R$ 300<br/>Empenho: R$ 700 · Unidade: R$ 0"]
        Distribuicao["Distribuição para a unidade<br/>Total do centro: R$ 1.000<br/>Livre no centro: R$ 300<br/>Empenho: R$ 700 · Unidade: R$ 500"]
        Despesa["Despesa paga pela unidade<br/>Total do centro: R$ 800<br/>Livre no centro: R$ 300<br/>Empenho: R$ 500 · Unidade: R$ 300"]
    end

    Exercicio --> Credito
    PessoaUsuario --> Credito
    Credito --> Reforco
    Empenho --> Reforco
    Reforco --> Distribuicao
    UnidadeFinalidade --> Distribuicao
    Distribuicao --> Despesa
    Empenho --> Despesa
    UnidadeFinalidade --> Despesa

    Razao["Transações e lançamentos<br/>Registram todas as movimentações"]
    Credito -.-> Razao
    Reforco -.-> Razao
    Distribuicao -.-> Razao
    Despesa -.-> Razao
    PessoaUsuario -.-> Razao

    subgraph Encerramento["Fechamento do exercício"]
        DevolucaoDupla["Devolver R$ 300<br/>Debita empenho e unidade"]
        DevolucaoEmpenho["Devolver R$ 200<br/>Zera o restante do empenho"]
        DevolucaoCentro["Devolver R$ 300<br/>Zera o recurso não empenhado"]
        Fechado["Exercício fechado<br/>Centro: R$ 0 · Empenho: R$ 0<br/>Unidade: R$ 0"]
    end

    Despesa --> DevolucaoDupla
    DevolucaoDupla --> DevolucaoEmpenho
    DevolucaoEmpenho --> DevolucaoCentro
    DevolucaoCentro --> Fechado
    Fechado -.-> Razao
    Fechado --> Rollback["Rollback da transação de teste<br/>Nenhum dado permanece gravado"]
    Rollback --> Fim([Fim])

    classDef entidade fill:#eaf2f8,stroke:#2874a6,color:#17202a
    classDef saldo fill:#e8f8f5,stroke:#148f77,color:#17202a
    classDef movimento fill:#fcf3cf,stroke:#b7950b,color:#17202a
    class PessoaUsuario,CentroNatureza,UnidadeFinalidade,Empenho,Exercicio,ReferenciasSIE entidade
    class Credito,Reforco,Distribuicao,Despesa,Fechado saldo
    class DevolucaoDupla,DevolucaoEmpenho,DevolucaoCentro,Razao movimento
```

O total do centro, o saldo do empenho e o saldo da unidade são dimensões diferentes
do mesmo razão. Por isso, no fechamento, R$ 300 são devolvidos debitando empenho e
unidade juntos; depois são devolvidos separadamente os R$ 200 restantes do empenho
e os R$ 300 que não foram empenhados.
