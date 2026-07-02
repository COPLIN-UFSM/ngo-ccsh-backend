from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from despesas.models import Beneficiario
from despesas.tests import DespesasTestAPI


class BeneficiarioViewSetTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url_list = reverse("despesas:beneficiario_interno-list")
        self.beneficiario = Beneficiario.objects.create(beneficiario="João Silva", cpf="12345678901")

    def test_get_beneficiarios_unauthenticated(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_beneficiarios_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_beneficiario(self):
        self.authentication(self.user_data_normal)
        data = {"beneficiario_interno": "Maria Souza", "cpf": "98765432100"}
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["beneficiario_interno"], "Maria Souza")

    def test_create_beneficiario_bad_request(self):
        self.authentication(self.user_data_normal)
        data = {"cpf": "98765432100"}
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_beneficiario(self):
        self.authentication(self.user_data_normal)
        url_detail = reverse("despesas:beneficiario_interno-detail", kwargs={"pk": self.beneficiario.pk})
        data = {"beneficiario_interno": "João Silva Editado"}
        response = self.client.patch(url_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["beneficiario_interno"], "João Silva Editado")

    def test_delete_beneficiario(self):
        self.authentication(self.user_data_normal)
        url_detail = reverse("despesas:beneficiario_interno-detail", kwargs={"pk": self.beneficiario.pk})
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
