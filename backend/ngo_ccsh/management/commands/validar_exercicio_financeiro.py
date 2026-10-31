"""
Executa um cenário completo para validar os modelos e serviços de despesas.

O fluxo simula a abertura de um exercício, o recebimento de orçamento, a reserva
de recursos em um empenho, a distribuição de um saldo para uma unidade, o registro
de uma despesa e o fechamento do exercício com a devolução dos saldos restantes.

Todos os dados são criados em uma única transação e revertidos ao final.
Assim, o comando pode ser executado para validar um banco já preparado sem deixar
cadastros ou lançamentos de teste persistidos.

Uso, a partir da pasta "backend":

    conda run -n ngo python manage.py validar_exercicio_financeiro --settings=ngo_ccsh.dev_settings

O exercício usado é o ano corrente. A sigla e os códigos criados para o teste são
únicos em cada execução. O comando utiliza um tipo e uma situação de unidade já
disponíveis nas views do SIE; ele não tenta inserir dados nessas views.

O banco selecionado precisa estar preparado com os DDLs da aplicação e ter as
views do SIE acessíveis. Mesmo usando "dev_settings", que aponta para o SQLite
local persistente, nenhum dado do cenário permanece gravado.

O diagrama de estados do fluxo, com os valores usados e o destino de cada saldo,
está em "backend/diagramas/validar_exercicio_financeiro.md".
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
        "Valida a abertura, os créditos, a despesa e o fechamento de um exercício "
        "sem persistir os dados de teste."
    )

    def handle(self, *args, **options):
        """
        Roda o cenário de ponta a ponta e sempre desfaz os dados criados.

        "transaction.atomic" garante que o cenário seja indivisível: se qualquer
        passo ou conferência falhar, o banco volta ao estado anterior. No caminho de
        sucesso marcamos explicitamente a transação para rollback, pois a finalidade
        do comando é validar o modelo, não criar dados de exemplo permanentes.
        """
        with transaction.atomic():
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    "Validação do fluxo financeiro (os dados serão revertidos)"
                )
            )
            referencias = self._criar_referencias_de_teste()
            self._validar_ciclo_do_exercicio(**referencias)

            transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                "Fluxo validado: exercício aberto, créditos e despesa registrados, "
                "saldos conferidos e exercício fechado. Os dados de teste foram "
                "revertidos."
            )
        )

    @staticmethod
    def _criar_referencias_de_teste():
        """
        Cria as entidades internas necessárias para executar operações financeiras.

        Tipo e situação da unidade são lidos das views do SIE, que são externas e
        somente leitura.
        """
        tipo_unidade = TipoUnidade.objects.order_by("id_tipo_unidade").first()
        situacao_unidade = SituacaoUnidade.objects.order_by(
            "id_situacao_unidade"
        ).first()
        if tipo_unidade is None or situacao_unidade is None:
            raise CommandError(
                "Não há tipo e situação de unidade disponíveis nas views do SIE. "
                "Verifique se as views v_tipos_unidades e v_situacoes_unidades "
                "estão acessíveis e possuem registros."
            )

        # Os campos únicos recebem o mesmo sufixo aleatório para tornar o cenário
        # facilmente reconhecível e permitir repetições sem colisão de cadastro.
        sufixo = get_random_string(8, allowed_chars="0123456789")
        cpf = get_random_string(11, allowed_chars="0123456789")
        codigo = f"TESTE{sufixo}"
        ano_fiscal = date.today().year

        pessoa = Pessoa.objects.create(
            # nome_pessoa=f"Validação do fluxo {sufixo}",
            nome_pessoa=f"Joselito {sufixo}",
            cpf=cpf,
            rg=f"RG{sufixo}",
        )
        usuario = Usuario.objects.create(
            cpf=cpf,
            email=f"fluxo-{sufixo}@example.invalid",
            pessoa=pessoa,
        )
        centro = Centro.objects.create(
            nome_centro=f"CCSH ({sufixo})",
            sigla_centro=f"CCSH ({sufixo})",
            cod_estruturado=codigo,
        )
        unidade = Unidade.objects.create(
            nome_unidade=f"Curso de Administração ({sufixo})",
            cod_estruturado=codigo,
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
            "finalidade": finalidade,
            "natureza": natureza,
            "sufixo": sufixo,
            "unidade": unidade,
            "usuario": usuario,
        }

    def _validar_ciclo_do_exercicio(
        self,
        *,
        ano_fiscal,
        centro,
        empenho,
        finalidade,
        natureza,
        sufixo,
        unidade,
        usuario,
    ):
        """
        Percorre e confere cada etapa da movimentação financeira.

        Valores usados no exemplo:

        * crédito inicial: 1.000,00;
        * reforço do empenho: 700,00;
        * distribuição para a unidade: 500,00;
        * despesa paga pela unidade: 200,00.

        Antes do fechamento, portanto, restam 800,00 no total do centro, 500,00 no
        empenho e 300,00 na unidade. O fechamento devolve esses três saldos sem
        contar duas vezes o mesmo dinheiro: 300,00 debitam empenho e unidade juntos,
        200,00 debitam apenas o empenho e 300,00 debitam apenas o centro.
        """
        credito_inicial = Decimal("1000.00")
        valor_empenhado = Decimal("700.00")
        valor_distribuido = Decimal("500.00")
        valor_despesa = Decimal("200.00")

        # 1. A abertura é explícita: o centro passa a ter um exercício em estado
        # aberto antes de aceitar qualquer lançamento financeiro.
        exercicio = ExercicioCentro.objects.create(
            centro=centro,
            ano_fiscal=ano_fiscal,
            status=ExercicioCentro.Status.ABERTO,
        )
        self.stdout.write(
            f"[1/6] Exercício {ano_fiscal} aberto para o centro {centro.sigla_centro}."
        )

        # 2. O crédito aumenta o total do centro. Nesta altura ainda não há saldo
        # reservado no empenho nem distribuído à unidade.
        services.creditar(
            centro,
            ano_fiscal,
            natureza,
            credito_inicial,
            usuario,
            justificativa=f"Crédito inicial de validação {sufixo}",
        )
        self._conferir(
            "total após o crédito",
            saldos.total_centro(centro, ano_fiscal, natureza),
            credito_inicial,
        )
        self._conferir(
            "saldo livre do centro após o crédito",
            saldos.livre_centro(centro, ano_fiscal, natureza),
            credito_inicial,
        )
        self.stdout.write(
            f"[2/6] Crédito registrado: R$ {credito_inicial:.2f}."
        )

        # 3. O reforço reserva parte do recurso livre para o empenho; não altera o
        # total recebido pelo centro.
        services.reforcar_empenho(
            empenho,
            valor_empenhado,
            usuario,
            justificativa=f"Reserva de validação {sufixo}",
        )
        self._conferir(
            "saldo do empenho após o reforço",
            saldos.saldo_empenho(empenho),
            valor_empenhado,
        )
        self._conferir(
            "recurso livre após o reforço",
            saldos.livre_centro(centro, ano_fiscal, natureza),
            credito_inicial - valor_empenhado,
        )
        self.stdout.write(
            f"[3/6] Empenho reforçado: R$ {valor_empenhado:.2f}; "
            f"restam R$ {credito_inicial - valor_empenhado:.2f} livres no centro."
        )

        # 4. A distribuição entrega saldo à unidade como um cheque contábil. O
        # lançamento não altera o total do centro nem o saldo do empenho.
        services.distribuir(
            centro,
            ano_fiscal,
            natureza,
            unidade,
            valor_distribuido,
            usuario,
            justificativa=f"Distribuição de validação {sufixo}",
        )
        self._conferir(
            "saldo da unidade após a distribuição",
            saldos.saldo_unidade(unidade, ano_fiscal, natureza),
            valor_distribuido,
        )
        self._conferir(
            "recurso não distribuído após a distribuição",
            saldos.nao_distribuido_centro(centro, ano_fiscal, natureza),
            credito_inicial - valor_distribuido,
        )
        self.stdout.write(f"[4/6] Distribuídos R$ {valor_distribuido:.2f} para {unidade.nome_unidade}.")

        # 5. A despesa debita simultaneamente o empenho, a unidade e o total do
        # centro. Isso demonstra o uso conjunto das duas dimensões do razão.
        services.registrar_despesa(
            empenho,
            unidade,
            finalidade,
            valor_despesa,
            usuario,
            justificativa=f"Despesa de validação {sufixo}",
        )
        total_restante = credito_inicial - valor_despesa
        empenho_restante = valor_empenhado - valor_despesa
        unidade_restante = valor_distribuido - valor_despesa
        self._conferir(
            "total do centro após a despesa",
            saldos.total_centro(centro, ano_fiscal, natureza),
            total_restante,
        )
        self._conferir(
            "saldo do empenho após a despesa",
            saldos.saldo_empenho(empenho),
            empenho_restante,
        )
        self._conferir(
            "saldo da unidade após a despesa",
            saldos.saldo_unidade(unidade, ano_fiscal, natureza),
            unidade_restante,
        )
        self.stdout.write(
            f"[5/6] Despesa de R$ {valor_despesa:.2f} registrada. "
            f"Saldos antes do fechamento: centro R$ {total_restante:.2f}, "
            f"empenho R$ {empenho_restante:.2f}, unidade R$ {unidade_restante:.2f}."
        )

        # 6. Para fechar, cada saldo precisa ter um destino. O primeiro lançamento
        # zera em conjunto o empenho e a unidade; os outros dois zeram cada saldo
        # restante sem atribuir duas vezes a mesma parcela do total.
        destinos = [
            services.DestinoSaldo(
                acao=services.DEVOLVER,
                montante=unidade_restante,
                empenho=empenho,
                unidade=unidade,
            ),
            services.DestinoSaldo(
                acao=services.DEVOLVER,
                montante=empenho_restante - unidade_restante,
                empenho=empenho,
            ),
            services.DestinoSaldo(
                acao=services.DEVOLVER,
                montante=total_restante - empenho_restante,
                natureza=natureza,
            ),
        ]
        fechamento = services.fechar_exercicio(
            centro,
            ano_fiscal,
            usuario,
            destinos,
        )

        pendencias = saldos.pendencias_fechamento(centro, ano_fiscal)
        if not pendencias["ok"]:
            raise CommandError(
                "O serviço informou sucesso no fechamento, mas ainda existem "
                f"pendências: {pendencias}."
            )
        exercicio.refresh_from_db()
        self._conferir(
            "estado do exercício após o fechamento",
            exercicio.status,
            ExercicioCentro.Status.FECHADO,
        )
        self._conferir(
            "saldo final do centro",
            saldos.total_centro(centro, ano_fiscal, natureza),
            Decimal("0.00"),
        )
        self._conferir(
            "saldo final do empenho",
            saldos.saldo_empenho(empenho),
            Decimal("0.00"),
        )
        self._conferir(
            "saldo final da unidade",
            saldos.saldo_unidade(unidade, ano_fiscal, natureza),
            Decimal("0.00"),
        )
        self.stdout.write(
            f"[6/6] Exercício fechado pela transação #{fechamento.pk}; "
            "pendências e saldos finais zerados."
        )

    @staticmethod
    def _conferir(descricao, valor_obtido, valor_esperado):
        """
        Interrompe o cenário com contexto se um saldo ou estado não for o esperado.

        A comparação é direta (incluindo Decimal) para que uma divergência real no
        modelo não seja escondida por arredondamento ou por uma tolerância genérica.
        """
        if valor_obtido != valor_esperado:
            raise CommandError(
                f"Falha ao conferir {descricao}: esperado {valor_esperado!r}, "
                f"obtido {valor_obtido!r}."
            )
