"""
Valida que o centro pode distribuir a totalidade do recurso mesmo com empenho.

Cenário:

* o centro recebe um crédito de 1.000,00;
* o centro reforça um empenho com 700,00 (300,00 ficam fora do empenho);
* o centro distribui 500,00 para a unidade A e 500,00 para a unidade B.

Como empenho e distribuição são dimensões independentes, a distribuição só é
limitada pelo total do centro (1.000,00), não pelo recurso fora do empenho
(300,00). Nada é gasto, então todos os saldos devem permanecer "livres":

* total do centro: 1.000,00
* saldo do empenho: 700,00
* saldo fora do empenho: 300,00
* saldo da unidade A: 500,00
* saldo da unidade B: 500,00
* gasto: 0,00

Todos os dados são criados em uma única transação e revertidos ao final.

Uso, a partir da pasta "backend":

    conda run -n ngo python manage.py validar_distribuicao_completa --settings=ngo_ccsh.dev_settings
"""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.crypto import get_random_string

from despesas import saldos, services
from despesas.models import (
    Empenho,
    ExercicioCentro,
    Finalidade,
    Natureza,
)
from entidades.models import (
    Centro,
    Pessoa,
    SituacaoUnidade,
    TipoUnidade,
    Unidade,
)
from usuarios.models import Usuario


