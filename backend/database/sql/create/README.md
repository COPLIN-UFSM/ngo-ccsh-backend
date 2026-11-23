# DDL do schema financeiro

Os arquivos desta pasta descrevem a criação do schema novo para um banco vazio.
Execute-os manualmente no Db2, na ordem numerada dos arquivos, pois as tabelas possuem relacionamentos entre si:

Os arquivos `*_v_sie_*.sql` criam as **views** do SIE (`v_sie_*`), alimentadas por dados do banco de dados 
institucional da UFSM.  

Os arquivos possuem apenas os comandos de criação de tabelas. Não execute estes `CREATE TABLE` sobre tabelas existentes.
