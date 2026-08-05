from django.urls import reverse
from rest_framework import status

from entidades.models import Telefone
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class TelefonesViewSetTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:telefones-list")
        self.telefone = Telefone.objects.create(telefone="55999300012", pessoa=self.pessoa_ativa)
        self.data = {"telefone": "5599111111", "pessoa": self.pessoa_ativa.pk}

    def test_get_telefones(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, response.data["count"])
        self.assertEqual(self.telefone.telefone, response.data["data"][0]["telefone"])

    def test_create_telefone_without_logged_user(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_create_telefone(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.data, format="json")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.data['telefone'], response.data["telefone"])

    def test_create_and_verify_pessoa_telefone(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.data, format="json")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        url = reverse("entidades:pessoas-detail", kwargs={"pk": self.pessoa_ativa.pk})
        response_pessoa = self.client.get(url)
        response_telefones = response_pessoa.data['telefones']
        match = next((e for e in response_telefones if e["id_telefone"] == self.telefone.pk), None)
        self.assertNotEqual(None, match)

    def test_create_telefone_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"celular": "poseidon@numero.com"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleTelefoneViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.telefone = Telefone.objects.create(telefone="55999300012", pessoa=self.pessoa_ativa)
        self.data = {"telefone": "5599111111", "pessoa": self.pessoa_ativa.pk}

        self.urlPrefix = "entidades:telefones-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.telefone.pk})

    def test_get_single_telefone(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("55999300012", response.data["telefone"])

    def test_get_nonexistent_telefone(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_patch_telefone(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url, data=self.data)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("5599111111", response.data['telefone'])

    def test_patch_telefone_without_effect(self):
        self.authentication(self.user_data_adm)
        data = {"unidade": "Departamento B Editado"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_telefone(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
