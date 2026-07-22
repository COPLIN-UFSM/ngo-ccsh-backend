# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase
# from despesas.models import Unidade
# from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase
#
#
# class UnidadeViewTestCase(BaseAuthenticatedUserTestCase):
#     def setUp(self):
#         self.url = reverse("entidades:unidades")
#         self.unidade = Unidade.objects.create(unidade="Departamento A", grupo="DEPTO")
#
#     def test_get_unidades(self):
#         self.authentication(self.user_data_adm)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_unidade_as_admin(self):
#         self.authentication(self.user_data_adm)
#         data = {"unidade": "Curso X", "grupo": "CURSOS"}
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_create_unidade_as_normal_user_fails(self):
#         self.authentication(self.user_data_normal)
#         data = {"unidade": "Curso Y", "grupo": "CURSOS"}
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#
#     def test_create_unidade_bad_request(self):
#         self.authentication(self.user_data_adm)
#         data = {"grupo": "CURSOS"}  # Missing unidade
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#
#
# class SingleunidadeViewTestCase(APITestCase):
#     def setUp(self):
#         self.create_test_users()
#         self.unidade = Unidade.objects.create(unidade="Departamento B", grupo="DEPTO")
#         self.url = reverse("entidades:single_unidade", kwargs={"pk": self.unidade.pk})
#
#     def test_get_single_unidade(self):
#         self.authentication(self.user_data_adm)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["unidade"], "Departamento B")
#
#     def test_get_nonexistent_unidade(self):
#         self.authentication(self.user_data_adm)
#         url = reverse("despesas:single_unidade", kwargs={"pk": 999})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#
#     def test_put_unidade_as_admin(self):
#         self.authentication(self.user_data_adm)
#         data = {"unidade": "Departamento B Editado", "grupo": "DEPTO"}
#         response = self.client.put(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_delete_unidade_as_admin(self):
#         self.authentication(self.user_data_adm)
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
