import re
from pathlib import Path

from django.apps import apps
from django.test import SimpleTestCase

from despesas.models import (
    Empenho,
    ExercicioCentro,
    Finalidade,
    GrupoFinalidade,
    ItemListaSIAFI,
    Lancamento,
    ListaSIAFI,
    Natureza,
    ParcelaBolsa,
    TipoDocumento,
    TipoDocumentoParaFinalidade,
    TipoMovimento,
    Transacao,
    ValorDocumento,
    VinculoBolsa,
)
from entidades.models import Centro, Email, Pessoa, Telefone, Unidade
from usuarios.models import Usuario


DDL_DIRECTORY = Path(__file__).parents[2] / "database" / "sql" / "create"
MODELS = (
    Centro,
    Unidade,
    Pessoa,
    Email,
    Telefone,
    Usuario,
    Natureza,
    GrupoFinalidade,
    Finalidade,
    TipoDocumento,
    TipoDocumentoParaFinalidade,
    Empenho,
    TipoMovimento,
    Transacao,
    Lancamento,
    ValorDocumento,
    ExercicioCentro,
    VinculoBolsa,
    ParcelaBolsa,
    ListaSIAFI,
    ItemListaSIAFI,
)
MODELS += tuple(
    model
    for model in apps.get_app_config("despesas").get_models()
    if model._meta.db_table.startswith("despesas_historical")
)
CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+ORCAMENTO\.([A-Z0-9_]+)\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)
COLUMN = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s+", re.IGNORECASE)


class Db2SchemaTests(SimpleTestCase):
    def test_internal_model_columns_are_declared_in_manual_ddl(self):
        ddl_columns = {}
        for path in DDL_DIRECTORY.glob("*.sql"):
            for match in CREATE_TABLE.finditer(path.read_text(encoding="utf-8")):
                table = match.group(1).casefold()
                columns = set()
                for line in match.group(2).splitlines():
                    column = COLUMN.match(line)
                    if column and column.group(1).upper() != "CONSTRAINT":
                        columns.add(column.group(1).casefold())
                ddl_columns[table] = columns

        missing = []
        for model in MODELS:
            columns = ddl_columns.get(model._meta.db_table.casefold())
            if columns is None:
                missing.append(f"{model.__name__}: tabela {model._meta.db_table}")
                continue
            for field in model._meta.local_concrete_fields:
                if field.column.casefold() not in columns:
                    missing.append(f"{model.__name__}.{field.name}: coluna {field.column}")

        self.assertEqual(missing, [])
