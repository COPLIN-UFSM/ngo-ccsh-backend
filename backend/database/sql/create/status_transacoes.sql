CREATE TABLE ORCAMENTO.STATUS_TRANSACOES (
  id_status_transacao INTEGER NOT NULL PRIMARY KEY,
  status varchar(64) NOT NULL
);

COMMENT ON TABLE ORCAMENTO.STATUS_TRANSACOES IS 'Tabela que armazena os diferentes status possíveis para uma transação';