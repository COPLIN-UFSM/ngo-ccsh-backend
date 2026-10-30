# TODO

## Migração do Db2 existente

- Preparar e revisar um plano de migração do schema legado em uso, com DDLs `ALTER`
  e conversão dos dados para os modelos novos. Os scripts em
  `backend/database/sql/create/` criam um schema vazio e não devem ser executados
  sobre tabelas existentes. Validar o plano com uma cópia representativa do banco
  antes da aplicação.
  * comentário do programador chefe: não existe banco de dados legado. Nada precisa
    ser feito, estamos em uma versão pré-deploy.

## API de bolsas e fechamento de exercício

- Definir contratos e implementar endpoints para vínculos e parcelas de bolsa,
  incluindo geração, alocação e cancelamento de parcelas.
- Definir contratos e implementar endpoints para criar e gerenciar Listas SIAFI,
  incluir parcelas e confirmar pagamentos.
- Definir contratos e implementar endpoints para consultar pendências, fechar e
  reabrir exercícios fiscais.
- Cobrir as novas rotas com testes de API, além dos testes de serviços que já
  validam as regras de negócio.
