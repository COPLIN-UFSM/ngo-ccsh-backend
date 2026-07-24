from django.urls import reverse
from rest_framework import status

from despesas.models import Unidade
from entidades.models import Centro, TipoUnidade, SituacaoUnidade
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class UnidadeViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:unidades-list")
        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="TEST", cod_estruturado="TTEST")
        self.tipo_unidade = TipoUnidade.objects.create(tipo_unidade="TOP")
        self.situacao_unidade = SituacaoUnidade.objects.create(situacao_unidade="MUITO BOA")
        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="CoisaBonita12",
                                            cod_estruturado="TdTEST")

        self.unidade = Unidade.objects.create(nome_unidade="Departamento A", cod_estruturado="DEPTO1",
                                              centro=self.centro, tipo_unidade=self.tipo_unidade,
                                              situacao_unidade=self.situacao_unidade)
        self.unidade_data = {"nome_unidade": "Departamento D", "cod_estruturado": "DEPTO2",
                             "centro": self.centro.id_centro_interno, "tipo_unidade": self.tipo_unidade.id_tipo_unidade,
                             "situacao_unidade": self.situacao_unidade.id_situacao_unidade}

    def test_get_unidades(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_unidade_as_admin(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.unidade_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_unidade_as_normal_user_fails(self):
        self.authentication(self.user_data_normal)

        response = self.client.post(self.url, data=self.unidade_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


    def test_create_unidade_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"nome_unidade": "Curso Legal"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

# class SingleunidadeViewTestCase(BaseAuthenticatedUserTestCase):
#     def setUp(self):
#         def setUp(self):
#             self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="TEST", cod_estruturado="TTEST")
#             self.tipo_unidade = TipoUnidade.objects.create(tipo_unidade="TOP")
#             self.situacao_unidade = SituacaoUnidade.objects.create(situacao_unidade="MUITO BOA")
#             self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="CoisaBonita12",
#                                                 cod_estruturado="TdTEST")
#
#             self.unidade = Unidade.objects.create(nome_unidade="Departamento A", cod_estruturado="DEPTO1",
#                                                   centro=self.centro, tipo_unidade=self.tipo_unidade,
#                                                   situacao_unidade=self.situacao_unidade)
#             self.url = reverse("entidades:single_unidade-detail", kwargs={"pk": self.unidade.pk})
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
#     def test_patch_unidade_as_admin(self):
#         self.authentication(self.user_data_adm)
#         data = {"unidade": "Departamento B Editado"}
#         response = self.client.patch(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#     def test_delete_unidade_as_admin(self):
#         self.authentication(self.user_data_adm)
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
