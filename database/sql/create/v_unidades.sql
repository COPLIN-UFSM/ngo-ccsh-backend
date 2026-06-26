create view orcamento.v_unidades as (
    select ID_UNIDADE, NOME_UNIDADE, COD_ESTRUTURADO, ID_CENTRO, TIPO_UNIDADE_ITEM ID_TIPO_UNIDADE, SITUACAO_ITEM ID_SITUACAO_UNIDADE
    from bee.NAV_UNIDADES
);

comment on table orcamento.v_unidades is 'Criada a partir de bee.nav_unidades.';

