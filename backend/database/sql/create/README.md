# DDL do schema financeiro

Os arquivos desta pasta descrevem a criação do schema novo para um banco vazio.
Execute-os manualmente no Db2, na ordem abaixo, porque as tabelas têm chaves
estrangeiras entre si:

1. `centros.sql`, `unidades.sql`, `pessoas.sql`, `usuarios.sql`
2. `emails.sql`, `telefones.sql`
3. `naturezas.sql`, `grupos_finalidades.sql`, `tipos_documentos.sql`
4. `finalidades.sql`, `tipos_documentos_para_finalidades.sql`
5. `tipos_movimentos.sql`, `empenhos.sql`, `transacoes.sql`
6. `lancamentos.sql`, `valores_documentos.sql`, `exercicios_centros.sql`
7. `vinculos_bolsas.sql`, `parcelas_bolsas.sql`, `listas_siafi.sql`,
   `itens_listas_siafi.sql`
8. As cinco tabelas `despesas_historical*.sql`

Os arquivos não são um script de alteração para um banco existente. A conversão
de um schema legado em uso exige um plano `ALTER`/migração de dados revisado para
aquele banco; não execute estes `CREATE TABLE` sobre tabelas existentes. As views
`v_*` do SIE são dependências externas e não são criadas por estes DDLs.
