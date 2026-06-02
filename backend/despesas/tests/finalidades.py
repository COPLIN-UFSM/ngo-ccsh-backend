from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from despesas.tests.subunidades import DespesasTestAPI
from despesas.models import NaturezaFinalidade, TipoFinalidade, Finalidade



class NaturezaFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:tipos_despesas")

    def test_get_naturezas(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_natureza(self):
        self.authentication(self.user_data_adm)
        data = {"natureza_finalidade": "Material de Consumo"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_natureza_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleNaturezaFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Equipamentos")
        self.url = reverse("despesas:single_natureza_finalidade", kwargs={"pk": self.natureza.pk})

    def test_get_single_natureza(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_natureza(self):
        self.authentication(self.user_data_adm)
        data = {"natureza_finalidade": "Equipamentos de TI"}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_natureza(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_natureza_with_children(self):
        self.authentication(self.user_data_adm)
        tipo = TipoFinalidade.objects.create(tipo_finalidade="Tipo Teste 1")
        Finalidade.objects.create(
            natureza_finalidade=self.natureza,
            tipo_finalidade=tipo,
            modalidade="DESPESA",
            finalidade="Finalidade com filho",
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TipoFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:subtipo_finalidade")

    def test_get_tipos_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {"tipo_finalidade": "Pesquisa"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SingleTipoFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.tipo_finalidade = TipoFinalidade.objects.create(tipo_finalidade="Extensão")
        self.url = reverse("despesas:single_subtipo_finalidade", kwargs={"pk": self.tipo_finalidade.pk})

    def test_get_single_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {"tipo_finalidade": "Extensão e Cultura"}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_tipo_finalidade_with_children(self):
        self.authentication(self.user_data_adm)
        natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Nat Teste")
        Finalidade.objects.create(
            natureza_finalidade=natureza,
            tipo_finalidade=self.tipo_finalidade,
            modalidade="DESPESA",
            finalidade="Finalidade com filho 2",
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FinalidadesViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:finalidades")
        self.natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Ensino")
        self.tipo = TipoFinalidade.objects.create(tipo_finalidade="Monitoria")

    def test_get_finalidades_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_finalidades_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {
            "natureza_finalidade": self.natureza.pk,
            "tipo_finalidade": self.tipo.pk,
            "modalidade": "DESPESA",
            "finalidade": "Bolsa de Monitoria",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_finalidade_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"modalidade": "DESPESA"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Inovação")
        self.tipo = TipoFinalidade.objects.create(tipo_finalidade="Projeto")
        self.finalidade = Finalidade.objects.create(
            natureza_finalidade=self.natureza,
            tipo_finalidade=self.tipo,
            modalidade="DESPESA",
            finalidade="Projeto X",
        )
        self.url = reverse("despesas:single_finalidades", kwargs={"pk": self.finalidade.pk})

    def test_get_single_finalidade(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {
            "natureza_finalidade": self.natureza.pk,
            "tipo_finalidade": self.tipo.pk,
            "modalidade": "DESPESA",
            "finalidade": "Projeto X Editado",
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
