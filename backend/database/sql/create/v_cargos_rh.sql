create view orcamento.v_cargos_rh as (
    select
        ID_CARGO,
        strip(DESCR_CARGO) CARGO
    from bee.CARGOS_RH
);

comment on table orcamento.v_cargos_rh is 'View criada a partir de BEE.CARGOS_RH';