create view ORCAMENTO.V_CURSOS as (
    select
        ac.ID_CURSO,
        ac.ID_CENTRO AS ID_CENTRO_SIE,
        strip(ac.NOME_CURSO) NOME_CURSO,
        strip(anc.DESCRICAO) NIVEL_CURSO,
        strip(am.descricao) MODALIDADE_CURSO,
        strip(acla.descricao) CLASSIFICACAO_CURSO
    from bee.acad_cursos ac
    inner join bee.ACAD_NIVEL_CURSOS anc on ac.ID_NIVEL = anc.id_nivel
    inner join bee.ACAD_MODALIDADE am on ac.ID_MODALIDADE = am.ID_MODALIDADE
    inner join bee.ACAD_CLASSIFICACAO acla on ac.ID_CLASSIF = acla.ID_CLASSIF
);

comment on table ORCAMENTO.V_CURSOS is 'View criada a partir das tabelas do banco bee ACAD_CURSOS, ACAD_NIVEL_CURSOS, ACAD_MODALIDADE e ACAD_CLASSIFICACAO.';