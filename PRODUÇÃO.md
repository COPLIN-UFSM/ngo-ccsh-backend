# Produção

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
DEBUG = False
APP_FULL_NAME = "Sistema de Gerenciamento de Gastos Acadêmicos da UFSM"
APP_SHORT_NAME = "SIGGA"
FRONTEND_URL = "https://proplan.ufsm.br/ngo-ccsh"
EMAIL_HOST_USER = "orcamento.ccsh@ufsm.br"
EMAIL_HOST_PASSWORD = "aaaa bbbb cccc dddd"
DEFAULT_FROM_EMAIL = "Núcleo de Gestão Orçamentária <orcamento.ccsh@ufsm.br>"
DJANGO_SECRET_KEY = "alguma_string_com_pelo_menos_32_caracteres"
JWT_SIGNING_KEY = "alguma_OUTRA_string_com_pelo_menos_32_caracteres"
SCRIPT_PREFIX="/ngo-ccsh-backend"
DB_USERNAME="<USERNAME>"
DB_PASSWORD="<PASSWORD>"
DB_HOST="<HOST>"
DB_PORT=50000
DB_DATABASE="<DATABASE>"
DB_SCHEMA="<SCHEMA>"
```

Substitua `<USERNAME>`, `<PASSWORD>`, `<HOST>´, `<DATABASE>` e `<SCHEMA>` pelos valores pertinentes.

O `EMAIL_HOST_PASSWORD` deve ser obtido a partir
do [painel de controle de segurança do Google](https://myaccount.google.com/u/0/apppasswords), criando uma **senha de App** 
para o email.

### Nginx

Configure também o roteamento do nginx no servidor:

```text
location /ngo-ccsh-backend/ {
     proxy_pass          http://127.0.0.1:8001/;
     proxy_set_header    Host                 $host;
     proxy_set_header    X-Real-IP            $remote_addr;
     proxy_set_header    X-Forwarded-For      $proxy_add_x_forwarded_for;
     proxy_set_header    X-Forwarded-Proto    $scheme;
}

location /ngo-ccsh/ {
     proxy_pass          http://127.0.0.1:8002/;
     proxy_set_header    Host                 $host;
     proxy_set_header    X-Real-IP            $remote_addr;
     proxy_set_header    X-Forwarded-For      $proxy_add_x_forwarded_for;
     proxy_set_header    X-Forwarded-Proto    $scheme;
}
```