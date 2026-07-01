from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from usuarios.models import Usuario
from despesas.models import Transacao, TipoDocumento, Empenho, Finalidade, NaturezaFinalidade, GrupoFinalidade, Unidade


class SetupTestAPI:
    """
    Mixin para auxiliar na criação de dados de teste e autenticação.
    """

    def create_test_users(self):
        self.user_admin = Usuario.objects.create_superuser(username="admin_test", email="admin_test@gmail.com", password="adminpass")
        self.user_normal = Usuario.objects.create_user(username="user_test", email="user_test@gmail.com", password="userpass")
        self.user_data_adm = {
            "matricula": self.user_admin.matricula,
            "password": "adminpass",
        }
        self.user_data_normal = {
            "matricula": self.user_normal.matricula,
            "password": "userpass",
        }

    def authentication(self, data):
        url_auth = reverse("autenticacao:login")
        response = self.client.post(url_auth, data=data)
        token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def create_finalidade(self):
        self.tipo_finalidade = GrupoFinalidade.objects.create(tipo_finalidade="Bolsas")
        self.natureza_finalidade = NaturezaFinalidade.objects.create(natureza_finalidade="Custeio")
        self.finalidade = Finalidade.objects.create(
            tipo_finalidade=self.tipo_finalidade, natureza_finalidade=self.natureza_finalidade, finalidade="Bolsa 2A"
        )

    def create_basic_data(self):
        self.empenho = Empenho.objects.create(empenho="2024NE0001", descricao="Empenho de Teste", finalidade=self.finalidade)
        self.tipo_doc = TipoDocumento.objects.create(tipo_documento="Nota Fiscal")
        self.subunidade = Unidade.objects.create(subunidade="PROPLAN")


class EmpenhoViewTestCase(APITestCase, SetupTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_finalidade()
        self.url = reverse("despesas:empenhos")
        self.new_empenho = {
            "empenho": "2024NE0002",
            "descricao": "Novo Empenho",
            "finalidade": self.finalidade.id_finalidade,
        }

    def test_get_all_empenhos_not_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_empenhos_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_empenho(self):
        self.authentication(self.user_data_normal)
        response = self.client.post(self.url, data=self.new_empenho)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SingleEmpenhoViewTestCase(APITestCase, SetupTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_finalidade()
        self.create_basic_data()
        self.url = reverse("despesas:single_empenho", kwargs={"pk": self.empenho.id_empenho})

    def test_get_empenho_details(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["empenho"], "2024NE0001")

    def test_update_empenho(self):
        self.authentication(self.user_data_adm)
        data = {"empenho": "2024NE0001-MOD", "descricao": "Desc Modificada", "finalidade": self.finalidade.id_finalidade}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.empenho.refresh_from_db()
        self.assertEqual(self.empenho.empenho, "2024NE0001-MOD")

    def test_delete_empenho_with_children(self):
        Transacao.objects.create(empenho=self.empenho, usuario=self.user_normal, montante=100.00, subunidade_executora=self.subunidade)
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        print(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Empenho.objects.filter(pk=self.empenho.id_empenho).exists())
