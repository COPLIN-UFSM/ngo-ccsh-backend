from django.urls import reverse
from rest_framework import status

from entidades.models import Centro, Curso, Pessoa, PessoaSIE
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class PessoaViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:pessoas-list")
        self.pessoaSIE = PessoaSIE.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000" )
        self.pessoa2SIE = PessoaSIE.objects.create(id_pessoa_sie=100, nome_pessoa="Shintaro Yamazaki", rg="22200000000", cpf="22200000000")
        self.pessoa = Pessoa.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000", pessoa_sie=self.pessoaSIE)

        self.pessoa_data = {
            "nome_pessoa": "Shingen Yamazaki",
            "rg": "22200000000",
            "cpf": "22200000000"
        }

        self.pessoa_data_not_registered_in_sie = {
            "nome_pessoa": "Shingen Yamazaki",
            "rg": "1111111100",
            "cpf": "1111111100"
        }

    def test_get_pessoas(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 7) # Contando com os criados no setup.
        self.assertIn({"id_pessoa_interna": 7, "nome_pessoa": "Leandro", "rg": "05100000000", "cpf": "05100000000", "telefones": [], "emails": []}, response.data['data'])

    def test_create_pessoa_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.pessoa_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cpf", response.data)

        response = self.client.get(self.url)
        self.assertIn({"id_pessoa_interna": 8, "nome_pessoa": "Shintaro Yamazaki", "rg": "22200000000", "cpf": "22200000000", "telefones": [], "emails": []}, response.data['data'])


    def test_create_pessoa_not_registered_in_sie(self):
        self.authentication(self.user_data_adm)

        response = self.client.post(self.url, data=self.pessoa_data_not_registered_in_sie, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual("Shingen Yamazaki", response.data['nome_pessoa'])
        self.assertEqual("1111111100", response.data['rg'])
        self.assertEqual("1111111100", response.data['cpf'])

    def test_create_pessoa_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"nome_pessoa": "Zeus"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



class SinglePessoaViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.pessoaSIE = PessoaSIE.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000")
        self.pessoa2SIE = PessoaSIE.objects.create(id_pessoa_sie=100, nome_pessoa="Shintaro Yamazaki", rg="22200000000", cpf="22200000000")

        self.pessoa = Pessoa.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000",
                                            pessoa_sie=self.pessoaSIE)
        self.pessoa_data = {
            "nome_pessoa": "Shingen Yamazaki",
            "rg": "22200000000",
            "cpf": "22200000000"
        }

        self.pessoa_data_not_registered_in_sie = {
            "nome_pessoa": "Shingen Yamazaki",
            "rg": "1111111100",
            "cpf": "1111111100"
        }

        self.urlPrefix = "entidades:pessoas-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.pessoa.id_pessoa_interna})


    def test_get_single_pessoa(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual("Leandro", response.data["nome_pessoa"])

    def test_get_single_pessoa_only_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": self.pessoa2SIE.id_pessoa_sie})
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("Shintaro Yamazaki", response.data["nome_pessoa"], )

    def test_get_nonexistent_pessoa(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pessoa_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_pessoa_not_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        self.pessoa.pessoa_sie = None
        self.pessoa.save()

        data = {"nome_pessoa": "Artemis", "telefone": "55991738312"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_patch_pessoa_cpf_not_unique_only_pessoas_not_in_sie(self):
    #     self.authentication(self.user_data_adm)
    #     self.pessoa.pessoa_sie = None
    #     self.pessoa.save()
    #
    #     data = {"nome_pessoa": "Artemis", "telefone": "55991738312"}
    #     response = self.client.patch(self.url, data=data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_pessoa(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
