CREATE TABLE ORCAMENTO.VALORES_DOCUMENTOS (
    ID_VALOR_DOCUMENTO INTEGER NOT NULL PRIMARY KEY,
    ID_TIPO_DOCUMENTO INTEGER NOT NULL REFERENCES ORCAMENTO.TIPOS_DOCUMENTOS(ID_TIPO_DOCUMENTO),
    ID_TRANSACAO INTEGER NOT NULL REFERENCES ORCAMENTO.TRANSACOES(ID_TRANSACAO),
    VALOR VARCHAR(256) NOT NULL
);

comment on table orcamento.valores_documentos is 'Tabela que armazena os valores dos documentos associados a transações específicas, permitindo o registro de informações adicionais relacionadas aos documentos.';