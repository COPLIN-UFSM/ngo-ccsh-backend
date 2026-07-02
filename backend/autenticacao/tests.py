from django.core import mail
from django.test import TestCase
from django.urls import reverse

from entidades.models import Pessoa, Servidor, Cargo
from ngo_ccsh import settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from usuarios.models import Usuario, UserManager

from autenticacao.services import (
    create_token_with_allow_password_change,
    is_token_valid,
    send_email_reset_password,
)

class AuthenticationBaseTestCase(APITestCase):
    def setUp(self):
        self.cargo_professor = Cargo.objects.create(
            cargo="Professor"
        )
        self.pessoa_ativa = Pessoa.objects.create(
            nome_pessoa="Loki",
            cpf="00000000000",
            rg="00000000000"
        )
        self.pessoa_inativa = Pessoa.objects.create(
            nome_pessoa="Odin",
            cpf="00000000001",
            rg="00000000001"
        )
        self.servidor_ativo_1 = Servidor.objects.create(
            pessoa=self.pessoa_ativa,
            matricula="123456789",
            cargo=self.cargo_professor,
            ativo=True
        )
        self.servidor_ativo_2 = Servidor.objects.create(
            pessoa=self.pessoa_inativa,
            matricula="987654321",
            cargo=self.cargo_professor,
            ativo=True
        )
        self.usuario_ativo_raw_password = "1234"
        self.usuario_inativo_raw_password = "1234"

        self.usuario_ativo = Usuario.objects.create_user(
            cpf=self.servidor_ativo_1.pessoa.cpf,
            email="loki@gmail.com",
            password=self.usuario_ativo_raw_password,
            is_active=True,
        )
        self.usuario_inativo = Usuario.objects.create_user(
            cpf=self.servidor_ativo_2.pessoa.cpf,
            email="odin@gmail.com",
            password=self.usuario_inativo_raw_password,
            is_active=False,
        )

class LoginViewTestCase(AuthenticationBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("autenticacao:login")

    def test_login_cpf_not_provided(self):
        data = {
            "password": self.usuario_ativo.password,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_password_not_provided(self):
        data = {
            "cpf": self.usuario_ativo.pessoa.cpf,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_password(self):
        data = {
            "cpf": self.usuario_ativo.pessoa.cpf,
            "password": self.usuario_ativo_raw_password + '!',
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_wrong_username(self):
        data = {
            "cpf": str(self.usuario_ativo.pessoa.cpf)[:-1] + '!',
            "password": self.usuario_ativo_raw_password,
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_not_active(self):
        response = self.client.post(self.url, data={
            "cpf": self.usuario_inativo.pessoa.cpf,
            "password": self.usuario_inativo_raw_password,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_user_active(self):
        data = {
            "cpf": self.usuario_ativo.pessoa.cpf,
            "password": self.usuario_ativo_raw_password,
        }
        response = self.client.post(self.url, data=data)
        self.assertIn("token", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_unauthorized_methods(self):
        response_get = self.client.get(self.url)
        response_patch = self.client.patch(self.url)
        response_delete = self.client.delete(self.url)

        self.assertEqual(response_get.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class RecoverPasswordViewTestCase(AuthenticationBaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("autenticacao:recuperar_senha")

    def test_recover_password_without_email(self):
        response = self.client.post(self.url, data=dict())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recover_password_with_unknown_email(self):
        response = self.client.post(self.url, data={"email": self.usuario_ativo.email + '!'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recover_password_with_valid_email(self):
        response = self.client.post(self.url, data={"email": self.usuario_ativo.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokensServiceTest(AuthenticationBaseTestCase):
    def test_token_invalid(self):
        self.assertFalse(is_token_valid("um token invalido"))

    def test_token_valid(self):
        token = AccessToken.for_user(user=self.usuario_ativo)
        self.assertTrue(is_token_valid(token))


class PasswordResetServiceTest(AuthenticationBaseTestCase):
    def test_token_allows_alter_password_with_not_password(self):
        token = create_token_with_allow_password_change(user=self.usuario_ativo)
        self.assertTrue(token)
        self.assertTrue(token["allow_password_change"])
        self.assertTrue(is_token_valid(token))

    def test_send_email_reset_password_success(self):
        token = "token-de-teste-123"
        send_email_reset_password(self.usuario_ativo, token)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(email.subject, f"{settings.APP_FULL_NAME} - Recuperação de Senha")
        self.assertEqual(email.to, [self.usuario_ativo.email])

        self.assertIn(token, email.body)  # type: ignore
