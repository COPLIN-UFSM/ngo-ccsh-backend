from django.test import TestCase

from entidades.models import (
    Centro,
    CentroSIE,
    Email,
    EmailSIE,
    Pessoa,
    PessoaSIE,
    Telefone,
    TelefoneSIE,
)


class ResolveFromSIETestCase(TestCase):
    def setUp(self):
        self.centro_sie = CentroSIE.objects.create(
            nome_centro="Centro X", sigla_centro="CX", cod_estruturado="CX01"
        )

    def test_get_importa_do_sie(self):
        centro = Centro.objects.get(sigla_centro="CX")
        self.assertEqual(centro.centro_sie, self.centro_sie)

    def test_filter_importa_do_sie(self):
        self.assertTrue(Centro.objects.filter(cod_estruturado="CX01").exists())
        self.assertEqual(Centro.objects.count(), 1)

    def test_lookup_com_sufixo(self):
        self.assertEqual(
            Centro.objects.filter(nome_centro__icontains="entro").count(), 1
        )

    def test_get_or_create_nao_duplica(self):
        centro, created = Centro.objects.get_or_create(
            sigla_centro="CX",
            defaults={"nome_centro": "x", "cod_estruturado": "outro"},
        )
        self.assertFalse(created)
        self.assertEqual(centro.centro_sie, self.centro_sie)

    def test_filtro_por_vinculo_sie(self):
        self.assertTrue(Centro.objects.filter(centro_sie=self.centro_sie).exists())

    def test_nao_duplica_quando_ja_existe(self):
        Centro.objects.get(sigla_centro="CX")
        Centro.objects.filter(sigla_centro="CX").first()
        self.assertEqual(Centro.objects.count(), 1)

    def test_inexistente_continua_inexistente(self):
        with self.assertRaises(Centro.DoesNotExist):
            Centro.objects.get(sigla_centro="NADA")
        self.assertFalse(Centro.objects.filter(sigla_centro="NADA").exists())

    def test_pessoa_filter_por_cpf(self):
        PessoaSIE.objects.create(nome_pessoa="Ana", cpf="123", rg="456")
        self.assertEqual(Pessoa.objects.filter(cpf="123").count(), 1)

    def test_importa_contatos_ao_importar_pessoa(self):
        pessoa_sie = PessoaSIE.objects.create(nome_pessoa="Ana", cpf="1234", rg="4567")
        EmailSIE.objects.create(
            pessoa_sie=pessoa_sie,
            email="ana@example.com",
        )
        TelefoneSIE.objects.create(
            pessoa_sie=pessoa_sie,
            telefone="5551999999999",
        )

        pessoa = Pessoa.objects.get(cpf="1234")

        self.assertEqual(
            list(pessoa.email_set.values_list("email", flat=True)),
            ["ana@example.com"],
        )
        self.assertEqual(
            list(pessoa.telefone_set.values_list("telefone", flat=True)),
            ["5551999999999"],
        )

    def test_nao_duplica_contatos_ao_repetir_importacao(self):
        pessoa_sie = PessoaSIE.objects.create(nome_pessoa="Ana", cpf="1234", rg="4567")
        EmailSIE.objects.create(
            pessoa_sie=pessoa_sie,
            email="ana@example.com",
        )
        TelefoneSIE.objects.create(
            pessoa_sie=pessoa_sie,
            telefone="5551999999999",
        )

        Pessoa.objects.get(cpf="1234")
        Pessoa.objects.get(cpf="1234")

        self.assertEqual(Email.objects.filter(email="ana@example.com").count(), 1)
        self.assertEqual(Telefone.objects.filter(telefone="5551999999999").count(), 1)

    def test_nao_reatribui_email_existente_a_outra_pessoa(self):
        outra_pessoa = Pessoa.objects.create(nome_pessoa="Bruna", cpf="7654", rg="3210")
        Email.objects.create(pessoa=outra_pessoa, email="shared@example.com")
        pessoa_sie = PessoaSIE.objects.create(nome_pessoa="Ana", cpf="1234", rg="4567")
        EmailSIE.objects.create(
            pessoa_sie=pessoa_sie,
            email="shared@example.com",
        )

        with self.assertLogs("entidades.managers", level="WARNING"):
            imported_person = Pessoa.objects.get(cpf="1234")

        self.assertFalse(imported_person.email_set.exists())
        self.assertEqual(
            Email.objects.get(email="shared@example.com").pessoa_id,
            outra_pessoa.pk,
        )
