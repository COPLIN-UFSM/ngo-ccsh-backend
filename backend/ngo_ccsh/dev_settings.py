"""
Script para testes locais com SQLite persistente em disco, sem alterar o banco de produção.
"""

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

# # cria tabelas com managed = False, mas só se o banco ainda não existir
if not os.path.exists(DATABASES['default']['NAME']):
    print('[INFO] dev.sqlite3 não encontrado - criando tabelas do banco de dados')
    force_create_unmanaged_models()

# desativa configuração ativa apenas em produção
del FORCE_SCRIPT_NAME

# adiciona autenticação por sessão APENAS para o ambiente dev
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += ["rest_framework.authentication.SessionAuthentication"]

# remove configurações do servidor de produção
STATIC_URL = "/static/"

DEBUG = True
