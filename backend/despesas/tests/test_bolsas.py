"""Tests for scholarship allocations and SIAFI payment lists."""

import datetime as dt
from decimal import Decimal as D

from django.core.exceptions import ValidationError

from despesas import saldos, services
from despesas.models import Empenho, Finalidade, ListaSIAFI, ParcelaBolsa, Transacao, VinculoBolsa
from despesas.services import RegraDeNegocio, SaldoInsuficiente
from despesas.tests.helpers import BaseRazao
from entidades.models import Pessoa, PessoaSIE


class TestBolsas(BaseRazao):
    def setUp(self):
        super().setUp()
        self.e1 = self.novo_empenho("001", self.bolsa2a)
        self.bia = self.bolsista()
        self.creditar(1000)
        services.reforcar_empenho(self.e1, 300, self.usuario)
        self.distribuir(self.A, 600)
        self.vinculo = VinculoBolsa.objects.create(
            bolsista=self.bia,
            unidade=self.A,
            finalidade=self.bolsa2a,
            valor_mensal=D("100"),
            inicio=dt.date(2026, 7, 1),
            fim=dt.date(2027, 6, 30),
        )

    def parcelas(self, ano):
        return list(self.vinculo.parcelas.filter(ano_fiscal=ano).order_by("competencia"))

    def test_so_pessoas_do_sie_sao_bolsistas(self):
        externa = Pessoa.objects.create(nome_pessoa="Zé", cpf="9", rg="9")
        with self.assertRaises(ValidationError):
            VinculoBolsa.objects.create(
                bolsista=externa, unidade=self.A, finalidade=self.bolsa2a,
                valor_mensal=D("100"), inicio=dt.date(2026, 1, 1), fim=dt.date(2026, 12, 1),
            )
        sem_vinculo = Pessoa.objects.create(
            pessoa_sie=PessoaSIE.objects.create(nome_pessoa="Cid", cpf="8", rg="8"),
            nome_pessoa="Cid", cpf="8", rg="8",
        )
        with self.assertRaises(ValidationError):
            VinculoBolsa.objects.create(
                bolsista=sem_vinculo, unidade=self.A, finalidade=self.bolsa2a,
                valor_mensal=D("100"), inicio=dt.date(2026, 1, 1), fim=dt.date(2026, 12, 1),
            )

    def test_parcelas_atravessam_o_ano_fiscal(self):
        criadas = services.gerar_parcelas(self.vinculo)
        self.assertEqual(len(criadas), 12)
        self.assertEqual(len(self.parcelas(2026)), 6)
        self.assertEqual(len(self.parcelas(2027)), 6)
        self.assertEqual(services.gerar_parcelas(self.vinculo), [])  # idempotente

    def test_alocar_nao_empenha_e_ano_futuro_fica_previsto(self):
        services.gerar_parcelas(self.vinculo)
        for p in self.parcelas(2026):
            services.alocar_parcela(p, empenho_previsto=self.e1)

        n = self.custeio
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, n), D("600"))  # razão intacto
        self.assertEqual(saldos.alocado_unidade(self.A, 2026, n), D("600"))
        self.assertEqual(saldos.disponivel_unidade(self.A, 2026, n), D("0"))
        self.assertEqual(self.e1.saldo, D("300"))  # empenho não mudou (alocar != empenhar)

        # 2027 ainda não tem orçamento: continua prevista, sem reserva
        p27 = self.parcelas(2027)[0]
        with self.assertRaises(SaldoInsuficiente):
            services.alocar_parcela(p27)
        p27.refresh_from_db()
        self.assertEqual(p27.status, ParcelaBolsa.Status.PREVISTA)
        self.assertEqual(saldos.compromisso_futuro(self.centro), {2027: D("600")})

        # alerta de complemento do empenho: 600 alocados para sair de 300 empenhados
        self.assertEqual(saldos.previsto_empenho(self.e1), D("600"))
        self.assertEqual(saldos.a_complementar(self.e1), D("300"))
        services.reforcar_empenho(self.e1, 300, self.usuario)
        self.assertEqual(saldos.a_complementar(self.e1), D("0"))

        # chegou o orçamento de 2027: agora dá para alocar
        services.creditar(self.centro, 2027, self.custeio, 1000, self.usuario)
        services.distribuir(self.centro, 2027, self.custeio, self.A, 1000, self.usuario)
        services.alocar_parcela(p27)
        self.assertEqual(saldos.compromisso_futuro(self.centro), {2027: D("500")})

    def test_cancelar_libera_a_reserva(self):
        services.gerar_parcelas(self.vinculo)
        p = self.parcelas(2026)[0]
        services.alocar_parcela(p, self.e1)
        self.assertEqual(saldos.disponivel_unidade(self.A, 2026, self.custeio), D("500"))
        services.cancelar_parcela(p)
        self.assertEqual(saldos.disponivel_unidade(self.A, 2026, self.custeio), D("600"))

    def test_debito_administrativo_so_pega_o_disponivel(self):
        services.gerar_parcelas(self.vinculo)
        for p in self.parcelas(2026)[:5]:  # 500 alocados, 100 disponível
            services.alocar_parcela(p, self.e1)
        obra = Finalidade.objects.create(nome="Reforma", natureza=self.custeio)
        e2 = self.novo_empenho("002", obra)
        services.reforcar_empenho(e2, 400, self.usuario)
        with self.assertRaises(SaldoInsuficiente):
            services.registrar_despesa(
                e2, self.A, obra, 101, self.usuario,
                administrativo=True, justificativa="subunidade parada",
            )
        services.registrar_despesa(
            e2, self.A, obra, 100, self.usuario,
            administrativo=True, justificativa="subunidade parada",
        )

    def test_pagar_lista(self):
        services.gerar_parcelas(self.vinculo)
        for p in self.parcelas(2026):
            services.alocar_parcela(p, self.e1)
        jul = self.parcelas(2026)[0]
        lista = services.criar_lista(self.centro, dt.date(2026, 7, 15))
        self.assertEqual(lista.competencia, dt.date(2026, 7, 1))
        services.incluir_parcelas(lista, [jul])

        with self.assertRaises(ValidationError):  # número do SIAFI é obrigatório
            services.pagar_lista(lista, self.usuario, "  ")

        disponivel_antes = saldos.disponivel_unidade(self.A, 2026, self.custeio)
        t = services.pagar_lista(lista, self.usuario, "2026LS000123")
        lista.refresh_from_db()
        jul.refresh_from_db()
        self.assertEqual(lista.status, ListaSIAFI.Status.PAGA)
        self.assertEqual(lista.transacao, t)
        self.assertEqual(t.operacao, Transacao.Operacao.LISTA_SIAFI)
        self.assertEqual(jul.status, ParcelaBolsa.Status.PAGA)
        self.assertEqual(self.e1.saldo, D("200"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("500"))
        self.assertEqual(saldos.alocado_unidade(self.A, 2026, self.custeio), D("500"))
        # pagar o que já estava alocado não muda o disponível
        self.assertEqual(
            saldos.disponivel_unidade(self.A, 2026, self.custeio), disponivel_antes
        )
        self.assertEqual(t.lancamentos.get().finalidade, self.bolsa2a)
        with self.assertRaises(RegraDeNegocio):
            services.pagar_lista(lista, self.usuario, "outra")

    def test_lista_completada_com_outro_empenho_no_fim_do_ano(self):
        monitoria = Finalidade.objects.create(nome="Bolsa Monitoria", natureza=self.custeio)
        e2 = self.novo_empenho("002", monitoria)
        services.reforcar_empenho(e2, 50, self.usuario)
        services.gerar_parcelas(self.vinculo)
        ago = self.parcelas(2026)[1]
        services.alocar_parcela(ago, self.e1)
        lista = services.criar_lista(self.centro, dt.date(2026, 8, 1))
        (item,) = services.incluir_parcelas(lista, [ago])

        with self.assertRaises(ValidationError):  # partes não somam o item
            services.pagar_lista(
                lista, self.usuario, "L1", divisoes={item.pk: [(self.e1, D("60")), (e2, D("30"))]}
            )
        services.pagar_lista(
            lista, self.usuario, "L1", divisoes={item.pk: [(self.e1, D("60")), (e2, D("40"))]}
        )
        self.assertEqual(self.e1.saldo, D("240"))
        self.assertEqual(e2.saldo, D("10"))
        self.assertEqual(saldos.saldo_unidade(self.A, 2026, self.custeio), D("500"))

    def test_lista_sem_saldo_no_empenho_nao_grava_nada(self):
        services.gerar_parcelas(self.vinculo)
        p = self.parcelas(2026)[0]
        pobre = self.novo_empenho("009", self.bolsa2a)
        services.reforcar_empenho(pobre, 50, self.usuario)
        services.alocar_parcela(p, pobre)
        lista = services.criar_lista(self.centro, dt.date(2026, 7, 1))
        services.incluir_parcelas(lista, [p])
        with self.assertRaises(SaldoInsuficiente):
            services.pagar_lista(lista, self.usuario, "L9")
        p.refresh_from_db()
        lista.refresh_from_db()
        self.assertEqual(p.status, ParcelaBolsa.Status.ALOCADA)
        self.assertEqual(lista.status, ListaSIAFI.Status.RASCUNHO)
        self.assertEqual(pobre.saldo, D("50"))

    def test_parcela_so_entra_em_lista_da_sua_competencia(self):
        services.gerar_parcelas(self.vinculo)
        ago = self.parcelas(2026)[1]
        services.alocar_parcela(ago, self.e1)
        lista = services.criar_lista(self.centro, dt.date(2026, 7, 1))
        with self.assertRaises(ValidationError):
            services.incluir_parcelas(lista, [ago])
        prevista = self.parcelas(2026)[2]
        with self.assertRaises(RegraDeNegocio):
            services.incluir_parcelas(services.criar_lista(self.centro, dt.date(2026, 9, 1)), [prevista])
