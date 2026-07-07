CREATE TABLE ORCAMENTO.VALORES_DOCUMENTOS (
    ID_TIPO_DOCUMENTO INTEGER NOT NULL REFERENCES ORCAMENTO.TIPOS_DOCUMENTOS(ID_TIPO_DOCUMENTO),
    ID_VERSAO_TRANSACAO INTEGER NOT NULL REFERENCES ORCAMENTO.VERSOES_TRANSACOES(ID_VERSAO_TRANSACAO),
    VALOR VARCHAR(256) NOT NULL,
    PRIMARY KEY(ID_TIPO_DOCUMENTO, ID_VERSAO_TRANSACAO)
);

comment on table orcamento.valores_documentos is 'Tabela que armazena os valores dos documentos associados a transações específicas, permitindo o registro de informações adicionais relacionadas aos documentos.';