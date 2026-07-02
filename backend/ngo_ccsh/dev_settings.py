"""
Script para desenvolvimento local com SQLite persistente em disco, sem alterar o banco de produção.
"""

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

# desativa configuração ativa apenas em produção
del FORCE_SCRIPT_NAME

# adiciona autenticação por sessão APENAS para o ambiente dev
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] += ["rest_framework.authentication.SessionAuthentication"]

# remove configurações do servidor de produção
STATIC_URL = "/static/"

DEBUG = True
