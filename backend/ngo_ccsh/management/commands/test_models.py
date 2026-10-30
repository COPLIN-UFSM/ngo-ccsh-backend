from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.crypto import get_random_string

from despesas import saldos, services
from despesas.models import Empenho, Finalidade, Natureza
from entidades.models import Centro, Pessoa
from usuarios.models import Usuario


class Command(BaseCommand):
    help = "Executa uma verificação transacional dos modelos de despesas."

    @transaction.atomic
    def handle(self, *args, **options):
        cpf = self._cpf_disponivel()
        pessoa = Pessoa.objects.create(
            nome_pessoa="Verificação de modelos",
            cpf=cpf,
            rg=get_random_string(10, allowed_chars="0123456789"),
        )
        usuario = Usuario.objects.create(
            cpf=cpf,
            email=f"model-check-{cpf}@example.invalid",
            pessoa=pessoa,
        )
        centro = Centro.objects.create(
            nome_centro="Verificação de modelos",
            sigla_centro=f"T{cpf[:5]}",
            cod_estruturado=cpf[:10],
        )
        natureza = Natureza.objects.create(nome=f"Verificação {cpf}")
        finalidade = Finalidade.objects.create(
            nome=f"Verificação {cpf}",
            natureza=natureza,
        )
        empenho = Empenho.objects.create(
            numero_empenho=cpf,
            centro=centro,
            ano_fiscal=2099,
            natureza=natureza,
            finalidade=finalidade,
        )

        services.creditar(centro, 2099, natureza, 10, usuario)
        services.reforcar_empenho(empenho, 10, usuario)
        if saldos.saldo_empenho(empenho) != 10:
            raise RuntimeError("O saldo do empenho não corresponde ao reforço.")

        transaction.set_rollback(True)
        self.stdout.write(self.style.SUCCESS("Modelos e operações verificados."))

    @staticmethod
    def _cpf_disponivel():
        while True:
            cpf = get_random_string(11, allowed_chars="0123456789")
            if not Pessoa.objects.filter(cpf=cpf).exists():
                return cpf
