from http import client
from nturl2path import url2pathname
from types import new_class
from urllib import request, response
from rest_framework.test import APITestCase, force_authenticate

from rest_framework_simplejwt.tokens import AccessToken

from ..models import CustomUser
from django.urls import reverse
from rest_framework import status


def createUserNotActive() -> dict:
    user_not_active = CustomUser.objects.create_user(
        username="user_not_active",
        email="user2@gmail.com",
        password="userpass2",
        is_active=False,
    )
    data_not_active = {
        "username": user_not_active.username,
        "password": "userpass2",
    }
    return {"user_not_active": user_not_active, "data": data_not_active}

def authentication_super_token(self, user):
    token = AccessToken.for_user(user=user)
    token["allow_password_change"] = True
    self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')


def authentication(self, data):
    urlAuth = reverse("users:login")
    response = self.client.post(urlAuth, data=data)
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertTrue("token" in response.data)
    token = response.data["token"]
    self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)


class SetupUsers:

    def __init__(self):
        self.admin = CustomUser.objects.create_superuser(
            username="admin", email="admin@gmail.com", password="adminpass"
        )
        self.normal = CustomUser.objects.create_user(
            username="user", email="user@gmail.com", password="userpass"
        )
        self.data_adm = {
            "username": self.admin.username,
            "password": "adminpass",
        }
        self.data_normal = {
            "username": self.normal.username,
            "password": "userpass",
        }


class LoginViewTestCase(APITestCase):
    def setUp(self):
        self.users = SetupUsers()
        self.user_not_active = createUserNotActive()
        self.url = reverse("users:login")

    def test_login_username_not_provided(self):
        data = {
            "password": self.users.data_normal["password"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_password_not_provided(self):
        data = {
            "username": self.users.data_normal["username"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_password_failed_authentication(self):
        data = {
            "username": self.users.data_normal["username"],
            "password": "senhaerrada",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_username_failed_authentication(self):
        data = {
            "username": "users1231",
            "password": self.users.data_normal["password"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_not_active(self):
        response = self.client.post(self.url, data=self.user_not_active["data"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_authenticated(self):
        response = self.client.post(self.url, data=self.users.data_normal)
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


class UserViewTestCase(APITestCase):
    def setUp(self):
        self.users = SetupUsers()
        self.url = reverse("users:userView")
        self.newUser = {
            "username": "Kakaroto",
            "email": "goku@gmail.com",
            "password": "vegeta",
            "password_confirm": "vegeta",
        }

    def test_get_all_users_with_not_user_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_users_with_user_authenticated(self):
        authentication(self, self.users.data_normal)
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_user_with_not_user_authenticated(self):
        response = self.client.post(self.url, self.newUser)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_user_with_normal_user(self):
        authentication(self, self.users.data_normal)
        response = self.client.post(self.url, data=self.newUser)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_user_with_password_confirm_not_provided(self):
        authentication(self, self.users.data_adm)
        response = self.client.post(
            self.url,
            data={
                "username": "Donatelo",
                "password": "TartarugaNinja",
                "email": "escultordonatelo@gmail.com",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_passwords_not_equal(self):
        authentication(self, self.users.data_adm)
        response = self.client.post(
            self.url,
            data={
                "username": "Donatelo",
                "password": "TartarugaNinja",
                "password_confirm": "EscultorNinja",
                "email": "escultordonatelo@gmail.com",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_admin_user(self):
        authentication(self, self.users.data_adm)
        response = self.client.post(self.url, data=self.newUser)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class updatePermissionsTestCase(APITestCase):
    def setUp(self):
        self.users = SetupUsers()
        self.url = reverse(
            "users:permission_update", kwargs={"pk": self.users.normal.id}
        )
        self.newData = {"is_superuser": True}

    def test_update_user_permission_with_not_user_authenticated(self):
        response = self.client.patch(self.url, data=self.newData)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_permission_with_normal_user_authenticated(self):
        authentication(self, self.users.data_normal)
        response = self.client.patch(self.url, data=self.newData)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_permission_with_user_pk_not_found(self):
        urlPkNotFound = reverse("users:permission_update", kwargs={"pk": 3131232})
        authentication(self, self.users.data_adm)
        response = self.client.patch(urlPkNotFound, data=self.newData)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_permission_with_not_provided_fields(self):
        authentication(self, self.users.data_adm)
        response = self.client.patch(self.url, data={"xadrez": False})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_permission_with_admin_user_authenticated_no_change(self):
        authentication(self, self.users.data_adm)
        response = self.client.patch(
            self.url, data={"is_superuser": self.users.normal.is_superuser}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_permission_with_admin_user_authenticated(self):
        authentication(self, self.users.data_adm)
        response = self.client.patch(self.url, data=self.newData)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChangePasswordView(APITestCase):
    def setUp(self):
        self.users = SetupUsers()
        self.url = reverse("users:change_password", kwargs={"pk": self.users.normal.id})
        self.new_password = {
            "old_password": self.users.data_normal["password"],
            "new_password": "homem-aranha",
            "new_password_confirm": "homem-aranha",
        }

    def test_change_password_with_not_user_authenticated(self):
        response = self.client.patch(self.url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_user_not_found(self):
        authentication(self, data=self.users.data_normal)
        url = reverse("users:change_password", kwargs={"pk": 122131})
        response = self.client.patch(url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_password_different_user_by_normal_user(self):
        authentication(self, data=self.users.data_normal)
        url = reverse("users:change_password", kwargs={"pk": self.users.admin.id})
        response = self.client.patch(url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password_new_password_not_provided(self):
        authentication(self, data=self.users.data_normal)
        response = self.client.patch(self.url, data={"new_password": "1s231321"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_new_password_confirm_not_provided(self):
        authentication(self, data=self.users.data_normal)
        response = self.client.patch(
            self.url, data={"new_password_confirm": "12313f21"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_new_passwords_not_equal(self):
        authentication(self, data=self.users.data_normal)
        response = self.client.patch(
            self.url,
            data={"new_password": "1231231", "new_password_confirm": "12313f21"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_token_require_old_password(self):
        authentication(self, data=self.users.data_normal)
        response = self.client.patch(
            self.url,
            data={
                "new_password": self.users.data_normal["password"],
                "new_password_confirm": self.users.data_normal["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_adm_dont_need_old_password(self):
        authentication(self, data=self.users.data_adm)
        response = self.client.patch(
            self.url,
            data={
                "new_password": self.users.data_normal["password"],
                "new_password_confirm": self.users.data_normal["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_by_user(self):
        authentication(self, data=self.users.data_normal)
        response = self.client.patch(self.url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_token_can_skip_old_password(self):
        authentication_super_token(self, self.users.normal)
        response = self.client.patch(
            self.url,
            data={
                "new_password": self.users.data_normal["password"],
                "new_password_confirm": self.users.data_normal["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_different_user_by_admin_user(self):
        authentication(self, self.users.data_adm)
        url = reverse("users:change_password", kwargs={"pk": self.users.normal.id})
        response = self.client.patch(
            url,
            data={
                "new_password": self.users.data_normal["password"],
                "new_password_confirm": self.users.data_normal["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
