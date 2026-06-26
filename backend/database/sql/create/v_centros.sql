create view V_CENTROS as (
    select id_centro, cod_estruturado, sigla_centro, strip(nome_centro) NOME_CENTRO
    from bee.NAV_CENTROS
    where ID_CENTRO not in (121, 2021) -- poli e ctism (antigos)
);

comment on table V_CENTROS is 'Gerada a partir de bee.NAV_CENTROS';

