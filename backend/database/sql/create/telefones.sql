CREATE TABLE ORCAMENTO.TELEFONES (
    id_telefone INTEGER NOT NULL PRIMARY KEY,
    id_pessoa INTEGER NOT NULL,
    telefone varchar(16) NOT NULL,
    ATIVO BOOLEAN NOT NULL
);

comment on table orcamento.telefones is 'Armazena telefones de pessoas na aplicação. Mantido independentemente do banco de dados institucional (SIE)';