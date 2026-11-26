from django.urls import reverse
from rest_framework.test import APIClient

from despesas import services
from despesas.tests.helpers import BaseRazao


class IdFilterApiTests(BaseRazao):
    def setUp(self):
        super().setUp()
        self.api = APIClient()
        self.api.force_authenticate(user=self.usuario)

    def test_operations_expose_stable_ids_and_filter_transactions_by_id(self):
        self.creditar(500)
        self.distribuir(self.A, 100)

        operations = self.api.get(reverse("despesas:tipos_dado"))
        self.assertEqual(operations.status_code, 200, operations.data)
        by_code = {item["codigo"]: item for item in operations.data["data"]}
        self.assertEqual(
            {code: item["id_operacao"] for code, item in by_code.items()},
            {
                "credito": 1,
                "reforco": 2,
                "distribuicao": 3,
                "transferencia": 4,
                "despesa": 5,
                "anulacao": 6,
                "conversao": 7,
                "lista_siafi": 8,
                "fechamento": 9,
                "reabertura": 10,
                "correcao": 11,
            },
        )
        self.assertEqual(
            by_code["credito"],
            {"id_operacao": 1, "nome": "Crédito", "codigo": "credito"},
        )

        transactions = self.api.get(
            reverse("despesas:transacoes-list"), {"id_operacao": "1,3"}
        )
        self.assertEqual(transactions.status_code, 200, transactions.data)
        self.assertEqual(transactions.data["count"], 2)
        self.assertEqual(
            {item["id_operacao"] for item in transactions.data["data"]},
            {1, 3},
        )

        unknown_operation = self.api.get(
            reverse("despesas:transacoes-list"), {"id_operacao": 999}
        )
        self.assertEqual(unknown_operation.status_code, 200, unknown_operation.data)
        self.assertEqual(unknown_operation.data["count"], 0)

    def test_lancamento_serializer_and_filters_use_ids(self):
        credit = self.creditar(500)
        credit_line = credit.lancamentos.get()
        credit_lines = self.api.get(
            reverse(
                "despesas:transacao-lancamentos-list",
                kwargs={"transacao_pk": credit.pk},
            ),
            {
                "id_tipo_movimento": credit_line.tipo_movimento_id,
                "id_natureza": self.custeio.pk,
                "id_finalidade": "null",
            },
        )

        self.assertEqual(credit_lines.status_code, 200, credit_lines.data)
        self.assertEqual(credit_lines.data["count"], 1)
        serialized_credit = credit_lines.data["data"][0]
        self.assertEqual(
            serialized_credit["id_tipo_movimento"], credit_line.tipo_movimento_id
        )
        self.assertEqual(serialized_credit["id_natureza"], self.custeio.pk)
        self.assertIsNone(serialized_credit["id_finalidade"])

        empenho = self.novo_empenho("001", self.bolsa2a)
        services.reforcar_empenho(empenho, 100, self.usuario)
        expense = services.registrar_despesa(
            empenho, None, self.bolsa2a, 25, self.usuario
        )
        expense_lines = self.api.get(
            reverse(
                "despesas:transacao-lancamentos-list",
                kwargs={"transacao_pk": expense.pk},
            ),
            {"id_finalidade": self.bolsa2a.pk},
        )

        self.assertEqual(expense_lines.status_code, 200, expense_lines.data)
        self.assertEqual(expense_lines.data["count"], 1)
        self.assertEqual(
            expense_lines.data["data"][0]["id_finalidade"], self.bolsa2a.pk
        )

    def test_empenhos_and_finalidades_can_be_filtered_by_id(self):
        empenho = self.novo_empenho("001", self.bolsa2a)
        self.novo_empenho("002", self.passagens)

        empenhos = self.api.get(
            reverse("despesas:empenhos-list"), {"id_empenho": empenho.pk}
        )
        self.assertEqual(empenhos.status_code, 200, empenhos.data)
        self.assertEqual(empenhos.data["count"], 1)
        self.assertEqual(empenhos.data["data"][0]["id_empenho"], empenho.pk)

        finalidades = self.api.get(
            reverse("despesas:finalidades-list"),
            {"id_finalidade": self.passagens.pk},
        )
        self.assertEqual(finalidades.status_code, 200, finalidades.data)
        self.assertEqual(finalidades.data["count"], 1)
        self.assertEqual(
            finalidades.data["data"][0]["id_finalidade"], self.passagens.pk
        )
