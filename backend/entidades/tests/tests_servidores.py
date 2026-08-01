from django.urls import reverse
from rest_framework import status

from entidades.models import Pessoa, PessoaSIE, Servidor, Cargo
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class ServidorViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:servidores-list")

        self.cargo_professor = Cargo.objects.create(cargo="Professor")
        self.cargo_reitor = Cargo.objects.create(cargo="Reitor")

        self.pessoaSIE = PessoaSIE.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000")
        self.pessoa = Pessoa.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000",
                                            pessoa_sie=self.pessoaSIE)

        self.servidor = Servidor.objects.create(pessoa=self.pessoa, matricula="200000063",
                                                cargo=self.cargo_professor)

        self.servidor_data = {
            "matricula": "200000123",
            "cargo": self.cargo_reitor.id_cargo,
        }

    def test_get_servidores(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)
        item = next((s for s in response.data["data"] if s["matricula"] == "200000063"), None)
        self.assertIsNotNone(item)

        self.assertEqual("200000063", item['matricula'])
        self.assertEqual("Professor", item['cargo'])

    def test_create_servidor(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.servidor_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_servidor_not_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.servidor_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SingleServidorViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.cargo_professor = Cargo.objects.create(cargo="Professor")
        self.cargo_reitor = Cargo.objects.create(cargo="Reitor")

        self.pessoaSIE = PessoaSIE.objects.create(id_pessoa_sie=500, nome_pessoa="Leandro", rg="05100000000",
                                                  cpf="05100000000")
        self.pessoa = Pessoa.objects.create(id_pessoa_interna=self.pessoaSIE.id_pessoa_sie, nome_pessoa="Leandro",
                                            rg="05100000000", cpf="05100000000",
                                            pessoa_sie=self.pessoaSIE)
        self.servidor = Servidor.objects.create(pessoa=self.pessoa, matricula="200000063",
                                                cargo=self.cargo_professor)

        self.servidor_data = {
            "matricula": "200000123",
            "cargo": self.cargo_reitor.id_cargo,
        }

        self.urlPrefix = "entidades:servidores-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.servidor.id_contrato_rh})

    def test_get_single_servidor(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("Professor", response.data["cargo"])
        self.assertEqual("Leandro", response.data["pessoa"]['nome_pessoa'])
        self.assertEqual("05100000000", response.data["pessoa"]['cpf'])

    def test_get_nonexistent_servidor(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_pessoa_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_pessoa_not_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        self.pessoa.pessoa_sie = None
        self.pessoa.save()

        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # def test_patch_pessoa_only_registered_in_sie(self):
    #     self.authentication(self.user_data_adm)
    #     url = reverse(self.urlPrefix, kwargs={"pk": self.pessoa2SIE.id_pessoa_sie})
    #     response = self.client.patch(self.url, data={"rg": "05100000000"}, format="json")
    #     self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    #
    #     response = self.client.get(url)
    #     self.assertEqual(
    #         {"id_pessoa_interna": 8, "nome_pessoa": "Shintaro Yamazaki", "rg": "22200000000", "cpf": "22200000000",
    #          "telefones": [], "emails": []}, response.data)

    def test_delete_pessoa(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
