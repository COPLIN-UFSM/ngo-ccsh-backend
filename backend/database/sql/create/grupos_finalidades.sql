CREATE TABLE ORCAMENTO.GRUPOS_FINALIDADES (
    id_grupo_finalidade INTEGER NOT NULL PRIMARY KEY,
    grupo_finalidade varchar(256) NOT NULL,
    ATIVO BOOLEAN DEFAULT TRUE
);

comment on table orcamento.grupos_finalidades is 'Grupos de finalidades orçamentárias';