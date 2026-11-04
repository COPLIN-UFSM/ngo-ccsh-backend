create view ORCAMENTO.V_SIE_CENTROS as (
    select
        id_centro as ID_CENTRO_SIE,
        cod_estruturado,
        sigla_centro,
        strip(nome_centro) NOME_CENTRO
    from bee.NAV_CENTROS
    where ID_CENTRO not in (121, 2021) -- poli e ctism (antigos)
);

comment on table ORCAMENTO.V_SIE_CENTROS is 'Gerada a partir de bee.NAV_CENTROS';

