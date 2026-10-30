from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from despesas.models import (
    Empenho,
    ExercicioCentro,
    Finalidade,
    Lancamento,
    Natureza,
    Transacao,
)
from entidades.models import Centro, Pessoa, SituacaoUnidade, TipoUnidade, Unidade
from usuarios.models import Usuario


class TestModelsCommandTests(TestCase):
    def test_runs_full_year_flow_and_rolls_back_all_test_data(self):
        # A unidade interna precisa apontar para valores das views institucionais.
        # Nesta execução isolada, estes registros representam as linhas de referência
        # que normalmente já existem no SIE.
        TipoUnidade.objects.create(tipo_unidade="Unidade de teste")
        SituacaoUnidade.objects.create(situacao_unidade="Ativa")

        before_counts = {
            "centros": Centro.objects.count(),
            "empenhos": Empenho.objects.count(),
            "exercicios": ExercicioCentro.objects.count(),
            "finalidades": Finalidade.objects.count(),
            "lancamentos": Lancamento.objects.count(),
            "naturezas": Natureza.objects.count(),
            "pessoas": Pessoa.objects.count(),
            "transacoes": Transacao.objects.count(),
            "unidades": Unidade.objects.count(),
            "usuarios": Usuario.objects.count(),
        }
        output = StringIO()

        call_command("test_models", stdout=output)

        self.assertIn("[1/6] Exercício", output.getvalue())
        self.assertIn("[6/6] Exercício fechado", output.getvalue())
        self.assertIn("Os dados de teste foram revertidos.", output.getvalue())
        self.assertEqual(
            {
                "centros": Centro.objects.count(),
                "empenhos": Empenho.objects.count(),
                "exercicios": ExercicioCentro.objects.count(),
                "finalidades": Finalidade.objects.count(),
                "lancamentos": Lancamento.objects.count(),
                "naturezas": Natureza.objects.count(),
                "pessoas": Pessoa.objects.count(),
                "transacoes": Transacao.objects.count(),
                "unidades": Unidade.objects.count(),
                "usuarios": Usuario.objects.count(),
            },
            before_counts,
        )
