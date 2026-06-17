# Desenvolvimento

Esse capítulo explica como configurar o ambiente de desenvolvimento para a aplicação, e como rodar os testes.

## Sumário

* [Onde fazer commits](#onde-fazer-commits)
* [Sem Docker](#sem-docker)
* [Com Docker](#com-docker)

## git

Entre no servidor onde o serviço será hospedado e clone o repositório:

```bash
git clone https://github.com/COPLIN-UFSM/ngo-ccsh-backend.git
```

Após isso, entre na pasta com `cd ngo-ccsh-backend`. 

## Docker

Monte o container:

```bash
docker compose build
      
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py collectstatic --noinput

docker compose up -d
```

Isso executará o backend e exporá na porta `8001`: [http://localhost:8001/](http://localhost:8001/)

Depois, com o container rodando, crie o super usuário:

```bash
docker compose -f docker-compose.yml exec web python manage.py createsuperuser
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, e adicione as seguintes variáveis de ambiente:

```python
DEBUG=True
APP_FULL_NAME="Sistema de Gerenciamento de Gastos Acadêmicos da UFSM"
APP_SHORT_NAME="SIGGA"
FRONTEND_URL="https://proplan.ufsm.br/ngo-ccsh"
EMAIL_HOST_USER="orcamento.ccsh@ufsm.br"
EMAIL_HOST_PASSWORD="aaaa bbbb cccc dddd"
DEFAULT_FROM_EMAIL="Núcleo de Gestão Orçamentária <orcamento.ccsh@ufsm.br>"
```

O `EMAIL_HOST_PASSWORD` deve ser obtido a partir
do [painel de controle de segurança do Google](https://myaccount.google.com/u/0/apppasswords), criando uma **senha de App** 
para o email.