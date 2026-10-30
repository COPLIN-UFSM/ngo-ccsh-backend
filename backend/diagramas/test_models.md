# Sequência do fluxo de validação de despesas

O comando `ngo_ccsh.management.commands.test_models` percorre a sequência abaixo
para validar os modelos e serviços de despesas. O cenário cria suas referências,
abre o exercício, lança crédito, empenho, distribuição e despesa, e fecha o ano
devolvendo os saldos restantes. Todas as operações são feitas dentro de uma única
transação, revertida ao final para não deixar dados de teste persistidos.

```mermaid
sequenceDiagram
    autonumber
    actor Operador
    participant Comando as test_models
    participant SIE as Views do SIE
    participant Servicos as Services de despesas
    participant Saldos as Consultas de saldo
    participant Banco as Banco de dados

    Operador->>Comando: Executa o comando
    Comando->>Banco: Inicia transaction.atomic()

    Comando->>SIE: Busca tipo e situação de unidade
    SIE-->>Comando: Retorna referências existentes
    Comando->>Banco: Cria pessoa, usuário, centro, unidade,<br/>natureza, finalidade e empenho

    Comando->>Banco: Cria exercício do ano corrente como aberto
    Banco-->>Comando: Exercício aberto

    Comando->>Servicos: creditar(centro, ano, natureza, 1.000,00)
    Servicos->>Banco: Registra crédito no razão
    Servicos->>Saldos: Consulta total e recurso livre
    Saldos-->>Servicos: Total 1.000,00; livre 1.000,00
    Servicos-->>Comando: Crédito registrado

    Comando->>Servicos: reforcar_empenho(empenho, 700,00)
    Servicos->>Banco: Registra reforço no razão
    Servicos->>Saldos: Consulta saldo do empenho e recurso livre
    Saldos-->>Servicos: Empenhado 700,00; livre 300,00
    Servicos-->>Comando: Reforço registrado

    Comando->>Servicos: distribuir(centro, unidade, 500,00)
    Servicos->>Banco: Registra distribuição no razão
    Servicos->>Saldos: Consulta saldo da unidade e não distribuído
    Saldos-->>Servicos: Unidade 500,00; não distribuído 500,00
    Servicos-->>Comando: Distribuição registrada

    Comando->>Servicos: registrar_despesa(empenho, unidade, 200,00)
    Servicos->>Banco: Registra despesa no razão
    Servicos->>Saldos: Consulta total, empenho e unidade
    Saldos-->>Servicos: Centro 800,00; empenho 500,00;<br/>unidade 300,00
    Servicos-->>Comando: Despesa registrada

    Note over Comando,Servicos: O fechamento destina cada saldo remanescente sem contar o mesmo recurso duas vezes.
    Comando->>Servicos: fechar_exercicio(centro, ano, destinos)
    Servicos->>Banco: Devolve 300,00 debitando empenho e unidade
    Servicos->>Banco: Devolve 200,00 debitando o restante do empenho
    Servicos->>Banco: Devolve 300,00 do saldo não empenhado do centro
    Servicos->>Saldos: Verifica pendências do exercício
    Saldos->>Banco: Consulta saldos e parcelas alocadas
    Banco-->>Saldos: Não há saldos nem parcelas pendentes
    Saldos-->>Servicos: Fechamento sem pendências
    Servicos->>Banco: Marca exercício como fechado e associa transação
    Servicos-->>Comando: Transação de fechamento

    Comando->>Banco: Marca a transação de teste para rollback
    Banco-->>Comando: Reverte dados e lançamentos criados
    Comando-->>Operador: Fluxo validado; banco sem alterações persistentes
```
