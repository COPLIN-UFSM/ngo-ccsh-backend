from nturl2path import url2pathname
from types import new_class
from urllib import request, response
from rest_framework.test import APITestCase
from ..models import CustomUser
from django.urls import reverse
from rest_framework import status


class LoginViewTestCase(APITestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            username="admin", email="admin@gmail.com", password="adminpass"
        )
        self.normal_user = CustomUser.objects.create_user(
            username="user", email="user@gmail.com", password="userpass"
        )
        self.normal_user_not_active = CustomUser.objects.create_user(
            username="user_not_active",
            email="user2@gmail.com",
            password="userpass2",
            is_active=False,
        )
        self.data_user_adm = {
            "username": self.admin_user.username,
            "password": "adminpass",
        }
        self.data_user_normal = {
            "username": self.normal_user.username,
            "password": "userpass",
        }
        self.data_user_not_active = {
            "username": self.normal_user_not_active.username,
            "password": "userpass2",
        }

        self.url = reverse("users:login")

    def test_login_username_not_provided(self):
        data = {
            "password": self.data_user_normal["password"],
        }
        detailExpected = "Dados não inseridos. Por favor insira o usuário e a senha."

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], detailExpected)

    def test_login_password_not_provided(self):
        data = {
            "username": self.data_user_normal["username"],
        }
        detailExpected = "Dados não inseridos. Por favor insira o usuário e a senha."

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], detailExpected)

    def test_login_password_failed_authentication(self):
        data = {
            "username": self.data_user_normal["username"],
            "password": "senhaerrada",
        }
        detailExpected = "Credenciais inválidas."

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], detailExpected)

    def test_login_username_failed_authentication(self):
        data = {
            "username": "users1231",
            "password": self.data_user_normal["password"],
        }
        detailExpected = "Credenciais inválidas."

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], detailExpected)

    def test_login_user_not_active(self):
        response = self.client.post(self.url, data=self.data_user_not_active)
        detailExpected = "Credenciais inválidas."

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], detailExpected)

    def test_login_authenticated(self):
        response = self.client.post(self.url, data=self.data_user_normal)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_methods_not_authorized(self):
        response_get = self.client.get(self.url)
        response_patch = self.client.patch(self.url)
        response_delete = self.client.delete(self.url)

        self.assertEqual(response_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(
            response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )


# Continuar aqui
class UserViewTestCase(APITestCase):
    # self.client.login()
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            username="admin", email="admin@gmail.com", password="adminpass"
        )
        self.normal_user = CustomUser.objects.create_user(
            username="user", email="user@gmail.com", password="userpass"
        )
        self.data_user_adm = {
            "username": self.admin_user.username,
            "password": "adminpass",
        }
        self.data_user_normal = {
            "username": self.normal_user.username,
            "password": "userpass",
        }
        self.url = reverse("users:userView")

    def test_user_not_logged_permissions(self):
        response_get = self.client.get(self.url)
        response_post = self.client.post(self.url)
        self.assertEqual(response_get.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response_post.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_users(self):
        self.assertTrue(
            self.client.login(
                username=self.data_user_normal["username"],
                password=self.data_user_normal["password"],
            )
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_adm_can_create_users(self):
        self.assertTrue(
            self.client.login(
                username=self.data_user_normal["username"],
                password=self.data_user_normal["password"],
            )
        )
        new_user = {
            "username": "loki",
            "email": "loki@gmail.com",
            "password": "dinamarca",
        }
        response = self.client.post(self.url, data=new_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
