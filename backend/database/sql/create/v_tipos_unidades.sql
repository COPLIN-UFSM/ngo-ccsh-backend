create view V_TIPOS_UNIDADES as (
    select ITEM_TABELA ID_TIPO_UNIDADE, STRIP(DESCRICAO) TIPO_UNIDADE
    from bee.TAB_ESTRUTURADA
    where COD_TABELA = 106
    and ITEM_TABELA <> 0
);
comment on table V_TIPOS_UNIDADES is 'Tipo de unidade (criada a partir de BEE.TAB_ESTRUTURADA com COD_TABELA=106)';