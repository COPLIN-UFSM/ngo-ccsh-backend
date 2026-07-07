import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from despesas.models import *
from entidades.models import *

from tqdm import tqdm

class Command(BaseCommand):
    help = 'Cria dados iniciais para o banco de dados de desenvolvimento'

    @staticmethod
    def convert_value(field, value):
        if value == "":
            return None

        if isinstance(field, models.BooleanField):
            return value.upper() in ("TRUE", "1", "YES")

        if isinstance(field, ( models.IntegerField, models.AutoField, models.BigIntegerField)):
            return int(value)

        if isinstance(field, models.DecimalField):
            return Decimal(value)

        return value


    def handle(self, *args, **kwargs):
        csv_path = Path(settings.BASE_DIR) / 'database' / 'csv'

        mapping = {
            # Entidades
            "V_CENTROS_SIE.csv": CentroSIE,
            "V_TIPOS_UNIDADES.csv": TipoUnidade,
            "V_SITUACOES_UNIDADES.csv": SituacaoUnidade,
            "V_UNIDADES_SIE.csv": UnidadeSIE,
            "V_CURSOS.csv": Curso,
            "V_CARGOS.csv": Cargo,
            "V_PESSOAS_SIE.csv": PessoaSIE,
            "V_SERVIDORES.csv": Servidor,
            "V_DISCENTES.csv": Discente,
            # Despesas
            "NATUREZAS_FINALIDADES.csv": NaturezaFinalidade,
            "GRUPOS_FINALIDADES.csv": GrupoFinalidade,
            "FINALIDADES.csv": Finalidade,
            "TIPOS_DOCUMENTOS.csv": TipoDocumento,
            "TIPOS_DOCUMENTOS_PARA_FINALIDADES.csv": TipoDocumentoParaFinalidade,
            "STATUS_TRANSACOES.csv": StatusTransacao,
        }

        for filename, model in tqdm(mapping.items(), total=len(mapping), desc='Inserindo dados'):
            field_map = {}
            field_objects = {}

            for field in model._meta.fields:
                attr_name = field.attname if field.is_relation else field.name

                if field.column is not None:
                    field_map[field.column.upper()] = attr_name

                field_objects[attr_name] = field

            with open(csv_path / filename, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    new_row = {}

                    for key, value in row.items():
                        attr_name = field_map[key.upper()]
                        field = field_objects[attr_name]

                        new_row[attr_name] = self.convert_value(field, value)

                    model.objects.create(**new_row)
