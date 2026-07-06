create view orcamento.V_UNIDADES as (
    select ID_UNIDADE, STRIP(NOME_UNIDADE) NOME_UNIDADE, COD_ESTRUTURADO, ID_CENTRO, TIPO_UNIDADE_ITEM ID_TIPO_UNIDADE, SITUACAO_ITEM ID_SITUACAO_UNIDADE
    from bee.NAV_UNIDADES
    where ID_CENTRO not in (121, 2021) -- poli e ctism (antigos)
);
comment on table orcamento.V_UNIDADES is 'Criada a partir de bee.nav_unidades.';