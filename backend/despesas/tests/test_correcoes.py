"""Tests for immutable transaction corrections."""

import datetime as dt
from decimal import Decimal as D

from django.core.exceptions import ValidationError

from despesas import saldos, services
from despesas.models import Lancamento, Transacao
from despesas.services import RegraDeNegocio, SaldoInsuficiente
from despesas.tests.helpers import BaseRazao


class TestCorrecoes(BaseRazao):
    def setUp(self):
        super().setUp()
        self.e1 = self.novo_empenho("001", self.passagens)
        self.creditar(1000)
        services.reforcar_empenho(self.e1, 1000, self.usuario)
        self.distribuir(self.A, 1000)

    def test_estimada_depois_definitiva(self):
        # diárias: registra já o compromisso, sem nota fiscal
        t = services.registrar_despesa(
            self.e1, self.A, self.passagens, 200, self.usuario, estimada=True
        )
        self.assertEqual(self.e1.saldo, D("800"))

        # chegaram as notas: troca o valor e fecha a estimativa (sem justificativa)
        t2 = services.corrigir_transacao(
            t,
            self.usuario,
            linhas=[l.com(montante=D("-150")) for l in services.linhas_vigentes(t)],
            documentos=[(self.nota_fiscal, "NF-1")],
            estimada=False,
        )
        self.assertEqual(self.e1.saldo, D("850"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("850"))
        self.assertEqual(t2.corrige, t)
        self.assertFalse(t2.estimada)
        self.assertEqual(services.transacao_vigente(t), t2)
        self.assertEqual(t2.lancamentos.count(), 2)  # estorno + nova linha
        self.assertEqual(t2.lancamentos_vigentes().get().montante, D("-150"))
        self.assertEqual(t2.documentos.get().valor, "NF-1")
        # histórico: a original continua intacta
        self.assertEqual(t.lancamentos.get().montante, D("-200"))
        # gasto só conta o vigente
        self.assertEqual(self.e1.gasto, D("150"))

    def test_corrigir_definitiva_exige_justificativa_e_documentos(self):
        t = services.registrar_despesa(
            self.e1, self.A, self.passagens, 100, self.usuario,
            documentos=[(self.nota_fiscal, "NF-1")],
        )
        novas = [l.com(montante=D("-120")) for l in services.linhas_vigentes(t)]
        with self.assertRaises(ValidationError):
            services.corrigir_transacao(t, self.usuario, linhas=novas)
        t2 = services.corrigir_transacao(
            t, self.usuario, linhas=novas, justificativa="valor digitado errado"
        )
        self.assertEqual(t2.documentos.get().valor, "NF-1")  # documentos copiados
        self.assertEqual(self.e1.saldo, D("880"))
        # só a mais recente da cadeia pode ser corrigida
        with self.assertRaises(RegraDeNegocio):
            services.corrigir_transacao(t, self.usuario, justificativa="de novo")
        t3 = services.corrigir_transacao(
            t2, self.usuario, data=dt.date(2026, 5, 2), justificativa="data errada"
        )
        self.assertEqual(t3.data, dt.date(2026, 5, 2))
        self.assertEqual(self.e1.saldo, D("880"))
        self.assertEqual(services.transacao_vigente(t), t3)

    def test_cancelar_e_o_mesmo_que_corrigir_sem_linhas(self):
        t = services.registrar_despesa(
            self.e1, self.A, self.passagens, 100, self.usuario, estimada=True
        )
        services.corrigir_transacao(t, self.usuario, linhas=[])
        self.assertEqual(self.e1.saldo, D("1000"))

    def test_correcao_nao_pode_deixar_saldo_negativo(self):
        t = services.registrar_despesa(
            self.e1, self.A, self.passagens, 100, self.usuario, estimada=True
        )
        antes = Lancamento.objects.count()
        with self.assertRaises(SaldoInsuficiente):
            services.corrigir_transacao(
                t, self.usuario,
                linhas=[l.com(montante=D("-1001")) for l in services.linhas_vigentes(t)],
            )
        self.assertEqual(Lancamento.objects.count(), antes)

    def test_transacao_de_estimada_pode_ser_corrigida_varias_vezes(self):
        t = services.registrar_despesa(
            self.e1, self.A, self.passagens, 100, self.usuario, estimada=True
        )
        t2 = services.corrigir_transacao(
            t, self.usuario, estimada=True,
            linhas=[l.com(montante=D("-130")) for l in services.linhas_vigentes(t)],
        )
        self.assertTrue(t2.estimada)
        self.assertEqual(self.e1.saldo, D("870"))
