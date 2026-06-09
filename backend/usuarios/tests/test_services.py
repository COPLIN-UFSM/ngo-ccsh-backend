from django.test import TestCase
from django.core import mail
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken

from ..services import (
    create_token_with_allow_password_change,
    is_token_valid,
    send_email_reset_password,
)
from ..models import Usuario


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

        # verifica se o e-mail foi enviado
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        # verifica o assunto
        self.assertEqual(
            email.subject,
            f"{settings.APP_FULL_NAME} - Recuperação de Senha"
        )

        # verifica o recipiente
        self.assertEqual(email.to, [self.user.email])

        # o token deve aparecer no corpo da mensagem
        self.assertIn(token, email.body)