class Command(BaseCommand):
    help = (
        "Valida que a distribuição integral para duas unidades é aceita mesmo "
        "com parte do recurso empenhada, sem persistir os dados de teste."
    )

    def handle(self, *args, **options):
        with transaction.atomic():
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    "Validação de distribuição com empenho (dados revertidos)"
                )
            )
            referencias = self._criar_referencias_de_teste()
            self._validar_distribuicao(**referencias)
            transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Distribuição validada: 500,00 para cada unidade com 700,00 "
                "empenhados e nenhum gasto. Os dados de teste foram revertidos."
            )
        )

    @staticmethod
    def _criar_referencias_de_teste():
        tipo_unidade = TipoUnidade.objects.order_by("id_tipo_unidade").first()
        situacao_unidade = SituacaoUnidade.objects.order_by(
            "id_situacao_unidade"
        ).first()
        if tipo_unidade is None or situacao_unidade is None:
            raise CommandError(
                "Não há tipo e situação de unidade disponíveis nas views do SIE. "
                "Verifique se as views v_sie_tipos_unidades e v_sie_situacoes_unidades "
                "estão acessíveis e possuem registros."
            )

        sufixo = get_random_string(8, allowed_chars="0123456789")
        cpf = get_random_string(11, allowed_chars="0123456789")
        codigo = f"TESTE{sufixo}"
        ano_fiscal = date.today().year

        pessoa = Pessoa.objects.create(
            nome_pessoa=f"Joselito {sufixo}",
            cpf=cpf,
            rg=f"RG{sufixo}",
        )
        usuario = Usuario.objects.create(
            cpf=cpf,
            email=f"distribuicao-{sufixo}@example.invalid",
            pessoa=pessoa,
        )
        centro = Centro.objects.create(
            nome_centro=f"CCSH ({sufixo})",
            sigla_centro=f"CCSH ({sufixo})",
            cod_estruturado=codigo,
        )
        unidade_a = Unidade.objects.create(
            nome_unidade=f"Curso de Administração ({sufixo})",
            cod_estruturado=f"{codigo}A",
            centro=centro,
            tipo_unidade=tipo_unidade,
            situacao_unidade=situacao_unidade,
        )
        unidade_b = Unidade.objects.create(
            nome_unidade=f"Curso de Direito ({sufixo})",
            cod_estruturado=f"{codigo}B",
            centro=centro,
            tipo_unidade=tipo_unidade,
            situacao_unidade=situacao_unidade,
        )
        natureza = Natureza.objects.create(nome=f"Natureza de validação {sufixo}")
        finalidade = Finalidade.objects.create(
            nome=f"Finalidade de validação {sufixo}",
            natureza=natureza,
        )
        empenho = Empenho.objects.create(
            numero_empenho=sufixo,
            centro=centro,
            ano_fiscal=ano_fiscal,
            natureza=natureza,
            finalidade=finalidade,
        )

        return {
            "ano_fiscal": ano_fiscal,
            "centro": centro,
            "empenho": empenho,
            "natureza": natureza,
            "sufixo": sufixo,
            "unidade_a": unidade_a,
            "unidade_b": unidade_b,
            "usuario": usuario,
        }

    def _validar_distribuicao(
        self,
        *,
        ano_fiscal,
        centro,
        empenho,
        natureza,
        sufixo,
        unidade_a,
        unidade_b,
        usuario,
    ):
        credito_inicial = Decimal("1000.00")
        valor_empenhado = Decimal("700.00")
        valor_distribuido = Decimal("500.00")
        valor_fora_do_empenho = credito_inicial - valor_empenhado

        ExercicioCentro.objects.create(
            centro=centro,
            ano_fiscal=ano_fiscal,
            status=ExercicioCentro.Status.ABERTO,
        )
        self.stdout.write(
            f"[1/4] Exercício {ano_fiscal} aberto para o centro {centro.sigla_centro}."
        )

        services.creditar(
            centro,
            ano_fiscal,
            natureza,
            credito_inicial,
            usuario,
            justificativa=f"Crédito inicial de validação {sufixo}",
        )
        self.stdout.write(f"[2/4] Crédito registrado: R$ {credito_inicial:.2f}.")

        services.reforcar_empenho(
            empenho,
            valor_empenhado,
            usuario,
            justificativa=f"Reserva de validação {sufixo}",
        )
        self.stdout.write(
            f"[3/4] Empenho reforçado: R$ {valor_empenhado:.2f}; "
            f"restam R$ {valor_fora_do_empenho:.2f} fora do empenho."
        )

        # A distribuição é limitada pelo total do centro, não pelo que está fora
        # do empenho. Duas distribuições de 500,00 somam 1.000,00 e devem passar.
        for unidade in (unidade_a, unidade_b):
            services.distribuir(
                centro,
                ano_fiscal,
                natureza,
                unidade,
                valor_distribuido,
                usuario,
                justificativa=f"Distribuição de validação {sufixo}",
            )
        self.stdout.write(
            f"[4/4] Distribuídos R$ {valor_distribuido:.2f} para cada unidade."
        )

        self._conferir(
            "saldo do centro",
            saldos.total_centro(centro, ano_fiscal, natureza),
            credito_inicial,
        )
        self._conferir(
            "saldo do empenho",
            saldos.saldo_empenho(empenho),
            valor_empenhado,
        )
        self._conferir(
            "saldo fora do empenho",
            saldos.livre_centro(centro, ano_fiscal, natureza),
            valor_fora_do_empenho,
        )
        self._conferir(
            "saldo da unidade A",
            saldos.saldo_unidade(unidade_a, ano_fiscal, natureza),
            valor_distribuido,
        )
        self._conferir(
            "saldo da unidade B",
            saldos.saldo_unidade(unidade_b, ano_fiscal, natureza),
            valor_distribuido,
        )
        self._conferir(
            "disponível da unidade A (sem bolsas alocadas)",
            saldos.disponivel_unidade(unidade_a, ano_fiscal, natureza),
            valor_distribuido,
        )
        self._conferir(
            "gasto do empenho (nada foi pago)",
            saldos.gasto_empenho(empenho),
            Decimal("0.00"),
        )

    @staticmethod
    def _conferir(descricao, valor_obtido, valor_esperado):
        if valor_obtido != valor_esperado:
            raise CommandError(
                f"Falha ao conferir {descricao}: esperado {valor_esperado!r}, "
                f"obtido {valor_obtido!r}."
            )
