CREATE TABLE ORCAMENTO.TIPOS_DOCUMENTOS (
    id_tipo_documento INTEGER NOT NULL PRIMARY KEY,
    tipo_documento varchar(128) NOT NULL,
    ATIVO BOOLEAN DEFAULT TRUE
);

comment on table orcamento.tipos_documentos is 'Tipos de documentos inseridos em uma transação (e.g. cpf, rg)';