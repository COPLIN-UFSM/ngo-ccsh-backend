"""Tests for catalog and accounting validation rules."""

import datetime as dt
from decimal import Decimal as D

from django.core.exceptions import ValidationError

from despesas import services
from despesas.models import Lancamento, TipoDocumento, TipoMovimento, Transacao
from despesas.tests.helpers import BaseRazao
from entidades.models import Centro, Pessoa

Codigo = TipoMovimento.Codigo


class TestRegrasDoCatalogo(BaseRazao):
    def test_empenho_precisa_ter_natureza_da_finalidade(self):
        with self.assertRaises(ValidationError):
            self.novo_empenho("001", self.bolsa2a, natureza=self.capital)

    def test_nao_paga_natureza_com_recurso_de_outra(self):
        e1 = self.novo_empenho("001", self.bolsa2a)
        self.creditar(100)
        services.reforcar_empenho(e1, 100, self.usuario)
        with self.assertRaises(ValidationError):
            services.registrar_despesa(e1, None, self.obra, 10, self.usuario)

    def test_empenho_pode_pagar_outra_finalidade_da_mesma_natureza(self):
        e1 = self.novo_empenho("001", self.bolsa2a)
        self.creditar(100)
        services.reforcar_empenho(e1, 100, self.usuario)
        services.registrar_despesa(
            e1, None, self.passagens, 10, self.usuario, documentos=[(self.nota_fiscal, "NF-1")]
        )
        self.assertEqual(e1.saldo, D("90"))

    def test_toda_despesa_precisa_de_empenho(self):
        self.creditar(100)
        t = Transacao.objects.create(
            operacao="despesa", data=dt.date(2026, 1, 1), usuario=self.usuario
        )
        with self.assertRaises(ValidationError):
            Lancamento.objects.create(
                transacao=t,
                tipo_movimento=TipoMovimento.obter(Codigo.PAGAMENTO),
                centro=self.centro,
                ano_fiscal=2026,
                natureza=self.custeio,
                montante=D("-10"),
            )

    def test_ano_do_lancamento_precisa_ser_o_do_empenho(self):
        e1 = self.novo_empenho("001", self.bolsa2a)
        t = Transacao.objects.create(
            operacao="reforco", data=dt.date(2026, 1, 1), usuario=self.usuario
        )
        with self.assertRaises(ValidationError):
            Lancamento.objects.create(
                transacao=t,
                tipo_movimento=TipoMovimento.obter(Codigo.REFORCO_EMPENHO),
                centro=self.centro,
                ano_fiscal=2027,
                natureza=self.custeio,
                empenho=e1,
                montante=D("10"),
            )

    def test_hierarquia_de_unidades(self):
        sub = self.nova_unidade("A1", "11.01.01", pai=self.A)
        self.assertEqual(sub.ancestrais(), [self.A])
        self.assertEqual(list(self.A.subunidades.all()), [sub])
        outro = Centro.objects.create(nome_centro="CT", sigla_centro="CT", cod_estruturado="12")
        with self.assertRaises(ValidationError):
            self.nova_unidade("X", "12.01", pai=self.A, centro=outro)

    def test_beneficiario_pode_ser_pessoa_externa(self):
        externa = Pessoa.objects.create(nome_pessoa="Zé", cpf="9", rg="9")
        self.assertTrue(externa.externa)
        e1 = self.novo_empenho("001", self.passagens)
        self.creditar(100)
        services.reforcar_empenho(e1, 100, self.usuario)
        t = services.registrar_despesa(
            e1, None, self.passagens, 50, self.usuario,
            beneficiario=externa,
            documentos=[(self.nota_fiscal, "NF-1"), (self.trecho, "SMA-POA"), (self.trecho, "POA-SMA")],
        )
        self.assertEqual(t.beneficiario, externa)
        self.assertEqual(
            list(t.documentos.filter(tipo_documento=self.trecho).values_list("ordem", "valor")),
            [(0, "SMA-POA"), (1, "POA-SMA")],
        )

    def test_documento_de_outra_finalidade_e_obrigatorios(self):
        e1 = self.novo_empenho("001", self.passagens)
        self.creditar(100)
        services.reforcar_empenho(e1, 100, self.usuario)
        with self.assertRaises(ValidationError):  # falta a nota fiscal
            services.registrar_despesa(e1, None, self.passagens, 10, self.usuario)
        with self.assertRaises(ValidationError):  # campo não aceito na finalidade
            services.registrar_despesa(
                e1, None, self.bolsa2a, 10, self.usuario, documentos=[(self.trecho, "x")]
            )

    def test_tipo_dado_do_documento(self):
        data = TipoDocumento.objects.create(nome="Data da viagem", tipo_dado="data")
        self.assertEqual(data.validar_valor("2026-03-01"), "2026-03-01")
        with self.assertRaises(ValidationError):
            data.validar_valor("01/03/2026")
