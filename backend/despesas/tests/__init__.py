from usuarios.models import Usuario
from django.urls import reverse


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
