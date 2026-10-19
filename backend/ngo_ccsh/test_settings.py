"""
Script para testes locais com SQLite em memória, não persistente, sem alterar o banco de produção.
"""

from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

TEST_RUNNER = "ngo_ccsh.test_runner.CustomTestRunner"

# desativa configuração ativa apenas em produção
FORCE_SCRIPT_NAME = None
