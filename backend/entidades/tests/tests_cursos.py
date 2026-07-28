from django.urls import reverse
from rest_framework import status

from despesas.models import Unidade
from entidades.models import Centro, TipoUnidade, SituacaoUnidade, UnidadeSIE, Curso
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class CursoViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:cursos-list")
        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="CoisaBonita12",
                                            cod_estruturado="TdTEST")

        self.curso = Curso.objects.create(centro=self.centro, nome_curso="Curso A", nivel_curso="Bacharelado",
                                            modalidade_curso="Presencial", classificacao_curso="Graduação")

        self.curso_data = {
            "centro": self.centro.id_centro_interno,
            "nome_curso": "Curso B",
            "nivel_curso": "Licenciatura",
            "modalidade_curso": "EAD",
            "classificacao_curso": "Pós-graduação"
        }

    def test_get_cursos(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_curso(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.curso_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_curso_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"nome_curso": "Curso Legal"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class SingleCursoViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="CoisaBonita12",
                                            cod_estruturado="TdTEST")

        self.curso = Curso.objects.create(centro=self.centro, nome_curso="Curso A", nivel_curso="Bacharelado",
                                          modalidade_curso="Presencial", classificacao_curso="Graduação")

        self.curso_data = {
            "centro": self.centro.id_centro_interno,
            "nome_curso": "Curso B",
            "nivel_curso": "Licenciatura",
            "modalidade_curso": "EAD",
            "classificacao_curso": "Pós-graduação"
        }

        self.urlPrefix = "entidades:cursos-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.curso.id_curso})

    def test_get_single_curso(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome_curso"], "Curso A")

    def test_get_nonexistent_curso(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_curso_registered_on_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_curso(self):
        self.authentication(self.user_data_adm)
        self.curso.curso_sie = None
        self.curso.save()

        data = {"nome_curso": "Curso B Editado"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_curso(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
