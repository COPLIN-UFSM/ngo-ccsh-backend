"""Shared fixtures for ledger, scholarship, and exercise tests."""

from django.test import TestCase

from despesas import services
from despesas.models import Empenho, Finalidade, Natureza, TipoDocumento, TipoDocumentoParaFinalidade
from entidades.models import Cargo, Centro, Pessoa, PessoaSIE, Servidor, SituacaoUnidade, TipoUnidade, Unidade
from usuarios.models import Usuario


class BaseRazao(TestCase):
    def setUp(self):
        pessoa_usuario = Pessoa.objects.create(
            nome_pessoa="Ana", cpf="00000000001", rg="RG-ANA"
        )
        self.usuario = Usuario.objects.create(
            cpf=pessoa_usuario.cpf,
            email="ana@example.com",
            pessoa=pessoa_usuario,
        )
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
