from django.apps import apps
from django.db import connection

from django.core.management import call_command
from django.core.management.base import BaseCommand

from despesas.models import Transacao, Empenho, Finalidade, NaturezaFinalidade, TipoFinalidade, TipoDocumento, \
    VersaoTransacao, StatusTransacao
from entidades.models import Unidade, Centro, SituacaoUnidade, TipoUnidade, PessoaSIE, Pessoa
from usuarios.models import Usuario


class Command(BaseCommand):
    help = "Test model integrity"

    def handle(self, *args, **options):
        # Create the schema in the transient SQLite database.
        call_command(
            "migrate",
            interactive=False,
            verbosity=0,
            run_syncdb=True,
        )

        self.stdout.write("Database schema initialized.")

        self.__create_unmanaged_tables__()
        self.__create_base_data__()
        self.test_models()

    def __create_unmanaged_tables__(self):
        for model in apps.get_models():
            if model._meta.managed:
                continue

            original = model._meta.managed
            model._meta.managed = True

            try:
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(model)

                self.stdout.write(self.style.SUCCESS(f"  [OK] {model._meta.db_table}"))
            except AttributeError as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERRO] {model._meta.db_table}: {e}")
                )
            finally:
                model._meta.managed = original

    @staticmethod
    def __create_base_data__():
        henry_sie = PessoaSIE.objects.create(
            nome_pessoa="Henry",
            cpf="00000000001",
            rg="00000000001"
        )
        henry_pessoa = Pessoa.objects.create(
            pessoa_sie=henry_sie,
            nome_pessoa=henry_sie.nome_pessoa,
            cpf=henry_sie.cpf,
            rg=henry_sie.rg
        )
        henry_usuario = Usuario.objects.create(
            cpf=henry_sie.cpf,
            email="henry@example.com",
            ativo=True,
            pessoa=henry_pessoa
        )
        tipo_documento_descricao = TipoDocumento.objects.create(
            tipo_documento="Descrição"
        )
        custeio = NaturezaFinalidade.objects.create(
            natureza_finalidade="Custeio"
        )
        credito = TipoFinalidade.objects.create(
            tipo_finalidade="Crédito",
        )
        debito = TipoFinalidade.objects.create(
            tipo_finalidade="Débito",
        )
        transferencia = TipoFinalidade.objects.create(
            tipo_finalidade="Transferência"
        )
        bolsa_2a = Finalidade.objects.create(
            finalidade="Bolsa 2A",
            natureza_finalidade=custeio,
            tipo_finalidade=debito,
        )
        bolsa_2a.tipos_documentos.add(
            tipo_documento_descricao,
            through_defaults={
                "obrigatorio": False,
                "ativo": True,
            },
        )
        finalidade_aporte_recursos = Finalidade.objects.create(
            finalidade="Aporte de Recursos",
            natureza_finalidade=custeio,
            tipo_finalidade=credito,
        )

        ccsh = Centro.objects.create(
            nome_centro="Centro de Ciências Sociais e Humanas",
            sigla_centro="CCSH",
            cod_estruturado="001",
        )
        situacao_ativo = SituacaoUnidade.objects.create(
            situacao_unidade="Ativo",
        )
        tipo_unidade_orcamentaria = TipoUnidade.objects.create(
            tipo_unidade="Unidade Orçamentária",
        )
        ngo = Unidade.objects.create(
            nome_unidade="Núcleo de Gestão Orçamentária",
            cod_estruturado="002",
            centro=ccsh,
            tipo_unidade=tipo_unidade_orcamentaria,
            situacao_unidade=situacao_ativo,
            pode_empenhar=True
        )
        status = StatusTransacao.objects.create(
            status_transacao="Pago"
        )

        models = [
            tipo_documento_descricao, custeio, credito, debito, transferencia, bolsa_2a, ngo, henry_usuario,
            status, finalidade_aporte_recursos
        ]
        for model in models:
            model.save()

    def test_models(self):
        print("Testando criação de modelos no banco de dados")

        finalidade_bolsa = Finalidade.objects.get(
            finalidade="Bolsa 2A"
        )
        finalidade_aporte = Finalidade.objects.get(
            finalidade="Aporte de Recursos"
        )

        # cria o empenho inicial
        empenho = Empenho.objects.create(
            numero_empenho="1",
            numero_pen="1",
            finalidade=finalidade_bolsa,
        )

        # cria a transação sem versão
        transacao_aporte = Transacao.objects.create()

        # cria a primeira versão
        v_transacao_aporte = VersaoTransacao.objects.create(
            transacao=transacao_aporte,
            numero_versao=1,
            empenho=empenho,
            finalidade=finalidade_aporte,
            unidade_executora=Unidade.objects.get(
                nome_unidade="Núcleo de Gestão Orçamentária"
            ),
            usuario=Usuario.objects.get(
                pessoa=Pessoa.objects.get(cpf="00000000001")
            ),
            status_pagamento=StatusTransacao.objects.get(
                status_transacao="Pago"
            ),
            montante=1000
        )
        # conecta os dois
        transacao_aporte.versao_transacao = v_transacao_aporte
        transacao_aporte.save(update_fields=["versao_transacao"])

        print(f'Orçamento do empenho: {empenho.orcamento}')
        print(f'Gasto do empenho: {empenho.gasto}')
        print(f'Saldo do empenho: {empenho.saldo}')
        print('----------------------------------')


        # cria a transação sem versão
        transacao_gasto_bolsa = Transacao.objects.create()

        # cria a primeira versão
        v_transacao_gasto_bolsa = VersaoTransacao.objects.create(
            transacao=transacao_gasto_bolsa,
            numero_versao=1,
            empenho=empenho,
            finalidade=finalidade_bolsa,
            unidade_executora=Unidade.objects.get(
                nome_unidade="Núcleo de Gestão Orçamentária"
            ),
            usuario=Usuario.objects.get(
                pessoa=Pessoa.objects.get(cpf="00000000001")
            ),
            status_pagamento=StatusTransacao.objects.get(
                status_transacao="Pago"
            ),
            montante=700
        )
        # conecta os dois
        transacao_gasto_bolsa.versao_transacao = v_transacao_gasto_bolsa
        transacao_gasto_bolsa.save(update_fields=["versao_transacao"])

        print(f'Orçamento do empenho: {empenho.orcamento}')
        print(f'Gasto do empenho: {empenho.gasto}')
        print(f'Saldo do empenho: {empenho.saldo}')
