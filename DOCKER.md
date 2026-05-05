# Docker

## Sem docker-compose.yml

1. Construa a imagem com
   ```bash
   docker build -t ngo-ccsh-backend .
   ```

2. Rode o container com
   ```bash
   docker run -p 8000:8000 -e DB_USERNAME=USERNAME -e DB_PASSWORD="PASSWORD" -e DB_HOST=bi.proj.ufsm.br -e DB_PORT=50000 -e DB_DATABASE=bee -e DB_SCHEMA=ORCAMENTO ngo-ccsh-backend
   ```

   ou (versão dev)
   
   ```bash
   docker run -p 8000:8000 -e DJANGO_SETTINGS_MODULE=ngo_ccsh.dev_settings ngo-ccsh-backend
   ```

## Com docker-compose.yml

1. Crie um arquivo `.env` com as seguintes variáveis de ambiente (substituindo os valores de `DB_USERNAME` e `DB_PASSWORD`):
   ```
   DB_USERNAME=USERNAME
   DB_PASSWORD="PASSWORD"
   DB_HOST=bi.proj.ufsm.br
   DB_PORT=50000
   DB_DATABASE=bee
   DB_SCHEMA=ORCAMENTO
   ```

2. Execute com:
   ```bash
   docker compose up -d --build --remove-orphans
   ```