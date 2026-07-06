create view ORCAMENTO.V_CENTROS_SIE as (
    select
        id_centro as ID_CENTRO_SIE,
        cod_estruturado,
        sigla_centro,
        strip(nome_centro) NOME_CENTRO
    from bee.NAV_CENTROS
    where ID_CENTRO not in (121, 2021) -- poli e ctism (antigos)
);

comment on table ORCAMENTO.V_CENTROS_SIE is 'Gerada a partir de bee.NAV_CENTROS';

