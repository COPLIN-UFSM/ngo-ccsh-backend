1. Construa a imagem com
   ```bash
   docker build -t ngo-ccsh-backend .
   ```

2. Rode o container com
   ```bash
   docker run -p 8000:8000 -e DB_USERNAME=USERNAME -e DB_PASSWORD="PASSWORD" -e DB_HOST=bi.proj.ufsm.br -e DB_PORT=50000 -e DB_DATABASE=bee -e DB_SCHEMA=ORCAMENTO ngo-ccsh-backend
   ```
