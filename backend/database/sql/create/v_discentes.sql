create view orcamento.v_discentes as (
    select
        caa.ID_CURSO_ALUNO,
        caa.id_pessoa as ID_PESSOA_SIE,
        strip(MATRICULA) MATRICULA,
        caa.ID_CURSO,
        ANO_EVASAO is NULL as ATIVO
    from CURSOS_ALUNOS_ATZ caa
    inner join acad_cursos ac on caa.id_curso = ac.ID_CURSO
    inner join ACAD_NIVEL_CURSOS anc on ac.ID_NIVEL = anc.ID_NIVEL
);

comment on table orcamento.v_discentes is 'View criada a partir das tabelas CURSOS_ALUNOS_ATZ';