create view V_UNIDADES as (
    select ID_UNIDADE, STRIP(NOME_UNIDADE) NOME_UNIDADE, COD_ESTRUTURADO, ID_CENTRO, TIPO_UNIDADE_ITEM ID_TIPO_UNIDADE, SITUACAO_ITEM ID_SITUACAO_UNIDADE
    from bee.NAV_UNIDADES
    where SITUACAO_ITEM not in (3, 4) -- extinta e desativada
);
comment on table V_UNIDADES is 'Criada a partir de bee.nav_unidades.';