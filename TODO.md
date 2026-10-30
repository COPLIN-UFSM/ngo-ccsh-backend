# TODO

Não há migração de banco legado a preparar: o projeto ainda está pré-deploy e não
existe uma base Db2 em uso.

## Antes do primeiro deploy

- Aplicar os DDLs em `backend/database/sql/create/` a um schema Db2 vazio de
  homologação e validar a sintaxe, as constraints, os índices e a compatibilidade
  com a versão de Db2 usada no ambiente de destino. Os scripts são manuais e não
  devem ser substituídos por migrations Django.
