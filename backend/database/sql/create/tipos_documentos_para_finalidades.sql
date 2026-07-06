CREATE TABLE orcamento.tipos_documentos_para_finalidades (
    ID_TIPO_DOCUMENTO_PARA_FINALIDADE INTEGER NOT NULL PRIMARY KEY,
    ID_TIPO_DOCUMENTO INTEGER NOT NULL REFERENCES orcamento.tipos_documentos(ID_TIPO_DOCUMENTO),
    ID_FINALIDADE INTEGER NOT NULL REFERENCES orcamento.finalidades(ID_FINALIDADE),
    OBRIGATORIO BOOLEAN NOT NULL DEFAULT FALSE
);

comment on table orcamento.tipos_documentos_para_finalidades is 'Tabela que relaciona os tipos de documentos com as finalidades, indicando se o documento é obrigatório para a finalidade específica.';