create view ORCAMENTO.V_CENTROS as (
    select id_centro, cod_estruturado, sigla_centro, nome_centro
    from bee.NAV_CENTROS
);

comment on table orcamento.V_CENTROS is 'Gerada a partir de bee.NAV_CENTROS';

