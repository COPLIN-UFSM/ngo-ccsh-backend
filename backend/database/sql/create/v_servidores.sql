create view orcamento.v_servidores as (
    select
        gsu.id_contrato_rh,
        gsu.id_pessoa,
        strip(MATR_EXTERNA) MATRICULA,
        gsu.ID_CARGO,
    CASE
        when DT_DESLIGAMENTO is NULL then TRUE
        when DT_DESLIGAMENTO > CURRENT_DATE then TRUE
        else FALSE
    END as ATIVO
    from GERAL_SERVIDORES_UFSM gsu
);

comment on table orcamento.v_servidores is 'View criada a partir das tabelas GERAL_SERVIDORES_UFSM';