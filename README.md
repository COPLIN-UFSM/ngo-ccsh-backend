# ngo-ccsh-backend

Backend em Django REST API do sistema de controle orçamentário do NGO CCSH.

## Sumário

* [Instalação](#instalação)
* [Instruções de uso](#instruções-de-uso)
* [Estrutura do projeto](#estrutura-do-projeto)
* [Contato](#contato)


## Instalação

Crie um novo ambiente virtual com os seguintes comandos (a partir da linha de comando):

```bash
conda env create -f environment.yml
conda activate ngo
```

## Instruções de Uso

```bash
conda activate ngo
cd backend
python manage.py runserver
```

## Estrutura do Projeto

O projeto do Django está na pasta `backend/`. 
O projeto possui três aplicativos:
* users: controle de **usuários** (adicionar usuários, promover a administradores, remover, etc)
* transactions: controle de **despesas**
* partials: controle de **lançamentos parciais**

## Contato

O repositório foi originalmente desenvolvido por Leandro Galbarino: [lonascimento@inf.ufsm.br]()

