from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APIClient

from despesas import services
from despesas.models import Transacao
from despesas.tests.helpers import BaseRazao


class TransactionApiTests(BaseRazao):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.api.force_authenticate(user=self.usuario)

    def test_create_credit_returns_transaction_and_ledger_lines(self):
        response = self.api.post(
            reverse("despesas:transacoes-list"),
            {
                "operacao": "credito",
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "natureza": self.custeio.pk,
                "montante": "500.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["operacao"], Transacao.Operacao.CREDITO)
        self.assertEqual(response.data["id_usuario"], self.usuario.pk)
        self.assertEqual(len(response.data["lancamentos"]), 1)
        self.assertEqual(response.data["lancamentos"][0]["montante"], "500.00")

    def test_invalid_operation_does_not_create_transaction(self):
        response = self.api.post(
            reverse("despesas:transacoes-list"),
            {"operacao": "not-supported"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transacao.objects.count(), 0)

    def test_correcting_an_expense_creates_a_new_transaction(self):
        empenho = self.novo_empenho("001", self.bolsa2a)
        self.creditar(500)
        services.reforcar_empenho(empenho, 500, self.usuario)
        original = services.registrar_despesa(
            empenho, None, self.bolsa2a, 100, self.usuario
        )

        response = self.api.post(
            f"/despesas/transacoes/{original.pk}/corrigir/",
            {
                "justificativa": "Ajuste do valor",
                "linhas": [
                    {
                        "tipo": "pagamento",
                        "centro": self.centro.pk,
                        "ano_fiscal": 2026,
                        "natureza": self.custeio.pk,
                        "montante": "-90.00",
                        "empenho": empenho.pk,
                        "finalidade": self.bolsa2a.pk,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["id_transacao_corrigida"], original.pk)
        self.assertEqual(len(response.data["lancamentos"]), 2)
        original.refresh_from_db()
        self.assertEqual(original.correcoes.get().lancamentos_vigentes().get().montante, Decimal("-90.00"))
