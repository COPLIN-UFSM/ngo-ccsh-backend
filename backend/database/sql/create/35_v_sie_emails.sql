create view orcamento.v_sie_emails as (
    select
        serv.ID_PESSOA ID_PESSOA_SIE,
        end.ID_ENDERECO ID_EMAIL_SIE,
        strip(lower(end.DESCR_MAIL)) EMAIL
    from ISERV_GERAL serv
    left join ENDERECOS end on end.ID_ORIGEM = serv.ID_PESSOA and end.TIPO_ORIGEM_ITEM = 2
);

comment on table orcamento.v_sie_emails is 'E-mails disponíveis no SIE para pessoas cadastradas.';