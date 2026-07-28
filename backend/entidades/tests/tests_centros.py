from django.urls import reverse
from rest_framework import status

from entidades.models import Centro, CentroSIE
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class CentroViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:centros-list")
        self.centro = CentroSIE.objects.create(nome_centro="Curso X", sigla_centro="TEST", cod_estruturado="TdTEST")
        self.centro = Centro.objects.create(centro_sie=self.centro, nome_centro="Curso X", sigla_centro="TEST", cod_estruturado="TdTEST")
        self.centro_data = {"nome_centro": "Curso X2", "sigla_centro": "TESTE", "cod_estruturado": "TdTESTE"}


    def test_get_centros(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_centro(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.centro_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_centro_as_normal_user(self):
        self.authentication(self.user_data_normal)

        response = self.client.post(self.url, data=self.centro_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_centro_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"nome_centro": "Curso Legal"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleCentroViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        super().setUp()
        self.centro = CentroSIE.objects.create(nome_centro="Curso X", sigla_centro="TEST", cod_estruturado="TdTEST")
        self.centro = Centro.objects.create(centro_sie=self.centro, nome_centro="Curso X", sigla_centro="TEST",
                                            cod_estruturado="TdTEST")
        self.centro_data = {"nome_centro": "Curso X", "sigla_centro": "TEST", "cod_estruturado": "TdTEST"}

        self.urlPrefix = "entidades:centros-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.centro.pk})

    def test_get_single_centro(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome_centro"], "Curso X")

    def test_get_nonexistent_centro(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_centro_registered_on_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_centro(self):
        self.authentication(self.user_data_adm)
        self.centro.centro_sie = None
        self.centro.save()

        data = {"centro": "Departamento B Editado"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_centro(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
