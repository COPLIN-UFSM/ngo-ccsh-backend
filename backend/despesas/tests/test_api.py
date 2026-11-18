import datetime as dt
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from entidades.models import Centro
from rest_framework.test import APIClient

from despesas import services
from despesas.models import (
    Finalidade,
    GrupoFinalidade,
    ListaSIAFI,
    ParcelaBolsa,
    TipoDocumento,
    Transacao,
    VinculoBolsa,
)
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
        self.assertEqual(
            response.data["lancamentos"][0]["id_centro"], self.centro.pk
        )
        self.assertEqual(response.data["lancamentos"][0]["montante"], "500.00")

    def test_transactions_filter_by_ledger_fiscal_year(self):
        matching = self.creditar(100, ano=2026)
        self.creditar(200, ano=2025)

        response = self.api.get(
            reverse("despesas:transacoes-list"),
            {"centro": self.centro.pk, "ano_fiscal": 2026},
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            [row["id_transacao"] for row in response.data["data"]],
            [matching.pk],
        )

    def test_finalidades_can_be_ordered_by_natureza_and_grupo_names(self):
        grupo_zeta = GrupoFinalidade.objects.create(nome="Zeta")
        grupo_alfa = GrupoFinalidade.objects.create(nome="Alfa")
        Finalidade.objects.create(
            nome="Grupo Zeta", natureza=self.custeio, grupo=grupo_zeta
        )
        Finalidade.objects.create(
            nome="Grupo Alfa", natureza=self.custeio, grupo=grupo_alfa
        )

        url = reverse("despesas:finalidades-list")
        natureza_response = self.api.get(url, {"ordering": "natureza"})
        self.assertEqual(natureza_response.status_code, 200, natureza_response.data)
        self.assertEqual(
            natureza_response.data["data"][0]["natureza"],
            "Capital",
        )

        grupo_response = self.api.get(url, {"ordering": "grupo"})
        self.assertEqual(grupo_response.status_code, 200, grupo_response.data)
        grupo_names = [
            row.get("grupo")
            for row in grupo_response.data["data"]
            if row.get("grupo") in {"Alfa", "Zeta"}
        ]
        self.assertEqual(grupo_names, ["Alfa", "Zeta"])

    def test_finalidades_filter_by_multiple_names_and_related_labels(self):
        grupo_zeta = GrupoFinalidade.objects.create(nome="Zeta")
        grupo_alfa = GrupoFinalidade.objects.create(nome="Alfa")
        Finalidade.objects.create(
            nome="Grupo Zeta", natureza=self.custeio, grupo=grupo_zeta
        )
        Finalidade.objects.create(
            nome="Grupo Alfa", natureza=self.custeio, grupo=grupo_alfa
        )
        url = reverse("despesas:finalidades-list")

        names = self.api.get(url, {"nome": "Bolsa 2A,Passagens"})
        self.assertEqual(names.status_code, 200, names.data)
        self.assertEqual(
            {row["nome"] for row in names.data["data"]},
            {"Bolsa 2A", "Passagens"},
        )

        naturezas = self.api.get(url, {"natureza": "Custeio,Capital"})
        self.assertEqual(naturezas.status_code, 200, naturezas.data)
        self.assertEqual(naturezas.data["count"], 5)

        grupos = self.api.get(url, {"grupo": "Alfa,Zeta"})
        self.assertEqual(grupos.status_code, 200, grupos.data)
        self.assertEqual(
            {row["grupo"] for row in grupos.data["data"]},
            {"Alfa", "Zeta"},
        )

    def test_empenhos_filter_and_order_by_supported_fields(self):
        matching = self.novo_empenho("2026-002", self.bolsa2a)
        self.novo_empenho("2025-001", self.obra, ano=2025)

        url = reverse("despesas:empenhos-list")
        filtered = self.api.get(
            url,
            {
                "numero_empenho": "2026",
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "natureza": self.custeio.pk,
                "finalidade": self.bolsa2a.pk,
            },
        )
        self.assertEqual(filtered.status_code, 200, filtered.data)
        self.assertEqual(
            [row["id_empenho"] for row in filtered.data["data"]], [matching.pk]
        )

        ordered = self.api.get(url, {"ordering": "numero_empenho"})
        self.assertEqual(ordered.status_code, 200, ordered.data)
        self.assertEqual(
            [row["numero_empenho"] for row in ordered.data["data"]],
            ["2025-001", "2026-002"],
        )

    def test_tipo_documento_filter_and_order_by_name(self):
        TipoDocumento.objects.create(nome="Nota antecipada")
        inactive = TipoDocumento.objects.create(
            nome="Nota complementar", ativo=False
        )
        url = reverse("despesas:tipos_documentos-list")

        filtered = self.api.get(url, {"nome": "nota", "ordering": "nome"})
        self.assertEqual(filtered.status_code, 200, filtered.data)
        self.assertEqual(
            [row["nome"] for row in filtered.data["data"]],
            ["Nota antecipada", "Nota fiscal"],
        )

        include_inactive = self.api.get(
            url, {"nome": "nota", "ativo": "false"}
        )
        self.assertEqual(include_inactive.status_code, 200, include_inactive.data)
        self.assertEqual(
            [row["id_tipo_documento"] for row in include_inactive.data["data"]],
            [inactive.pk],
        )

    def test_scholarship_endpoints_filter_by_scalar_fields(self):
        bolsista = self.bolsista()
        vinculo = VinculoBolsa.objects.create(
            bolsista=bolsista,
            unidade=self.A,
            finalidade=self.bolsa2a,
            valor_mensal=Decimal("100.00"),
            inicio=dt.date(2026, 1, 1),
            fim=dt.date(2026, 2, 1),
        )
        parcela = ParcelaBolsa.objects.create(
            vinculo=vinculo,
            competencia=dt.date(2026, 1, 1),
            valor=Decimal("100.00"),
            status=ParcelaBolsa.Status.ALOCADA,
        )
        lista = ListaSIAFI.objects.create(
            centro=self.centro, competencia=dt.date(2026, 1, 1)
        )
        outro_centro = Centro.objects.create(
            nome_centro="Outro centro",
            sigla_centro="OUTRO",
            cod_estruturado="22",
        )
        outra_unidade = self.nova_unidade(
            "Outra unidade", "22.01", centro=outro_centro
        )
        outro_vinculo = VinculoBolsa.objects.create(
            bolsista=self.bolsista("Bia 2", "2"),
            unidade=outra_unidade,
            finalidade=self.bolsa2a,
            valor_mensal=Decimal("100.00"),
            inicio=dt.date(2027, 1, 1),
            fim=dt.date(2027, 2, 1),
        )

        vinculos = self.api.get(
            reverse("despesas:vinculos-bolsa-list"),
            {
                "bolsista": bolsista.pk,
                "unidade": self.A.pk,
                "finalidade": self.bolsa2a.pk,
            },
        )
        self.assertEqual(vinculos.status_code, 200, vinculos.data)
        self.assertEqual(
            [row["id_vinculo_bolsa"] for row in vinculos.data["data"]],
            [vinculo.pk],
        )

        scoped_vinculos = self.api.get(
            reverse("despesas:vinculos-bolsa-list"),
            {"centro": outro_centro.pk, "ano_fiscal": 2027},
        )
        self.assertEqual(scoped_vinculos.status_code, 200, scoped_vinculos.data)
        self.assertEqual(
            [row["id_vinculo_bolsa"] for row in scoped_vinculos.data["data"]],
            [outro_vinculo.pk],
        )

        parcelas = self.api.get(
            reverse("despesas:parcelas-bolsa-list"),
            {
                "vinculo": vinculo.pk,
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "status": ParcelaBolsa.Status.ALOCADA,
                "competencia": "2026-01-01",
            },
        )
        self.assertEqual(parcelas.status_code, 200, parcelas.data)
        self.assertEqual(
            [row["id_parcela_bolsa"] for row in parcelas.data["data"]],
            [parcela.pk],
        )

        other_center_parcels = self.api.get(
            reverse("despesas:parcelas-bolsa-list"),
            {"centro": outro_centro.pk, "ano_fiscal": 2026},
        )
        self.assertEqual(other_center_parcels.status_code, 200, other_center_parcels.data)
        self.assertEqual(other_center_parcels.data["count"], 0)

        listas = self.api.get(
            reverse("despesas:listas-siafi-list"),
            {
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "competencia": "2026-01-01",
                "status": ListaSIAFI.Status.RASCUNHO,
            },
        )
        self.assertEqual(listas.status_code, 200, listas.data)
        self.assertEqual(
            [row["id_lista_siafi"] for row in listas.data["data"]], [lista.pk]
        )

    def test_unit_balances_require_a_year_or_unit_and_support_history(self):
        self.creditar(100, ano=2026)
        self.distribuir(self.A, 100, ano=2026)
        self.creditar(50, ano=2025)
        self.distribuir(self.A, 50, ano=2025)
        self.creditar(75, ano=2025)
        self.distribuir(self.B, 75, ano=2025)

        url = reverse("despesas:unidades-list")
        unfiltered = self.api.get(url)
        self.assertEqual(unfiltered.status_code, 400)

        by_year = self.api.get(url, {"ano_fiscal": 2026})
        self.assertEqual(by_year.status_code, 200, by_year.data)
        by_year_balances = {
            (row["id_unidade_interna"], row["id_natureza"]): row["saldo"]
            for row in by_year.data["data"]
        }
        self.assertEqual(
            by_year_balances[(self.A.pk, self.custeio.pk)], "100.00"
        )
        self.assertEqual(by_year_balances[(self.B.pk, self.custeio.pk)], "0.00")
        self.assertEqual(
            {row["id_unidade_interna"] for row in by_year.data["data"]},
            {self.A.pk, self.B.pk},
        )

        history = self.api.get(url, {"id_unidade_interna": self.A.pk})
        self.assertEqual(history.status_code, 200, history.data)
        self.assertEqual(
            [row["ano_fiscal"] for row in history.data["data"]], [2025, 2026]
        )
        self.assertEqual(
            [row["saldo"] for row in history.data["data"]], ["50.00", "100.00"]
        )
        self.assertTrue(
            all(
                row["id_unidade_interna"] == self.A.pk
                for row in history.data["data"]
            )
        )

    def test_unit_balances_can_be_limited_by_centro(self):
        other_center = Centro.objects.create(
            nome_centro="Outro centro", sigla_centro="OUT", cod_estruturado="12"
        )
        self.nova_unidade("Outra unidade", "12.01", centro=other_center)

        response = self.api.get(
            reverse("despesas:unidades-list"),
            {"ano_fiscal": 2026, "centro": self.centro.pk},
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            {row["id_unidade_interna"] for row in response.data["data"]},
            {self.A.pk, self.B.pk},
        )

    def test_transactions_filter_by_center_amount_operation_and_dates(self):
        today = dt.date.today()
        credit = services.creditar(
            self.centro, 2026, self.custeio, 100, self.usuario, data=today
        )
        distribution = services.distribuir(
            self.centro,
            2026,
            self.custeio,
            self.A,
            40,
            self.usuario,
            data=today,
        )
        day_start = timezone.make_aware(dt.datetime.combine(today, dt.time.min))
        date_bound = day_start.isoformat()

        response = self.api.get(
            reverse("despesas:transacoes-list"),
            {
                "centro": self.centro.pk,
                "operacao": "credito,distribuicao",
                "data_after": date_bound,
                "data_before": date_bound,
                "criada_em_after": date_bound,
                "criada_em_before": date_bound,
                "id_transacao_min": min(credit.pk, distribution.pk),
                "id_transacao_max": max(credit.pk, distribution.pk),
            },
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            {row["id_transacao"] for row in response.data["data"]},
            {credit.pk, distribution.pk},
        )

        by_amount = self.api.get(
            reverse("despesas:transacoes-list"),
            {"montante_min": "100", "montante_max": "100"},
        )
        self.assertEqual(by_amount.status_code, 200, by_amount.data)
        self.assertEqual(
            {row["id_transacao"] for row in by_amount.data["data"]},
            {credit.pk},
        )

    def test_nested_lancamentos_support_range_category_and_ordering(self):
        credit = services.creditar(
            self.centro, 2026, self.custeio, 100, self.usuario
        )
        lancamento = credit.lancamentos.get()
        url = reverse(
            "despesas:transacao-lancamentos-list",
            kwargs={"transacao_pk": credit.pk},
        )

        response = self.api.get(
            url,
            {
                "id_lancamento_min": lancamento.pk,
                "id_lancamento_max": lancamento.pk,
                "id_unidade": "null",
                "natureza": "Custeio",
                "tipo_movimento": "Crédito ordinário",
                "finalidade": "null",
                "montante_min": "100",
                "montante_max": "100",
                "ordering": "tipo_movimento",
            },
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["data"][0]["id_lancamento"], lancamento.pk
        )

    def test_unit_balances_include_spent_and_allocated_amounts(self):
        self.creditar(200)
        empenho = self.novo_empenho("001", self.bolsa2a)
        services.reforcar_empenho(empenho, 100, self.usuario)
        self.distribuir(self.A, 100)
        services.registrar_despesa(
            empenho, self.A, self.bolsa2a, 40, self.usuario
        )

        response = self.api.get(
            reverse("despesas:unidades-list"),
            {"ano_fiscal": 2026, "id_unidades": [self.A.pk]},
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data["data"]), 1)
        row = response.data["data"][0]
        self.assertEqual(row["saldo"], "60.00")
        self.assertEqual(row["gasto"], "40.00")
        self.assertEqual(row["orcamento"], "100.00")

    def test_invalid_operation_does_not_create_transaction(self):
        response = self.api.post(
            reverse("despesas:transacoes-list"),
            {"operacao": "not-supported"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Transacao.objects.count(), 0)

    def test_create_transfer_between_units(self):
        self.creditar(300)
        self.distribuir(self.A, 200)
        response = self.api.post(
            reverse("despesas:transacoes-list"),
            {
                "operacao": "transferencia",
                "centro": self.centro.pk,
                "ano_fiscal": 2026,
                "natureza": self.custeio.pk,
                "unidade_origem": self.A.pk,
                "unidade_destino": self.B.pk,
                "montante": "75.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["operacao"], Transacao.Operacao.TRANSFERENCIA)
        self.assertEqual(len(response.data["lancamentos"]), 2)
        self.assertEqual(
            [row["montante"] for row in response.data["lancamentos"]],
            ["-75.00", "75.00"],
        )

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
            reverse("despesas:listas-siafi-incluir-parcelas", args=[lista_id]),
            {"parcelas": [parcela.pk]},
            format="json",
        )
        self.assertEqual(included.status_code, 201, included.data)
        self.assertEqual(len(included.data["parcelas"]), 1)
        self.assertEqual(included.data["total"], "100.00")

        paid = self.api.post(
            reverse("despesas:listas-siafi-pagar", args=[lista_id]),
            {
                "numero_siafi": "2026LS000123",
                "divisoes": [
                    {
                        "parcela": included.data["parcelas"][0]["id_parcela_bolsa"],
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
            reverse("despesas:listas-siafi-incluir-parcelas", args=[lista_id]),
            {"parcelas": [parcela.pk]},
            format="json",
        )
        self.assertEqual(included.status_code, 201, included.data)
        parcela_id = included.data["parcelas"][0]["id_parcela_bolsa"]

        removed = self.api.delete(
            reverse(
                "despesas:listas-siafi-remover-parcela",
                args=[lista_id, parcela_id],
            )
        )
        self.assertEqual(removed.status_code, 204)
        parcela.refresh_from_db()
        self.assertEqual(parcela.status, ParcelaBolsa.Status.ALOCADA)
        self.assertIsNone(parcela.lista_id)

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
