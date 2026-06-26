create view orcamento.v_tipos_unidades as (
    select ITEM_TABELA ID_TIPO_UNIDADE, DESCRICAO TIPO_UNIDADE
    from bee.TAB_ESTRUTURADA
    where COD_TABELA = 106
    and ITEM_TABELA <> 0
);

comment on table orcamento.v_tipos_unidades is 'Tipo de unidade (criada a partir de BEE.TAB_ESTRUTURADA com COD_TABELA=106)';