from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from usuarios.models import Usuario
from autenticacao.services import create_token_with_allow_password_change


class UserTestMixin(object):
    def create_users(self):
        """
        Cria usuários para testes.
        """
        self.user_admin = Usuario.objects.create_superuser(
            username="admin",
            email="admin@gmail.com",
            password="adminpass"
        )
        self.user_regular = Usuario.objects.create_user(
            username="user",
            email="user@gmail.com",
            password="userpass"
        )
        self.user_inactive = Usuario.objects.create_user(
            username="user_not_active",
            email="user2@gmail.com",
            password="userpass2",
            is_active=False,
        )

    @property
    def user_admin_credentials(self):
        return {
            "id": 1,
            "username": self.user_admin.username,
            "password": "adminpass",
        }

    @property
    def user_regular_credentials(self):
        return {
            "id": 2,
            "username": self.user_regular.username,
            "password": "userpass",
        }

    @property
    def user_inactive_credentials(self):
        return {
            "id": 3,
            "username": self.user_inactive.username,
            "password": "userpass2",
        }

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def authenticate_with_reset_password_token(self, user):
        token = create_token_with_allow_password_change(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class UserListViewTestCase(APITestCase, UserTestMixin):
    def setUp(self):
        self.create_users()
        self.url = reverse("usuarios:userList")
        self.new_user_data = {
            "username": "1234",
            "full_name": "Goku",
            "is_superuser": False,
            "email": "goku@capsulecorporation.com",
            "password": "vegeta",
            "password2": "vegeta"
        }

    def test_get_users_while_not_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_users_while_authenticated(self):
        self.authenticate(self.user_regular)
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_register_user_while_not_authenticated(self):
        response = self.client.post(self.url, self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_user_while_being_regular_user(self):
        self.authenticate(self.user_regular)
        response = self.client.post(self.url, data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_user_while_being_admin_user(self):
        self.authenticate(self.user_admin)
        response = self.client.post(self.url, data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_user_with_confirm_password_field_not_filled(self):
        self.authenticate(self.user_admin)
        response = self.client.post(
            self.url,
            data={
                "username": "Donatelo",
                "password": "TartarugaNinja",
                "email": "escultordonatelo@gmail.com",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_not_identical_passwords_fields(self):
        self.authenticate(self.user_admin)
        response = self.client.post(
            self.url,
            data={
                "username": "Donatelo",
                "password": "TartarugaNinja",
                "password2": "TheNinja",
                "email": "escultordonatelo@gmail.com",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# TODO testar outra coisa depois! fazer refletir view!
class UpdatePermissionsTestCase(APITestCase, UserTestMixin):
    def setUp(self):
        self.create_users()
        self.url = reverse("usuarios:userDetails")
        self.new_user_data = {
            "username": "1234",
            "full_name": "Goku",
            "is_superuser": True,
            "email": "goku@capsulecorporation.com",
            "password": "vegeta",
            "password2": "vegeta"
        }

    def test_update_user_permission_while_not_authenticated(self):
        response = self.client.patch(
            reverse(self.url, kwargs={"id_usuario": self.user_regular.id}),
            data=self.new_user_data
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_permission_while_being_regular_user(self):
        self.authenticate(self.user_regular_credentials)
        response = self.client.patch(
            reverse(self.url, kwargs={"id_usuario": self.user_regular.id}),
            data=self.new_user_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_permission_while_being_admin_user(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(
            reverse(self.url, kwargs={"id_usuario": self.user_regular.id}),
            data=self.new_user_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_permission_while_being_admin_user_and_no_changes(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(
            reverse(self.url, kwargs={"id_usuario": self.user_regular.id}),
            data={"is_superuser": self.user_regular.is_superuser}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_permission_with_user_not_found(self):
        url_not_found = reverse(self.url, kwargs={"id_usuario": 3131232})
        self.authenticate(self.user_admin)
        response = self.client.patch(url_not_found, data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_permission_with_wrong_fields(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(
            reverse(self.url, kwargs={"id_usuario": self.user_regular.id}),
            data={"xadrez": False}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

# TODO não revisado!

class ChangePasswordViewTestCase(UserTestMixin, APITestCase):
    def setUp(self):
        self.create_users()
        self.url = reverse("ChangePasswordView", kwargs={"id": self.user_regular.id})
        self.new_password = {
            "old_password": self.user_regular_credentials["password"],
            "password1": "spider_man",
            "password2": "spider_man",
        }

    def test_change_password_with_token_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token_invalid")
        response = self.client.post(self.url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_not_user_authenticated(self):
        response = self.client.patch(self.url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_user_not_found(self):
        self.authenticate(data=self.user_regular_credentials)
        url = reverse("ChangePasswordView", kwargs={"id_usuario": 122131})
        response = self.client.patch(url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_password_different_user_by_normal_user(self):
        self.authenticate(data=self.user_regular_credentials)
        url = reverse("ChangePasswordView", kwargs={"id_usuario": self.user_admin.id})
        response = self.client.patch(url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password_new_password_not_provided(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url, data={"password1": "1s231321"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_new_password_confirm_not_provided(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url, data={"password2": "12313f21"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_new_passwords_not_equal(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(
            self.url,
            data={"password1": "1231231", "password2": "12313f21"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_adm_dont_need_old_password(self):
        self.authenticate(data=self.user_admin_credentials)
        response = self.client.patch(
            self.url,
            data={
                "password1": self.user_regular_credentials["password"],
                "password2": self.user_regular_credentials["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_by_user(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url, data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_token_can_skip_old_password(self):
        self.authenticate_with_reset_password_token(self.user_regular)
        response = self.client.patch(
            self.url,
            data={
                "password1": self.user_regular_credentials["password"],
                "password2": self.user_regular_credentials["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_different_user_by_admin_user(self):
        self.authenticate(self.user_admin_credentials)
        url = reverse("ChangePasswordView", kwargs={"id_usuario": self.user_regular.id})
        response = self.client.patch(
            url,
            data={
                "password1": self.user_regular_credentials["password"],
                "password2": self.user_regular_credentials["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserDetailsViewTestCase(APITestCase, UserTestMixin):
    def setUp(self):
        self.create_users()
        self.url_normal = reverse("userDetailsView", kwargs={"id_usuario": self.user_regular.id})
        self.url_adm = reverse("userDetailsView", kwargs={"id_usuario": self.user_admin.id})
        self.data = {
            "email": "sasuke@gmail.com",
            "full_name": "Sasuke Uchiha",
        }

    def test_get_info_with_not_user_authenticated(self):
        response = self.client.get(self.url_normal)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_info_with_user_not_found(self):
        self.authenticate(data=self.user_regular_credentials)
        url = reverse("userDetailsView", kwargs={"id_usuario": 999999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_info_with_user_not_found(self):
        self.authenticate(data=self.user_regular_credentials)
        url = reverse("userDetailsView", kwargs={"id_usuario": 999999})
        response = self.client.patch(url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_info_different_user_by_normal_user(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url_adm, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_info_with_no_valid_fields(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url_normal, data={"email": "email_bad_format"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_info_with_non_existing_fields(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url_normal, {"field_dont_exists": "oii", "is_superuser": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_info_different_user_by_admin_user(self):
        self.authenticate(self.user_admin_credentials)
        response = self.client.patch(
            self.url_normal,
            data=self.data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_info_by_owner_user(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.patch(self.url_normal, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_user_with_not_user_authenticated(self):
        response = self.client.get(self.url_normal)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_user_with_user_not_found(self):
        url = reverse("userDetailsView", kwargs={"id_usuario": 9999999})
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_by_owner_user(self):
        self.authenticate(data=self.user_regular_credentials)
        response = self.client.get(self.url_normal)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_different_user_by_admin_user(self):
        self.authenticate(self.user_admin_credentials)
        response = self.client.patch(
            self.url_normal,
            data=self.data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
