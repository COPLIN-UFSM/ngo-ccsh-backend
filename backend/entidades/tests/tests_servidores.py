from django.urls import reverse
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase
from rest_framework import status

from entidades.models import (
    Cargo,
    EmailSIE,
    Pessoa,
    PessoaSIE,
    Servidor,
    TelefoneSIE,
)


class ServidorViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:servidores-list")

        self.cargo_professor = Cargo.objects.create(cargo="Professor")
        self.cargo_reitor = Cargo.objects.create(cargo="Reitor")

        self.pessoaSIE = PessoaSIE.objects.create(
            nome_pessoa="Leandro", rg="05100000000", cpf="05100000000"
        )
        self.pessoa = Pessoa.objects.create(
            nome_pessoa="Leandro",
            rg="05100000000",
            cpf="05100000000",
            pessoa_sie=self.pessoaSIE,
        )

        self.servidor = Servidor.objects.create(
            pessoa=self.pessoa, matricula="200000063", cargo=self.cargo_professor
        )

        self.servidor_data = {
            "matricula": "200000123",
            "cargo": self.cargo_reitor.id_cargo,
        }

    def test_get_servidores(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 6)
        item = next(
            (s for s in response.data["data"] if s["matricula"] == "200000063"), None
        )
        self.assertIsNotNone(item)

        self.assertEqual("200000063", item["matricula"])
        self.assertEqual("Professor", item["cargo"])

    def test_create_servidor(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.servidor_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_servidor_not_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.servidor_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_cpf_imports_new_server_and_contacts(self):
        self.authentication(self.user_data_adm)
        pessoa_sie = PessoaSIE.objects.create(
            nome_pessoa="Ana Nova",
            cpf="99123456789",
            rg="88123456789",
        )
        EmailSIE.objects.create(
            pessoa_sie=pessoa_sie,
            email="ana.nova@example.com",
        )
        TelefoneSIE.objects.create(
            pessoa_sie=pessoa_sie,
            telefone="5551999999999",
        )
        Servidor.objects.create(
            pessoa_id=pessoa_sie.pk,
            matricula="200000999",
            cargo=self.cargo_professor,
            ativo=True,
        )

        response = self.client.get(
            self.url,
            {"cpf": pessoa_sie.cpf, "ativo": "true"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        servidor = response.data["data"][0]
        self.assertEqual(servidor["cpf"], pessoa_sie.cpf)
        self.assertEqual(
            [email["email"] for email in servidor["emails"]],
            ["ana.nova@example.com"],
        )
        self.assertEqual(
            [telefone["telefone"] for telefone in servidor["telefones"]],
            ["5551999999999"],
        )


class SingleServidorViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.cargo_professor = Cargo.objects.create(cargo="Professor")
        self.cargo_reitor = Cargo.objects.create(cargo="Reitor")

        self.pessoaSIE = PessoaSIE.objects.create(
            id_pessoa_sie=500,
            nome_pessoa="Leandro",
            rg="05100000000",
            cpf="05100000000",
        )
        self.pessoa = Pessoa.objects.create(
            id_pessoa_interna=self.pessoaSIE.id_pessoa_sie,
            nome_pessoa="Leandro",
            rg="05100000000",
            cpf="05100000000",
            pessoa_sie=self.pessoaSIE,
        )
        self.servidor = Servidor.objects.create(
            pessoa=self.pessoa, matricula="200000063", cargo=self.cargo_professor
        )

        self.servidor_data = {
            "matricula": "200000123",
            "cargo": self.cargo_reitor.id_cargo,
        }

        self.urlPrefix = "entidades:servidores-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.servidor.id_contrato_rh})

    def test_get_servidor_not_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_single_servidor(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("Professor", response.data["cargo"])
        self.assertEqual("Leandro", response.data["nome_pessoa"])
        self.assertEqual("05100000000", response.data["cpf"])

    def test_get_nonexistent_servidor(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_pessoa_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_pessoa(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
