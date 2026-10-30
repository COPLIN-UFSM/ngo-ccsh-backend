"""Tests for ledger balances and core spending rules."""

from decimal import Decimal as D

from django.core.exceptions import ValidationError

from despesas import saldos, services
from despesas.models import Finalidade, ImutavelError, Lancamento, Transacao
from despesas.services import SaldoInsuficiente
from despesas.tests.helpers import BaseRazao


class TestFluxoBasico(BaseRazao):
    def setUp(self):
        super().setUp()
        self.e1 = self.novo_empenho("001", self.bolsa2a)
        self.creditar(1000)
        services.reforcar_empenho(self.e1, 600, self.usuario)
        self.distribuir(self.A, 400)

    def test_baldes_derivados(self):
        c, n = self.centro, self.custeio
        self.assertEqual(saldos.total_centro(c, 2026, n), D("1000"))
        self.assertEqual(saldos.saldo_empenho(self.e1), D("600"))
        self.assertEqual(saldos.livre_centro(c, 2026, n), D("400"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, n), D("400"))
        self.assertEqual(saldos.nao_distribuido_centro(c, 2026, n), D("600"))

    def test_despesa_debita_as_duas_dimensoes(self):
        services.registrar_despesa(
            self.e1, self.A, self.bolsa2a, 100, self.usuario
        )
        c, n = self.centro, self.custeio
        self.assertEqual(self.e1.saldo, D("500"))
        self.assertEqual(self.e1.gasto, D("100"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, n), D("300"))
        self.assertEqual(saldos.total_centro(c, 2026, n), D("900"))
        # reforço e distribuição não mexem em dinheiro livre/distribuído do outro lado
        self.assertEqual(saldos.livre_centro(c, 2026, n), D("400"))
        self.assertEqual(saldos.nao_distribuido_centro(c, 2026, n), D("600"))

    def test_unidade_sem_saldo_nao_paga_e_nada_e_gravado(self):
        antes = (Lancamento.objects.count(), Transacao.objects.count())
        with self.assertRaises(SaldoInsuficiente):
            services.registrar_despesa(self.e1, self.A, self.bolsa2a, 401, self.usuario)
        self.assertEqual((Lancamento.objects.count(), Transacao.objects.count()), antes)

    def test_empenho_sem_saldo(self):
        with self.assertRaises(SaldoInsuficiente):
            services.registrar_despesa(self.e1, None, self.bolsa2a, 601, self.usuario)

    def test_nao_empenha_alem_do_recurso_livre(self):
        with self.assertRaises(SaldoInsuficiente):
            services.reforcar_empenho(self.e1, 401, self.usuario)

    def test_nao_distribui_alem_do_recurso_do_centro(self):
        with self.assertRaises(SaldoInsuficiente):
            self.distribuir(self.B, 601)

    def test_centro_paga_com_recurso_proprio(self):
        services.registrar_despesa(self.e1, None, self.bolsa2a, 100, self.usuario)
        self.assertEqual(saldos.nao_distribuido_centro(self.centro, 2026, self.custeio), D("500"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("400"))

    def test_transferir_e_recolher(self):
        services.transferir_entre_unidades(
            self.centro, 2026, self.custeio, self.A, self.B, 150, self.usuario
        )
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("250"))
        self.assertEqual(saldos.saldo_unidade(self.B, 2026, self.custeio), D("150"))
        services.recolher_de_unidade(
            self.centro, 2026, self.custeio, self.B, 150, self.usuario
        )
        self.assertEqual(saldos.nao_distribuido_centro(self.centro, 2026, self.custeio), D("750"))
        with self.assertRaises(SaldoInsuficiente):
            services.recolher_de_unidade(
                self.centro, 2026, self.custeio, self.B, 1, self.usuario
            )

    def test_debito_administrativo(self):
        obra_custeio = Finalidade.objects.create(nome="Reforma", natureza=self.custeio)
        e2 = self.novo_empenho("002", obra_custeio)
        services.reforcar_empenho(e2, 300, self.usuario)
        with self.assertRaises(ValidationError):  # sem justificativa
            services.registrar_despesa(
                e2, self.A, obra_custeio, 300, self.usuario, administrativo=True
            )
        with self.assertRaises(ValidationError):  # sem unidade
            services.registrar_despesa(
                e2, None, obra_custeio, 300, self.usuario,
                administrativo=True, justificativa="obra emergencial",
            )
        t = services.registrar_despesa(
            e2, self.A, obra_custeio, 300, self.usuario,
            administrativo=True, justificativa="obra emergencial",
        )
        self.assertEqual(t.operacao, Transacao.Operacao.DEBITO_ADMINISTRATIVO)
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("100"))

    def test_conversao_de_natureza(self):
        e_cap = self.novo_empenho("003", self.obra)
        services.converter_natureza(self.e1, e_cap, 200, self.usuario, unidade=self.A)
        self.assertEqual(self.e1.saldo, D("400"))
        self.assertEqual(e_cap.saldo, D("200"))
        self.assertEqual(saldos.total_centro(self.centro, 2026, self.custeio), D("800"))
        self.assertEqual(saldos.total_centro(self.centro, 2026, self.capital), D("200"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("200"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.capital), D("200"))
        with self.assertRaises(ValidationError):  # mesma natureza
            services.converter_natureza(self.e1, self.novo_empenho("004", self.bolsa2a), 10, self.usuario)

class TestImutabilidade(BaseRazao):
    def test_razao_nao_edita_nem_apaga(self):
        self.creditar(100)
        linha = Lancamento.objects.get()
        linha.montante = D("999")
        with self.assertRaises(ImutavelError):
            linha.save()
        with self.assertRaises(ImutavelError):
            linha.delete()
        with self.assertRaises(ImutavelError):
            Lancamento.objects.update(montante=1)
        with self.assertRaises(ImutavelError):
            Lancamento.objects.all().delete()
        self.assertEqual(Lancamento.objects.get().montante, D("100"))
