-- TODO errado! remodelar para usuários ser unique

create view orcamento.v_pessoas as (
    (
        select gsu.id_pessoa,
        strip(MATR_EXTERNA) MATRICULA,
        strip(NOME_FUNCIONARIO) NOME_PESSOA,
        'Servidor' as VINCULO,
        STRIP(rh.DESCR_CARGO) CARGO,
        upper(strip(doc_cpf.NUMERO_DOCUMENTO)) CPF,
        upper(strip(doc_rg.NUMERO_DOCUMENTO)) RG,
        CASE
            when DT_DESLIGAMENTO is NULL then TRUE
            when DT_DESLIGAMENTO > CURRENT_DATE then TRUE
            else FALSE
        END as ATIVO
        from GERAL_SERVIDORES_UFSM gsu
        inner join CARGOS_RH rh on gsu.id_cargo = rh.id_cargo
        inner join DOC_PESSOAS doc_cpf on gsu.ID_PESSOA = doc_cpf.ID_PESSOA
        inner join DOC_PESSOAS doc_rg on gsu.ID_PESSOA = doc_rg.ID_PESSOA
        where
            doc_cpf.ID_TDOC_PESSOA = 1 -- cpf
            and doc_rg.ID_TDOC_PESSOA = 3 -- rg
    ) union (
        select caa.id_pessoa,
            strip(MATRICULA) MATRICULA,
            strip(NOME_ALUNO) NOME_PESSOA,
            'Discente' as VINCULO,
            'Discente nível ' || strip(anc.DESCRICAO) || ' do curso ' || strip(ac.NOME_CURSO) as CARGO,
            upper(strip(doc_cpf.NUMERO_DOCUMENTO)) CPF,
            upper(strip(doc_rg.NUMERO_DOCUMENTO)) RG,
            ANO_EVASAO is NULL as ATIVO
        from CURSOS_ALUNOS_ATZ caa
        inner join DOC_PESSOAS doc_cpf on caa.ID_PESSOA = doc_cpf.ID_PESSOA
        inner join DOC_PESSOAS doc_rg on caa.ID_PESSOA = doc_rg.ID_PESSOA
        inner join acad_cursos ac on caa.id_curso = ac.ID_CURSO
        inner join ACAD_NIVEL_CURSOS anc on ac.ID_NIVEL = anc.ID_NIVEL
        where
           doc_cpf.ID_TDOC_PESSOA = 1 -- cpf
           and doc_rg.ID_TDOC_PESSOA = 3  -- rg
           and ac.ID_CLASSIF <> 3 -- apenas para vínculo dos alunos
    )
);

comment on table orcamento.v_pessoas is 'View criada a partir das tabelas GERAL_SERVIDORES_UFSM e CURSOS_ALUNOS_ATZ, com informações de pessoas (servidores e discentes)';