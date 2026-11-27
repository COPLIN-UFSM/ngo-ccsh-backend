create view orcamento.v_sie_emails as (
    select
        ID_PESSOA ID_PESSOA_SIE,
        ID_CONTA ID_EMAIL_SIE,
        strip(ENDERECO) as EMAIL
    from EMAIL_CONTAS_PESSOAIS
);

comment on table orcamento.v_sie_emails is 'E-mails disponíveis no SIE para pessoas cadastradas.';