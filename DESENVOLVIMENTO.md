# Desenvolvimento

Esse capítulo explica como configurar o ambiente de desenvolvimento para a aplicação, e como rodar os testes.

## Configuração do ambiente

Para desenvolvimento, recomenda-se utilizar o gerenciador de pacotes [conda](https://docs.conda.io/en/latest/), 
e criar um ambiente virtual para a aplicação:

```bash
conda env create -f environment.yml
```

Depois é necessário ativar o ambiente de trabalho com `conda activate ngo` (sendo `ngo` o nome do ambiente criado, 
especificado no arquivo `environment.yml`).

## Rodando a aplicação em ambiente de desenvolvimento

Você pode rodá-la diretamente pela linha de comando com:

```bash
cd backend
conda activate ngo
python manage.py makemigrations --settings=ngo_ccsh.dev_settings
python manage.py migrate --settings=ngo_ccsh.dev_settings
python manage.py createsuperuser --settings=ngo_ccsh.dev_settings
python manage.py runserver --settings=ngo_ccsh.dev_settings
```

Ou então criar uma configuração no PyCharm, adicionando a variável de ambiente `DJANGO_SETTINGS_MODULE` com o valor 
`ngo_ccsh.dev_settings`:

[![Configuração do PyCharm](imagens/configuração_desenvolvimento.png)](imagens/configuração_desenvolvimento.png)

Teste a aplicação entrando na URL [http://localhost:8000/admin/](http://localhost:8000/admin/) e usando o usuário criado com o comando 
`createsuperuser`.

## Onde fazer commits

Para desenvolvimento, os commits devem ser feitos na branch `dev`. A branch `main` deve conter apenas código que já foi 
testado e validado e pode ser usado em produção.