import datetime as dt
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APIClient

from despesas import services
from despesas.models import ListaSIAFI, ParcelaBolsa, Transacao, VinculoBolsa
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
        self.assertEqual(
            original.correcoes.get().lancamentos_vigentes().get().montante,
            Decimal("-90.00"),
        )

    def test_create_vinculo_generate_allocate_and_cancel_parcela(self):
        bolsista = self.bolsista()
        response = self.api.post(
            reverse("despesas:vinculos-bolsa-list"),
            {
                "bolsista": bolsista.pk,
                "unidade": self.A.pk,
                "finalidade": self.bolsa2a.pk,
                "valor_mensal": "100.00",
                "inicio": "2026-07-14",
                "fim": "2026-08-31",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        vinculo = VinculoBolsa.objects.get(pk=response.data["id_vinculo_bolsa"])
        generated = self.api.post(
            reverse(
                "despesas:vinculos-bolsa-gerar-parcelas",
                args=[vinculo.pk],
            ),
            {},
            format="json",
        )
        self.assertEqual(generated.status_code, 201, generated.data)
        self.assertEqual(
            [row["competencia"] for row in generated.data],
            ["2026-07-01", "2026-08-01"],
        )
        repeated = self.api.post(
            reverse("despesas:vinculos-bolsa-gerar-parcelas", args=[vinculo.pk]),
            {},
            format="json",
        )
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.data, [])

        self.creditar(200)
        self.distribuir(self.A, 200)
        parcela_id = generated.data[0]["id_parcela_bolsa"]
        allocated = self.api.post(
            reverse("despesas:parcelas-bolsa-alocar", args=[parcela_id]),
            {},
            format="json",
        )
        self.assertEqual(allocated.status_code, 200, allocated.data)
        self.assertEqual(allocated.data["status"], ParcelaBolsa.Status.ALOCADA)
        cancelled = self.api.post(
            reverse("despesas:parcelas-bolsa-cancelar", args=[parcela_id]),
            {},
            format="json",
        )
        self.assertEqual(cancelled.status_code, 200, cancelled.data)
        self.assertEqual(cancelled.data["status"], ParcelaBolsa.Status.CANCELADA)

    def test_invalid_vinculo_is_rejected_without_database_error(self):
        bolsista = self.bolsista()
        response = self.api.post(
            reverse("despesas:vinculos-bolsa-list"),
            {
                "bolsista": bolsista.pk,
                "unidade": self.A.pk,
                "finalidade": self.bolsa2a.pk,
                "valor_mensal": "0.00",
                "inicio": "2026-08-01",
                "fim": "2026-07-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(VinculoBolsa.objects.count(), 0)

    def test_create_and_pay_siafi_list_through_api(self):
        bolsista = self.bolsista()
        vinculo = VinculoBolsa.objects.create(
            bolsista=bolsista,
            unidade=self.A,
            finalidade=self.bolsa2a,
            valor_mensal=Decimal("100"),
            inicio=dt.date(2026, 7, 1),
            fim=dt.date(2026, 7, 31),
        )
        parcela = services.gerar_parcelas(vinculo)[0]
        empenho = self.novo_empenho("001", self.bolsa2a)
        empenho_adicional = self.novo_empenho("002", self.bolsa2a)
        self.creditar(200)
        services.reforcar_empenho(empenho, 60, self.usuario)
        services.reforcar_empenho(empenho_adicional, 40, self.usuario)
        self.distribuir(self.A, 100)
        services.alocar_parcela(parcela, empenho)

        created = self.api.post(
            reverse("despesas:listas-siafi-list"),
            {"centro": self.centro.pk, "competencia": "2026-07-21"},
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        lista_id = created.data["id_lista_siafi"]
        self.assertEqual(created.data["competencia"], "2026-07-01")

        included = self.api.post(
            reverse("despesas:listas-siafi-incluir-itens", args=[lista_id]),
            {"parcelas": [parcela.pk]},
            format="json",
        )
        self.assertEqual(included.status_code, 201, included.data)
        self.assertEqual(len(included.data["itens"]), 1)

        paid = self.api.post(
            reverse("despesas:listas-siafi-pagar", args=[lista_id]),
            {
                "numero_siafi": "2026LS000123",
                "divisoes": [
                    {
                        "item": included.data["itens"][0]["id_item_lista_siafi"],
                        "partes": [
                            {"empenho": empenho.pk, "valor": "60.00"},
                            {"empenho": empenho_adicional.pk, "valor": "40.00"},
                        ],
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(paid.status_code, 201, paid.data)
        self.assertEqual(paid.data["operacao"], Transacao.Operacao.LISTA_SIAFI)
        lista = ListaSIAFI.objects.get(pk=lista_id)
        self.assertEqual(lista.status, ListaSIAFI.Status.PAGA)
        self.assertEqual(empenho.saldo, Decimal("0"))
        self.assertEqual(empenho_adicional.saldo, Decimal("0"))
        parcela.refresh_from_db()
        self.assertEqual(parcela.status, ParcelaBolsa.Status.PAGA)

    def test_removing_draft_list_item_does_not_cancel_allocation(self):
        bolsista = self.bolsista()
        vinculo = VinculoBolsa.objects.create(
            bolsista=bolsista,
            unidade=self.A,
            finalidade=self.bolsa2a,
            valor_mensal=Decimal("100"),
            inicio=dt.date(2026, 7, 1),
            fim=dt.date(2026, 7, 31),
        )
        parcela = services.gerar_parcelas(vinculo)[0]
        self.creditar(100)
        self.distribuir(self.A, 100)
        services.alocar_parcela(parcela)

        lista_response = self.api.post(
            reverse("despesas:listas-siafi-list"),
            {"centro": self.centro.pk, "competencia": "2026-07-01"},
            format="json",
        )
        self.assertEqual(lista_response.status_code, 201, lista_response.data)
        lista_id = lista_response.data["id_lista_siafi"]
        included = self.api.post(
            reverse("despesas:listas-siafi-incluir-itens", args=[lista_id]),
            {"parcelas": [parcela.pk]},
            format="json",
        )
        self.assertEqual(included.status_code, 201, included.data)
        item_id = included.data["itens"][0]["id_item_lista_siafi"]

        removed = self.api.delete(
            reverse(
                "despesas:listas-siafi-remover-item",
                args=[lista_id, item_id],
            )
        )
        self.assertEqual(removed.status_code, 204)
        self.assertFalse(
            ListaSIAFI.objects.get(pk=lista_id).itens.filter(pk=item_id).exists()
        )
        parcela.refresh_from_db()
        self.assertEqual(parcela.status, ParcelaBolsa.Status.ALOCADA)

    def test_exercise_pending_close_and_reopen_endpoints(self):
        self.creditar(100)
        pending_url = reverse("despesas:exercicios-pendencias")
        query = {"centro": self.centro.pk, "ano_fiscal": 2026}
        response = self.api.get(pending_url, query)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data["ok"])
        self.assertEqual(response.data["status"], "aberto")

        closed = self.api.post(
            reverse("despesas:exercicios-fechar"),
            {
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "destinos": [
                    {
                        "acao": "devolver",
                        "montante": "100.00",
                        "natureza": self.custeio.pk,
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(closed.status_code, 201, closed.data)
        self.assertEqual(closed.data["operacao"], Transacao.Operacao.FECHAMENTO)

        response = self.api.get(pending_url, query)
        self.assertEqual(response.data["status"], "fechado")
        self.assertTrue(response.data["ok"])

        reopened = self.api.post(
            reverse("despesas:exercicios-reabrir"),
            {
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "justificativa": "Reabertura para corrigir o fechamento",
            },
            format="json",
        )
        self.assertEqual(reopened.status_code, 201, reopened.data)
        self.assertEqual(reopened.data["operacao"], Transacao.Operacao.REABERTURA)
        response = self.api.get(pending_url, query)
        self.assertEqual(response.data["status"], "aberto")
