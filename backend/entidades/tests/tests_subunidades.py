from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from despesas.models import Unidade
from despesas.tests import DespesasTestAPI


class SubunidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("entidades:subunidades")
        self.subunidade = Unidade.objects.create(subunidade="Departamento A", grupo="DEPTO")

    def test_get_subunidades(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_subunidade_as_admin(self):
        self.authentication(self.user_data_adm)
        data = {"subunidade": "Curso X", "grupo": "CURSOS"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_subunidade_as_normal_user_fails(self):
        self.authentication(self.user_data_normal)
        data = {"subunidade": "Curso Y", "grupo": "CURSOS"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_subunidade_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"grupo": "CURSOS"}  # Missing subunidade
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleSubunidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.subunidade = Unidade.objects.create(subunidade="Departamento B", grupo="DEPTO")
        self.url = reverse("entidades:single_subunidade", kwargs={"pk": self.subunidade.pk})

    def test_get_single_subunidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subunidade"], "Departamento B")

    def test_get_nonexistent_subunidade(self):
        self.authentication(self.user_data_adm)
        url = reverse("despesas:single_subunidade", kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_subunidade_as_admin(self):
        self.authentication(self.user_data_adm)
        data = {"subunidade": "Departamento B Editado", "grupo": "DEPTO"}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_subunidade_as_admin(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
