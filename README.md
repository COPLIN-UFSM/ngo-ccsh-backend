# ngo-ccsh-backend

Backend em Django REST API do sistema de controle orçamentário do NGO CCSH.

## Sumário

* [Instalação](#instalação)
  * [Desenvolvimento](#desenvolvimento)
  * [Produção](#produção)
* [Executando testes](#executando-testes)
* [Estrutura do Projeto](#estrutura-do-projeto)
* [Contato](#contato)

## Instalação

Será necessário criar um ambiente virtual do Anaconda para executar a aplicação:

```bash
conda env create -f environment.yml
```

Após isso, existem duas maneiras de utilizar a aplicação: usando um banco de dados de desenvolvimento, e o banco de 
dados de produção.

### Desenvolvimento

O banco de dados de desenvolvimento é usado para fazer testes locais em um banco de dados SQLite persistente.

1. Delete os arquivos de migração (pasta `migrations`, uma para cada aplicação)
2. Execute os seguintes comandos (a partir da pasta [backend](backend)):
   ```bash
   python manage.py makemigrations --settings=ngo_ccsh.dev_settings
   python manage.py migrate --settings=ngo_ccsh.dev_settings
   python manage.py createsuperuser --settings=ngo_ccsh.dev_settings
   ```
3. Para executar a aplicação:
  ```bash
  python manage.py runserver --settings=ngo_ccsh.dev_settings
  ```

### Produção

O banco de dados de produção é o banco bee da UFSM; os dados dele são usados em painéis acadêmicos.

1. Delete os arquivos de migração (pasta `migrations`, uma para cada aplicação)
2. Execute os seguintes comandos (a partir da pasta [backend](backend)):
   ```bash
   python manage.py makemigrations ngo_ccsh 
   python manage.py migrate 
   python manage.py soft_reset
   ```
3. Para executar a aplicação:
   ```bash
   python manage.py runserver
   ```


## Executando testes

> [!CAUTION]
> Não use o banco de produção para executar os testes! As tabelas de produção podem ser removidas pelo código Django!

Os testes automatizados usando um banco de dados SQLite (ao invés do IBM DB2) para executar testes. As configurações
desse banco de dados estão no arquivo [test_settings.py](backend/ngo_ccsh/test_settings.py) (enquanto o arquivo usado para
produção é o [settings.py](backend/ngo_ccsh/settings.py)).

```bash
python manage.py test --settings=ngo_ccsh.test_setings 
```

Ou, se estiver executando pelo PyCharm, crie uma configuração como na tela abaixo:

![configuração_testes.png](imagens/configura%C3%A7%C3%A3o_testes.png)

## Estrutura do Projeto

O projeto do Django está na pasta `backend/`. 
O projeto possui três aplicativos:
* users: controle de **usuários** (adicionar usuários, promover a administradores, remover, etc)
* transactions: controle de **despesas**
* partials: controle de **lançamentos parciais**

## Contato

O repositório foi originalmente desenvolvido por Leandro Galbarino: [lonascimento@inf.ufsm.br]()

