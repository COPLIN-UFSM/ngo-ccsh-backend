create view ORCAMENTO.V_SITUACOES_UNIDADES as (
    select
        ITEM_TABELA ID_SITUACAO_UNIDADE,
        STRIP(DESCRICAO) SITUACAO_UNIDADE
    from bee.TAB_ESTRUTURADA
    where COD_TABELA = 105
    and ITEM_TABELA <> 0  -- remove linha "Selecione" do resultado
);
comment on table ORCAMENTO.V_SITUACOES_UNIDADES is 'Situação de unidade (criada a partir de BEE.TAB_ESTRUTURADA com COD_TABELA=105)';