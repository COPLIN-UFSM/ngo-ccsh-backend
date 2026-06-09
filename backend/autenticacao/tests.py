from django.urls import reverse
from django.test import TestCase
from django.core import mail

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from usuarios.models import Usuario
from usuarios.tests.test_views import UserTestAPI

from autenticacao.services import (
    create_token_with_allow_password_change,
    is_token_valid,
    send_email_reset_password,
)

# Create your tests here.
class LoginViewTestCase(APITestCase, UserTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_user_not_active()
        self.url = reverse("autenticacao:login")

    def test_login_username_not_provided(self):
        data = {
            "password": self.user_data_normal["password"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_password_not_provided(self):
        data = {
            "username": self.user_data_normal["username"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_password_failed_authentication(self):
        data = {
            "username": self.user_data_normal["username"],
            "password": "password_failed",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_username_failed_authentication(self):
        data = {
            "username": "users1231",
            "password": self.user_data_normal["password"],
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_not_active(self):
        response = self.client.post(self.url, data=self.user_data_not_active)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_authenticated(self):
        response = self.client.post(self.url, data=self.user_data_normal)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_methods_not_authorized(self):
        response_get = self.client.get(self.url)
        response_patch = self.client.patch(self.url)
        response_delete = self.client.delete(self.url)

        self.assertEqual(response_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class RecoverPasswordViewTestCase(APITestCase, UserTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("autenticacao:recover_password")
        self.data = {"email": self.user_normal.email}

    def test_recover_password_with_email_not_provided(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recover_password_with_email_not_found(self):
        response = self.client.post(self.url, data={"email": "deadpool@gmail.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recover_password_with_email_valid(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserTestDataMixin:
    def create_test_user(self):
        self.user_data = {
            "username": "loki",
            "email": "loki@gmail.com",
            "password": "olámundo",
        }
        return Usuario.objects.create_user(**self.user_data)


class TokensServiceTest(TestCase, UserTestDataMixin):
    def setUp(self):
        self.user = self.create_test_user()

    def test_token_invalid(self):
        self.assertFalse(is_token_valid("um token invalido"))

    def test_token_valid(self):
        token = AccessToken.for_user(user=self.user)
        self.assertTrue(is_token_valid(token))


class PasswordResetServiceTest(TestCase, UserTestDataMixin):
    def setUp(self):
        self.user = self.create_test_user()

    def test_token_allows_alter_password_with_not_password(self):
        token = create_token_with_allow_password_change(user=self.user)
        self.assertTrue(token)
        self.assertTrue(token["allow_password_change"])
        self.assertTrue(is_token_valid(token))

    def test_send_email_reset_password_success(self):
        token = "token-de-teste-123"
        send_email_reset_password(self.user, token)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(email.subject, "Portal Transparência CCSH - Recuperação de Senha")
        self.assertEqual(email.to, [self.user.email])

        self.assertIn(token, email.body)  # type: ignore
