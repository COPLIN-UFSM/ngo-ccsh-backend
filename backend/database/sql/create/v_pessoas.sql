create view orcamento.v_pessoas as (
    select
        pessoas.ID_PESSOA,
        strip(NOME_PESSOA) as NOME_PESSOA,
        upper(strip(doc_cpf.NUMERO_DOCUMENTO)) as CPF,
        upper(strip(doc_rg.NUMERO_DOCUMENTO)) as RG
    from PESSOAS
    inner join DOC_PESSOAS doc_cpf on pessoas.ID_PESSOA = doc_cpf.ID_PESSOA
    inner join DOC_PESSOAS doc_rg on pessoas.ID_PESSOA = doc_rg.ID_PESSOA
    where
        pessoas.NATUREZA_JURIDICA = 'F'
        and doc_cpf.ID_TDOC_PESSOA = 1 -- cpf
        and doc_rg.ID_TDOC_PESSOA = 3 -- rg
);

comment on table orcamento.v_pessoas is 'View criada a partir das tabelas GERAL_SERVIDORES_UFSM e CURSOS_ALUNOS_ATZ.';