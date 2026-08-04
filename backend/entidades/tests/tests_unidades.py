from django.urls import reverse
from rest_framework import status

from despesas.models import Unidade
from entidades.models import Centro, TipoUnidade, SituacaoUnidade, UnidadeSIE
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

    def test_create_unidade_(self):
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


class SingleUnidadeViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="TEST", cod_estruturado="TTEST")
        self.tipo_unidade = TipoUnidade.objects.create(tipo_unidade="TOP")
        self.situacao_unidade = SituacaoUnidade.objects.create(situacao_unidade="MUITO BOA")
        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="CoisaBonita12",
                                            cod_estruturado="TdTEST")
        self.unidade_sie = UnidadeSIE.objects.create(nome_unidade="Departamento A", cod_estruturado="DEPTO1",
                                                     centro=self.centro, tipo_unidade=self.tipo_unidade,
                                                     situacao_unidade=self.situacao_unidade)

        self.unidade = Unidade.objects.create(unidade_sie=self.unidade_sie, nome_unidade="Departamento A",
                                              cod_estruturado="DEPTO1",
                                              centro=self.centro, tipo_unidade=self.tipo_unidade,
                                              situacao_unidade=self.situacao_unidade)
        self.urlPrefix = "entidades:unidades-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.unidade.pk})

    def test_get_single_unidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome_unidade"], "Departamento A")

    def test_get_nonexistent_unidade(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_unidade_registered_on_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_unidade(self):
        self.authentication(self.user_data_adm)
        self.unidade.unidade_sie = None
        self.unidade.save()

        data = {"unidade": "Departamento B Editado"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_unidade_(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SituacaoUnidadeViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.situacao_unidade = SituacaoUnidade.objects.create(situacao_unidade="MUITO BOA")
        self.url = reverse("entidades:situacoes_unidades-list")
        self.data = {"situacao_unidade": "Curso Legal"}

    def test_get_situacoes_unidades(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, response.data["count"])
        self.assertEqual("MUITO BOA", response.data["data"][0]["situacao_unidade"], )

    def test_create_situacao_unidade_without_authentication(self):
        self.authentication(self.user_data_normal)
        self.response = self.client.post(self.url)
        self.assertEqual(405, self.response.status_code)

    def test_create_situacao_unidade_as_normal_user(self):
        self.authentication(self.user_data_normal)
        self.response = self.client.post(self.url, data=self.data)
        self.assertEqual(405, self.response.status_code)

    def test_create_situacao_unidade_with_name_already_exist(self):
        self.authentication(self.user_data_normal)
        self.response = self.client.post(self.url, data={"situacao_unidade": self.situacao_unidade.situacao_unidade})
        self.assertEqual(405, self.response.status_code)

    def test_create_situacao_unidade_bad_request(self):
        self.authentication(self.user_data_normal)
        self.response = self.client.post(self.url, data={"nome_unidade": "Curso Legal"})
        self.assertEqual(405, self.response.status_code)

class SingleSituacaoUnidadeViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.situacao_unidade = SituacaoUnidade.objects.create(situacao_unidade="MUITO BOA")

        self.urlPrefix = "entidades:situacoes_unidades-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.situacao_unidade.pk})
        self.data = {"situacao_unidade": "Curso Legal"}

    def test_get_single_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["situacao_unidade"], "MUITO BOA")

    def test_get_nonexistent_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        data = {"situacao_unidade": "Curso Ruim"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class TipoUnidadeViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.tipo_unidade = TipoUnidade.objects.create(tipo_unidade="Muito interessante")
        self.url = reverse("entidades:tipos_unidades-list")
        self.data = {"tipos_unidades": "Tipo top de linha"}

    def test_get_tipos_unidades(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, response.data["count"])
        self.assertEqual("Muito interessante", response.data["data"][0]["tipo_unidade"], )

    def test_create_tipo_unidade_without_authentication(self):
        self.authentication(self.user_data_normal)
        self.response = self.client.post(self.url)
        self.assertEqual(405, self.response.status_code)

    def test_create_tipo_unidade(self):
        self.authentication(self.user_data_normal)
        self.response = self.client.post(self.url, data=self.data)
        self.assertEqual(405, self.response.status_code)


class TipoUnidadeViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.tipo_unidade = TipoUnidade.objects.create(tipo_unidade="Muito interessante")

        self.urlPrefix = "entidades:tipos_unidades-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.tipo_unidade.pk})
        self.data = {"situacao_unidade": "Tipo Legal"}

    def test_get_single_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tipo_unidade"], "Muito interessante")

    def test_get_nonexistent_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        data = {"tipo_unidade": "Curso Ruim"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_situacao_unidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

