"""
Testes do razão, das bolsas e do fechamento de exercício.

Para rodar no projeto real, ajuste só ``BaseRazao.setUp`` (criação de Usuario,
TipoUnidade, SituacaoUnidade...), que aqui usa os campos mínimos.
"""

import datetime as dt
from decimal import Decimal as D

from django.core.exceptions import ValidationError
from django.test import TestCase

from entidades.models import (
    Cargo,
    Centro,
    Pessoa,
    PessoaSIE,
    Servidor,
    SituacaoUnidade,
    TipoUnidade,
    Unidade,
)
from usuarios.models import Usuario

from . import saldos, services
from .models import (
    Empenho,
    ExercicioCentro,
    Finalidade,
    ImutavelError,
    Lancamento,
    ListaSIAFI,
    Natureza,
    ParcelaBolsa,
    TipoDocumento,
    TipoDocumentoParaFinalidade,
    TipoMovimento,
    Transacao,
    VinculoBolsa,
)
from .services import (
    DEVOLVER,
    TRANSPORTAR,
    DestinoSaldo,
    ExercicioFechado,
    RegraDeNegocio,
    SaldoInsuficiente,
)

Codigo = TipoMovimento.Codigo


class BaseRazao(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(nome="ana")
        self.tipo_unidade = TipoUnidade.objects.create(tipo_unidade="Departamento")
        self.situacao = SituacaoUnidade.objects.create(situacao_unidade="Ativa")

        self.centro = Centro.objects.create(
            nome_centro="CCSH", sigla_centro="CCSH", cod_estruturado="11"
        )
        self.A = self.nova_unidade("A", "11.01")
        self.B = self.nova_unidade("B", "11.02")

        self.custeio = Natureza.objects.create(nome="Custeio")
        self.capital = Natureza.objects.create(nome="Capital")

        self.bolsa2a = Finalidade.objects.create(
            nome="Bolsa 2A", natureza=self.custeio, permite_transporte=True
        )
        self.passagens = Finalidade.objects.create(
            nome="Passagens", natureza=self.custeio, permite_transporte=False
        )
        self.obra = Finalidade.objects.create(nome="Obras", natureza=self.capital)

        self.nota_fiscal = TipoDocumento.objects.create(nome="Nota fiscal")
        self.trecho = TipoDocumento.objects.create(nome="Trecho")
        TipoDocumentoParaFinalidade.objects.create(
            tipo_documento=self.nota_fiscal, finalidade=self.passagens, obrigatorio=True
        )
        TipoDocumentoParaFinalidade.objects.create(
            tipo_documento=self.trecho, finalidade=self.passagens, obrigatorio=False
        )

    # -- fábricas ----------------------------------------------------------
    def nova_unidade(self, nome, codigo, pai=None, centro=None):
        return Unidade.objects.create(
            nome_unidade=nome,
            cod_estruturado=codigo,
            centro=centro or self.centro,
            unidade_pai=pai,
            tipo_unidade=self.tipo_unidade,
            situacao_unidade=self.situacao,
        )

    def novo_empenho(self, numero, finalidade, ano=2026, natureza=None, **kw):
        return Empenho.objects.create(
            numero_empenho=numero,
            centro=self.centro,
            ano_fiscal=ano,
            natureza=natureza or finalidade.natureza,
            finalidade=finalidade,
            **kw,
        )

    def creditar(self, valor, natureza=None, ano=2026):
        return services.creditar(
            self.centro, ano, natureza or self.custeio, valor, self.usuario
        )

    def distribuir(self, unidade, valor, natureza=None, ano=2026):
        return services.distribuir(
            self.centro, ano, natureza or self.custeio, unidade, valor, self.usuario
        )

    def bolsista(self, nome="Bia", cpf="1"):
        pessoa_sie = PessoaSIE.objects.create(nome_pessoa=nome, cpf=cpf, rg=cpf)
        pessoa = Pessoa.objects.create(
            pessoa_sie=pessoa_sie, nome_pessoa=nome, cpf=cpf, rg=cpf
        )
        cargo, _ = Cargo.objects.get_or_create(cargo="Professor")
        Servidor.objects.create(pessoa=pessoa, matricula=f"m{cpf}", cargo=cargo)
        return pessoa


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
