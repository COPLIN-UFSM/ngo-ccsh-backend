"""Tests for fiscal exercise closing and reopening."""

import datetime as dt
from decimal import Decimal as D

from django.core.exceptions import ValidationError

from despesas import saldos, services
from despesas.models import Empenho, ExercicioCentro, Lancamento, Transacao, VinculoBolsa
from despesas.services import DEVOLVER, TRANSPORTAR, DestinoSaldo, ExercicioFechado, RegraDeNegocio, SaldoInsuficiente
from despesas.tests.helpers import BaseRazao


class TestFechamento(BaseRazao):
    def setUp(self):
        super().setUp()
        self.e1 = self.novo_empenho("001", self.bolsa2a)  # permite transporte
        self.e2 = self.novo_empenho("002", self.passagens)  # não permite
        self.creditar(1000)
        services.reforcar_empenho(self.e1, 600, self.usuario)
        services.reforcar_empenho(self.e2, 400, self.usuario)
        self.distribuir(self.A, 700)
        self.distribuir(self.B, 300)
        services.registrar_despesa(self.e1, self.A, self.bolsa2a, 100, self.usuario)
        # situação: E1=500, E2=400 | A=600, B=300 | total=900
        self.e1_2027 = self.novo_empenho("001", self.bolsa2a, ano=2027, empenho_origem=self.e1)

    def destinos_corretos(self):
        return [
            DestinoSaldo(TRANSPORTAR, D("500"), empenho=self.e1, unidade=self.A, novo_empenho=self.e1_2027),
            DestinoSaldo(DEVOLVER, D("100"), empenho=self.e2, unidade=self.A),
            DestinoSaldo(DEVOLVER, D("300"), empenho=self.e2, unidade=self.B),
        ]

    def test_empenho_so_herda_saldo_de_finalidade_que_permite(self):
        with self.assertRaises(ValidationError):
            self.novo_empenho("002", self.passagens, ano=2027, empenho_origem=self.e2)
        with self.assertRaises(ValidationError):  # ano errado
            self.novo_empenho("003", self.bolsa2a, ano=2028, empenho_origem=self.e1)

    def test_fechamento_incompleto_nao_grava_nada(self):
        antes = Lancamento.objects.count()
        incompletos = self.destinos_corretos()[:2]  # esqueceu o saldo de B
        with self.assertRaises(RegraDeNegocio):
            services.fechar_exercicio(self.centro, 2026, self.usuario, incompletos)
        self.assertEqual(Lancamento.objects.count(), antes)
        self.assertEqual(
            ExercicioCentro.objects.get(centro=self.centro, ano_fiscal=2026).status, "aberto"
        )
        pend = saldos.pendencias_fechamento(self.centro, 2026)
        self.assertFalse(pend["ok"])

    def test_nao_transporta_finalidade_que_nao_permite(self):
        e2_2027 = Empenho(
            numero_empenho="002", centro=self.centro, ano_fiscal=2027, natureza=self.custeio,
            finalidade=self.passagens, empenho_origem=self.e2,
        )
        with self.assertRaises(ValidationError):
            e2_2027.save()

    def test_fechar(self):
        t = services.fechar_exercicio(self.centro, 2026, self.usuario, self.destinos_corretos())
        self.assertTrue(saldos.pendencias_fechamento(self.centro, 2026)["ok"])
        exercicio = ExercicioCentro.objects.get(centro=self.centro, ano_fiscal=2026)
        self.assertEqual(exercicio.status, "fechado")
        self.assertEqual(exercicio.transacao_fechamento, t)

        # empenhos de 2026 zerados; saldo foi para o empenho de 2027
        self.assertEqual(self.e1.saldo, D("0"))
        self.assertEqual(self.e2.saldo, D("0"))
        self.assertEqual(self.e1_2027.saldo, D("500"))
        # devolver à PROPLAN é gasto; transportar não é
        self.assertEqual(self.e2.gasto, D("400"))
        self.assertEqual(self.e1.gasto, D("100"))
        # o dinheiro transportado reaparece no centro, não nas subunidades
        n = self.custeio
        self.assertEqual(saldos.total_centro(self.centro, 2027, n), D("500"))
        self.assertEqual(saldos.nao_distribuido_centro(self.centro, 2027, n), D("500"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2027, n), D("0"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, n), D("0"))
        self.assertEqual(saldos.saldo_unidade(self.B, 2026, n), D("0"))

        # ano fechado não aceita lançamentos nem correções
        with self.assertRaises(ExercicioFechado):
            self.creditar(10)
        despesa = Transacao.objects.filter(operacao="despesa").get()
        with self.assertRaises(ExercicioFechado):
            services.corrigir_transacao(despesa, self.usuario, justificativa="x", linhas=[])
        with self.assertRaises(ExercicioFechado):
            services.fechar_exercicio(self.centro, 2026, self.usuario, [])

    def test_reabrir_e_fechar_de_novo(self):
        services.fechar_exercicio(self.centro, 2026, self.usuario, self.destinos_corretos())
        with self.assertRaises(ValidationError):
            services.reabrir_exercicio(self.centro, 2026, self.usuario, " ")
        services.reabrir_exercicio(self.centro, 2026, self.usuario, "lançamento errado")
        self.assertEqual(self.e1.saldo, D("500"))
        self.assertEqual(self.e2.saldo, D("400"))
        self.assertEqual(self.e1_2027.saldo, D("0"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("600"))
        self.assertEqual(saldos.total_centro(self.centro, 2027, self.custeio), D("0"))
        self.assertEqual(
            ExercicioCentro.objects.get(centro=self.centro, ano_fiscal=2026).status, "aberto"
        )
        # corrige o que estava errado e fecha de novo
        despesa = Transacao.objects.filter(operacao="despesa").get()
        services.corrigir_transacao(
            despesa, self.usuario, justificativa="era 50",
            linhas=[l.com(montante=D("-50")) for l in services.linhas_vigentes(despesa)],
        )
        destinos = [
            DestinoSaldo(TRANSPORTAR, D("550"), empenho=self.e1, unidade=self.A, novo_empenho=self.e1_2027),
            DestinoSaldo(DEVOLVER, D("100"), empenho=self.e2, unidade=self.A),
            DestinoSaldo(DEVOLVER, D("300"), empenho=self.e2, unidade=self.B),
        ]
        services.fechar_exercicio(self.centro, 2026, self.usuario, destinos)
        self.assertEqual(self.e1_2027.saldo, D("550"))

    def test_nao_reabre_se_o_saldo_transportado_ja_foi_gasto(self):
        services.fechar_exercicio(self.centro, 2026, self.usuario, self.destinos_corretos())
        services.distribuir(self.centro, 2027, self.custeio, self.A, 500, self.usuario)
        services.registrar_despesa(self.e1_2027, self.A, self.bolsa2a, 100, self.usuario)
        antes = Lancamento.objects.count()
        with self.assertRaises(SaldoInsuficiente):
            services.reabrir_exercicio(self.centro, 2026, self.usuario, "tentativa")
        self.assertEqual(Lancamento.objects.count(), antes)
        self.assertEqual(
            ExercicioCentro.objects.get(centro=self.centro, ano_fiscal=2026).status, "fechado"
        )

    def test_nao_fecha_com_parcelas_alocadas(self):
        bia = self.bolsista()
        vinculo = VinculoBolsa.objects.create(
            bolsista=bia, unidade=self.A, finalidade=self.bolsa2a, valor_mensal=D("10"),
            inicio=dt.date(2026, 12, 1), fim=dt.date(2026, 12, 31),
        )
        services.gerar_parcelas(vinculo)
        services.alocar_parcela(vinculo.parcelas.get(), self.e1)
        with self.assertRaises(RegraDeNegocio):
            services.fechar_exercicio(self.centro, 2026, self.usuario, self.destinos_corretos())

    def test_recurso_nao_empenhado_tambem_precisa_de_destino(self):
        # crédito que nunca foi empenhado nem distribuído
        self.creditar(50)
        with self.assertRaises(RegraDeNegocio):
            services.fechar_exercicio(self.centro, 2026, self.usuario, self.destinos_corretos())
        extra = DestinoSaldo(DEVOLVER, D("50"), natureza=self.custeio)
        services.fechar_exercicio(
            self.centro, 2026, self.usuario, self.destinos_corretos() + [extra]
        )
        self.assertTrue(saldos.pendencias_fechamento(self.centro, 2026)["ok"])
