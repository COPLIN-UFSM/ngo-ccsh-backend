import os.path

import csv
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from despesas.models import Beneficiario, Unidade, Finalidade, GrupoFinalidade, NaturezaFinalidade, TipoDocumento, \
    Empenho, Transacao, Centro, TipoUnidade, SituacaoUnidade
from usuarios.models import Usuario

from pathlib import Path
from django.conf import settings

# beneficiarios = [
#     Beneficiario(beneficiario_interno="Leandro", cpf="05186605085",matricula="202311173"),
#     Beneficiario(beneficiario_interno="Raíssa", cpf="00000000012",matricula="202411173")
# ]
#
# tipos_documentos = [
#     TipoDocumento(tipo_documento="Fatura"),
#     TipoDocumento(tipo_documento="Lista SIAFE")
# ]

class Command(BaseCommand):
    help = 'Cria dados iniciais para o banco de dados de desenvolvimento'

    def handle(self, *args, **kwargs):
        csv_path = Path(settings.BASE_DIR) / 'database' / 'csv'

        mapping = {
            "V_CENTROS.csv": Centro,
            "V_TIPOS_UNIDADES.csv": TipoUnidade,
            "V_SITUACOES_UNIDADES.csv": SituacaoUnidade,
            "V_UNIDADES.csv": Unidade,
        }

        for filename, model in mapping.items():
            with open(csv_path / filename, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        model.objects.create(**row)
                    except IntegrityError as ie:
                        print(row)
                        raise ie


        # bolsas, _ = GrupoFinalidade.objects.get_or_create(grupo_finalidade="Bolsas")
        # viagens, _ = GrupoFinalidade.objects.get_or_create(grupo_finalidade="Viagens")
        #
        # custeio, _ = NaturezaFinalidade.objects.get_or_create(natureza_finalidade="Custeio")
        # NaturezaFinalidade.objects.get_or_create(natureza_finalidade="Capital")
        #
        # finalidade,_ = Finalidade.objects.get_or_create(finalidade="Bolsa 2A", natureza_finalidade=custeio, grupo_finalidade=bolsas)
        # Finalidade.objects.get_or_create(finalidade="Bolsa Formação", natureza_finalidade=custeio, grupo_finalidade=bolsas)
        # Finalidade.objects.get_or_create(finalidade="Viagem Área", natureza_finalidade=custeio, grupo_finalidade=viagens)
        # Finalidade.objects.get_or_create(finalidade="Bolsa PRAE", natureza_finalidade=custeio, grupo_finalidade=bolsas)
        #
        # subunidades = Unidade.objects.bulk_create(subunidades_insert, ignore_conflicts=True)
        # subunidade_1 = Unidade.objects.filter(subunidade="Proplan").first()
        #
        # usuario = Usuario.objects.create_user(matricula="leandrogalbarino", email="leandrogalbarino@gmail.com", password="leandrogalbarino")
        #
        # Beneficiario.objects.bulk_create(beneficiarios,ignore_conflicts=True)
        # empenho,_ = Empenho.objects.get_or_create(empenho="fsfdsf45", descricao="Empenho de bolsas 2A", finalidade=finalidade)
        # transacao = Transacao.objects.get_or_create(
        #         finalidade=finalidade,
        #         empenho=empenho,
        #         unidade_executora=subunidade_1,
        #         usuario=usuario,
        #         status="PAGO",
        #         descricao="Blá blá blá.........",
        #         montante=1.1,
        #         eh_credito=False
        # )
