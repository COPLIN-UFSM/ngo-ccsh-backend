CREATE TABLE ORCAMENTO.EMAILS (
    id_email INTEGER NOT NULL PRIMARY KEY,
    id_pessoa INTEGER NOT NULL,
    email varchar(64) NOT NULL,
    ATIVO BOOLEAN NOT NULL
);

comment on table orcamento.emails is 'Armazena emails de pessoas na aplicação. Mantido independentemente do banco de dados institucional (SIE)';