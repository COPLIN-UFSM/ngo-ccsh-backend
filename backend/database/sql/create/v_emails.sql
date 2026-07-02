CREATE VIEW ORCAMENTO.V_EMAILS AS (
    select
        ID_CONTA,
        id_pessoa,
        strip(endereco) as EMAIL,
        IND_SITUACAO = 'A' ATIVO
    from EMAIL_CONTAS_PESSOAIS
);

COMMENT ON TABLE ORCAMENTO.V_EMAILS IS 'View criada a partir de BEE.EMAIL_CONTAS_PESSOAIS';