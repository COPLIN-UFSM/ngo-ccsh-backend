create view orcamento.v_sie_telefones as (
    select
        serv.ID_PESSOA ID_PESSOA_SIE,
        end.ID_ENDERECO ID_TELEFONE_SIE,
        strip(lower(REGEXP_REPLACE(FONE_RESIDENCIAL, '[^0-9]', ''))) TELEFONE
    from ISERV_GERAL serv
    left join ENDERECOS end on end.ID_ORIGEM = serv.ID_PESSOA and end.TIPO_ORIGEM_ITEM = 2
    where end.FONE_RESIDENCIAL is not null
    and length(strip(end.FONE_RESIDENCIAL)) > 0
union
    select
        serv.ID_PESSOA ID_PESSOA_SIE,
        end.ID_ENDERECO ID_TELEFONE_SIE,
        strip(lower(REGEXP_REPLACE(fone_celular, '[^0-9]', ''))) TELEFONE
    from ISERV_GERAL serv
    left join ENDERECOS end on end.ID_ORIGEM = serv.ID_PESSOA and end.TIPO_ORIGEM_ITEM = 2
    where end.fone_celular is not null
    and length(strip(end.FONE_CELULAR)) > 0
);

comment on table orcamento.v_sie_telefones is 'Telefones disponíveis no SIE para pessoas cadastradas.';




