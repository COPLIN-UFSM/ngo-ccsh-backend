from django.urls import reverse
from rest_framework import status

from entidades.models import Pessoa, PessoaSIE, Centro, Curso, Discente
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class DiscenteViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:discentes-list")

        self.centro = Centro.objects.create(nome_centro="Curso X", sigla_centro="CoisaBonita12",
                                            cod_estruturado="TdTEST")
        self.curso = Curso.objects.create(centro=self.centro, nome_curso="Curso A", nivel_curso="Bacharelado",
                                          modalidade_curso="Presencial", classificacao_curso="Graduação")
        self.cursoCC = Curso.objects.create(centro=self.centro, nome_curso="Ciência da Computação", nivel_curso="Bacharelado",
                                          modalidade_curso="Presencial", classificacao_curso="Graduação")

        self.pessoaSIE = PessoaSIE.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000")
        self.pessoa = Pessoa.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000",
                                            pessoa_sie=self.pessoaSIE)
        self.discente = Discente.objects.create(curso=self.curso, pessoa=self.pessoa, matricula="202311173")

        self.discente_data = {
            "matricula": "200000123",
            "curso": self.cursoCC.id_curso
        }

    def test_get_discentes(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        item = next((s for s in response.data["data"] if s["matricula"] == "202311173"), None)
        self.assertIsNotNone(item)

        self.assertEqual("202311173", item['matricula'])
        self.assertEqual("Leandro", item['pessoa']['nome_pessoa'])

    def test_create_discente(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.discente_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_discente_not_registered_in_sie(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.discente_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SingleDiscenteViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.centro = Centro.objects.create(
            nome_centro="Centro X",
            sigla_centro="CoisaBonita12",
            cod_estruturado="TdTEST",
        )
        self.curso = Curso.objects.create(
            centro=self.centro,
            nome_curso="Curso A",
            nivel_curso="Bacharelado",
            modalidade_curso="Presencial",
            classificacao_curso="Graduação",
        )
        self.cursoCC = Curso.objects.create(
            centro=self.centro,
            nome_curso="Ciência da Computação",
            nivel_curso="Bacharelado",
            modalidade_curso="Presencial",
            classificacao_curso="Graduação",
        )

        self.pessoaSIE = PessoaSIE.objects.create(nome_pessoa="Leandro", rg="05100000000", cpf="05100000000")
        self.pessoa = Pessoa.objects.create(
            nome_pessoa="Leandro",
            rg="05100000000",
            cpf="05100000000",
            pessoa_sie=self.pessoaSIE,
        )
        self.discente = Discente.objects.create(curso=self.curso, pessoa=self.pessoa, matricula="202311173")

        self.discente_data = {
            "matricula": "200000123",
            "curso": self.cursoCC.id_curso,
        }

        self.urlPrefix = "entidades:discentes-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.discente.id_curso_aluno})

    def test_get_discente_not_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_single_discente(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual("202311173", response.data["matricula"])
        self.assertEqual("Leandro", response.data["pessoa"]['nome_pessoa'])
        self.assertEqual("05100000000", response.data["pessoa"]['cpf'])
        self.assertEqual("Curso A", response.data["curso"]["nome_curso"])

    def test_get_nonexistent_discente(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_discente_not_allowed(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_discente_not_allowed(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
