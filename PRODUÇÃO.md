# Produção

Esse arquivo descreve os passos que devem ser realizados para colocar em produção este servidor.

## Actions Runner e Docker Engine

> [!NOTE]
> Ignore esta seção caso o servidor de produção já possua um Action Runner do GitHub e uma engine do Docker.

No servidor de produção, crie um action runner e execute-o. Instruções na documentação do GitHub
Actions: https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners

O servidor de produção também deve estar rodando um Docker Engine: https://docs.docker.com/engine/install/

## Adicione segredos e variáveis no repositório

### Segredos

Acesse https://github.com/COPLIN-UFSM/ngo-ccsh-backend/settings/secrets/actions e adicione os seguintes 
segredos no nível de repositório:

* **DB_HOST:** URL onde o banco de dados está hospedado;
* **DB_DATABASE:** nome do banco de dados;
* **DB_SCHEMA:** schema a ser utilizada;
* **DB_PORT:** porta de acesso;
* **DB_USERNAME:** nome do usuário para acesso;
* **DB_PASSWORD:** senha de acesso;
* **DEPLOY_SERVER_REPO_PATH:** caminho onde o código-fonte deste repositório será armazenado no servidor de produção;
* **DJANGO_SECRET_KEY:** uma chave que invalida os logins quando é trocada (troque-a quando houver atualizações grandes);
* **JWT_SIGNING_KEY:** mesma coisa de `DJANGO_SECRET_KEY`;
* **EMAIL_HOST_PASSWORD:** senha do endereço de e-mail utilizado para enviar e-mails de recuperação e relatórios.

### Variáveis

Acesse https://github.com/COPLIN-UFSM/ngo-ccsh-backend/settings/variables/actions e adicione as 
seguintes variáveis no nível de repositório:

* **EMAIL_HOST_USER:** endereço de e-mail da conta que enviará os e-mails de recuperação; 
* **DEFAULT_FROM_EMAIL:** nome por extenso da conta de e-mail;
* **APP_FULL_NAME:** nome por extenso da aplicação;
* **APP_SHORT_NAME:** nome curto da aplicação;
* **FRONTEND_URL:** endereço URL de onde o frontend está hospedado;
* **SCRIPT_PREFIX:** subdiretório no servidor de produção onde o backend está hospedado (por exemplo, 
  `/ngo-ccsh-backend`).

> [!NOTE]
> Confira [.env.example](.env.example) para exemplos de valores.

>[!IMPORTANT]
> O `EMAIL_HOST_PASSWORD` deve ser obtido a partir 
> do [painel de controle de segurança do Google](https://myaccount.google.com/u/0/apppasswords), 
> criando uma **senha de App** para o email.

## Clone o repositório

Entre no servidor de produção e clone este repositório:

```bash
git clone https://github.com/COPLIN-UFSM/ngo-ccsh-backend.git
```

> [!IMPORTANT]
> O caminho onde o repositório será criado deve ser o mesmo de `DEPLOY_SERVER_REPO_PATH`!

## Monte a imagem com Docker

Dentro da pasta do repositório:

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

### Nginx

Configure também o roteamento do nginx no servidor no arquivo `/etc/nginx/sites-available/default` 
(ou outro arquivo de configuração do nginx):

```text
location /ngo-ccsh-backend/ {
     proxy_pass          http://127.0.0.1:8001/;
     proxy_set_header    Host                 $host;
     proxy_set_header    X-Real-IP            $remote_addr;
     proxy_set_header    X-Forwarded-For      $proxy_add_x_forwarded_for;
     proxy_set_header    X-Forwarded-Proto    $scheme;
}
```

Após modificar o arquivo, reinicie o nginx com:

```bash
sudo systemctl restart nginx
```


> [!IMPORTANT]
> A localização do backend deve ser a mesma da variável `SCRIPT_PREFIX`!

> [!IMPORTANT]
> A localização do frontend deve ser a mesma da variável `FRONTEND_URL`!