from usuarios.models import Usuario
from django.urls import reverse
from despesas.models import TipoDocumento, Empenho, Finalidade, NaturezaFinalidade, GrupoFinalidade, Unidade


class DespesasTestAPI:
    def create_test_users(self):
        self.user_admin = Usuario.objects.create_superuser(username="admin_test", email="admin_test@gmail.com", password="adminpass")
        self.user_normal = Usuario.objects.create_user(username="user_test", email="user_test@gmail.com", password="userpass")
        self.user_data_adm = {
            "username": self.user_admin.username,
            "password": "adminpass",
        }
        self.user_data_normal = {
            "username": self.user_normal.username,
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
