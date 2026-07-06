CREATE TABLE ORCAMENTO.TRANSACOES (
    id_transacao INTEGER NOT NULL PRIMARY KEY,
    ID_VERSAO_TRANSACAO INTEGER NOT NULL REFERENCES ORCAMENTO.VERSOES_TRANSACOES (ID_VERSAO_TRANSACAO),
    DATA_CRIACAO timestamp not null
);

COMMENT ON TABLE ORCAMENTO.TRANSACOES is 'Uma transação é uma operação de crédito, débito ou transferência. Pode possuir várias versões, dependendo das modificações feitas em seus campos (nenhuma transação é deletada).';
