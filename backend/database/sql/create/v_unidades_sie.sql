create view orcamento.V_UNIDADES_SIE as (
    select
        ID_UNIDADE AS ID_UNIDADE_SIE,
        STRIP(NOME_UNIDADE) NOME_UNIDADE,
        COD_ESTRUTURADO,
        ID_CENTRO AS ID_CENTRO_SIE,
        TIPO_UNIDADE_ITEM ID_TIPO_UNIDADE,
        SITUACAO_ITEM ID_SITUACAO_UNIDADE
    from bee.NAV_UNIDADES
    where ID_CENTRO not in (121, 2021) -- poli e ctism (antigos e desativados)
);

comment on table orcamento.V_UNIDADES_SIE is 'Criada a partir de bee.nav_unidades.';