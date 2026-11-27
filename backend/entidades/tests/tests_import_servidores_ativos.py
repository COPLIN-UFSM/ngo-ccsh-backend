from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from entidades.models import (
    Cargo,
    Email,
    EmailSIE,
    Pessoa,
    PessoaSIE,
    Servidor,
    Telefone,
    TelefoneSIE,
)


class ImportServidoresAtivosCommandTestCase(TestCase):
    def setUp(self):
        self.cargo = Cargo.objects.create(cargo="Analista")

    def create_servidor(self, pessoa_sie_id, matricula, ativo=True):
        return Servidor.objects.create(
            pessoa_id=pessoa_sie_id,
            matricula=matricula,
            cargo=self.cargo,
            ativo=ativo,
        )

    def run_command(self):
        stdout = StringIO()
        stderr = StringIO()
        call_command(
            "import_servidores_ativos",
            stdout=stdout,
            stderr=stderr,
        )
        return stdout.getvalue(), stderr.getvalue()

    def test_importa_pessoas_contatos_e_eh_idempotente(self):
        pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa="Ana",
            cpf="99123456789",
            rg="88123456789",
        )
        EmailSIE.objects.create(
            pessoa_sie=pessoa_sie,
            email="ana@example.com",
        )
        TelefoneSIE.objects.create(
            pessoa_sie=pessoa_sie,
            telefone="5551999999999",
        )
        self.create_servidor(pessoa_sie.pk, "200000101")

        stdout, stderr = self.run_command()
        self.run_command()

        pessoa = Pessoa.objects.get(pessoa_sie=pessoa_sie)
        self.assertEqual(pessoa.email_set.count(), 1)
        self.assertEqual(pessoa.telefone_set.count(), 1)
        self.assertIn("Pessoas criadas: 1", stdout)
        self.assertEqual(stderr, "")
        self.assertEqual(Email.objects.filter(email="ana@example.com").count(), 1)
        self.assertEqual(Telefone.objects.filter(telefone="5551999999999").count(), 1)

    def test_importa_contatos_em_pessoa_existente_sem_reatribuir_email(self):
        outra_pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa="Bruna",
            cpf="77123456789",
            rg="66123456789",
        )
        outra_pessoa = Pessoa.objects.create(
            pessoa_sie=outra_pessoa_sie,
            nome_pessoa=outra_pessoa_sie.nome_pessoa,
            cpf=outra_pessoa_sie.cpf,
            rg=outra_pessoa_sie.rg,
        )
        Email.objects.create(pessoa=outra_pessoa, email="shared@example.com")

        pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa="Ana",
            cpf="99123456789",
            rg="88123456789",
        )
        EmailSIE.objects.create(
            pessoa_sie=pessoa_sie,
            email="shared@example.com",
        )
        TelefoneSIE.objects.create(
            pessoa_sie=pessoa_sie,
            telefone="5551999999999",
        )
        self.create_servidor(pessoa_sie.pk, "200000102")
        self.run_command()

        pessoa = Pessoa.objects.get(pessoa_sie=pessoa_sie)
        self.assertEqual(pessoa.email_set.count(), 0)
        self.assertEqual(pessoa.telefone_set.count(), 1)
        self.assertEqual(
            Email.objects.get(email="shared@example.com").pessoa_id,
            outra_pessoa.pk,
        )

    def test_ignora_inativos_e_reporta_pessoa_sie_ausente(self):
        pessoa_inativa_sie = PessoaSIE.objects.create(
            nome_pessoa="Odin",
            cpf="55123456789",
            rg="44123456789",
        )
        self.create_servidor(pessoa_inativa_sie.pk, "200000103", ativo=False)
        self.create_servidor(999999, "200000104", ativo=True)

        _, stderr = self.run_command()

        self.assertFalse(
            Pessoa._base_manager.filter(pessoa_sie=pessoa_inativa_sie).exists()
        )
        self.assertIn("Sem pessoa em v_sie_pessoas: 1", stderr)

    def test_reporta_conflito_de_cpf_sem_ocultar_outros_erros(self):
        outra_pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa="Bruna",
            cpf="99123456789",
            rg="66123456789",
        )
        Pessoa.objects.create(
            pessoa_sie=outra_pessoa_sie,
            nome_pessoa=outra_pessoa_sie.nome_pessoa,
            cpf=outra_pessoa_sie.cpf,
            rg=outra_pessoa_sie.rg,
        )
        pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa="Ana",
            cpf="99123456789",
            rg="88123456789",
        )
        self.create_servidor(pessoa_sie.pk, "200000105")

        _, stderr = self.run_command()

        self.assertIn("conflitos de pessoa: 1", stderr)
        self.assertFalse(Pessoa._base_manager.filter(pessoa_sie=pessoa_sie).exists())
