# Docker

Para executar um container em modo de desenvolvimento localmente, rode os seguintes comandos:
   
```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d
```

Isso executará o backend e exporá na porta `8001`: [http://localhost:8001/](http://localhost:8001/)

Depois, com o container rodando, crie o super usuário:

```bash
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```