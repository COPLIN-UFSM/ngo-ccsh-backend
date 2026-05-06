"""
Script para testes locais com SQLite em memória, não persistente, sem alterar o banco de produção.
"""

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# cria tabelas com managed = False
force_create_unmanaged_models()

# desativa configuração ativa apenas em produção
FORCE_SCRIPT_NAME = None