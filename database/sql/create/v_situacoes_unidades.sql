create view orcamento.v_situacoes_unidades as (
    select ITEM_TABELA ID_SITUACAO_UNIDADE, DESCRICAO SITUACAO_UNIDADE
    from bee.TAB_ESTRUTURADA
    where COD_TABELA = 105
    and ITEM_TABELA <> 0
);

comment on table orcamento.v_situacoes_unidades is 'Situação de unidade (criada a partir de BEE.TAB_ESTRUTURADA com COD_TABELA=105)';
