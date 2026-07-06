from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from entidades.models import Servidor, Cargo, Pessoa
from usuarios.models import Usuario
from autenticacao.services import create_token_with_allow_password_change


class UserTestCase(APITestCase):
    def setUp(self):
        """
        Cria usuários para testes.
        """
        self.cargo_analista = Cargo.objects.create(
            cargo="Analista"
        )
        self.pessoa_1 = Pessoa.objects.create(
            nome_pessoa="Loki",
            cpf="00000000000",
            rg="00000000000"
        )
        self.pessoa_2 = Pessoa.objects.create(
            nome_pessoa="Odin",
            cpf="00000000001",
            rg="00000000001"
        )
        self.pessoa_3 = Pessoa.objects.create(
            nome_pessoa="Thor",
            cpf="00000000002",
            rg="00000000002"
        )
        self.pessoa_4 = Pessoa.objects.create(
            nome_pessoa="Valkyrie",
            cpf="00000000003",
            rg="00000000003"
        )
        self.servidor_1 = Servidor.objects.create(
            pessoa=self.pessoa_1,
            matricula="0000000",
            cargo=self.cargo_analista,
            ativo=True
        )
        self.servidor_2 = Servidor.objects.create(
            pessoa=self.pessoa_2,
            matricula="0000001",
            cargo=self.cargo_analista,
            ativo=True
        )
        self.servidor_3 = Servidor.objects.create(
            pessoa=self.pessoa_3,
            matricula="0000002",
            cargo=self.cargo_analista,
            ativo=True
        )
        self.servidor_4 = Servidor.objects.create(
            pessoa=self.pessoa_4,
            matricula="0000003",
            cargo=self.cargo_analista,
            ativo=True
        )

        self.usuario_admin_raw_password = "1234"
        self.usuario_regular_raw_password = "1234"
        self.usuario_inactive_raw_password = "1234"

        self.user_admin = Usuario.objects.create_superuser(
            cpf=self.servidor_1.pessoa.cpf,
            email="loki@gmail.com",
            password=self.usuario_admin_raw_password,
            is_active=True,
            is_superuser=True
        )
        self.user_regular = Usuario.objects.create_user(
            cpf=self.servidor_2.pessoa.cpf,
            email="odin@gmail.com",
            password=self.usuario_regular_raw_password,
            is_active=True,
            is_superuser=False
        )
        self.user_inactive = Usuario.objects.create_user(
            cpf=self.servidor_3.pessoa.cpf,
            email="thor@gmail.com",
            password=self.usuario_inactive_raw_password,
            is_active=False,
            is_superuser=False
        )

    def authenticate_with_invalid_token(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer invalid_token"
        )

    def authenticate(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def authenticate_with_reset_password_token(self, user):
        token = create_token_with_allow_password_change(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class UserListViewTestCase(UserTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("usuarios:user_list")
        self.new_user_data = {
            "cpf": self.servidor_4.pessoa.cpf,
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
                "cpf": self.servidor_4.pessoa.cpf,
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
                "cpf": self.servidor_4.pessoa.cpf,
                "password": "TartarugaNinja",
                "password2": "TheNinja",
                "email": "escultordonatelo@gmail.com",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserDetailsViewTestCase(UserTestCase):
    def setUp(self):
        super().setUp()
        self.url = lambda x: reverse("usuarios:user_details", kwargs={"id": x})
        self.new_user_data = {
            "email": "sasuke@gmail.com",
            "full_name": "Sasuke Uchiha",
        }

    # GET
    def test_get_user_details_while_not_authenticated(self):
        response = self.client.get(self.url(self.user_regular.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_details_with_user_not_found(self):
        self.authenticate(user=self.user_regular)
        response = self.client.get(self.url(999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_user_details_with_valid_user(self):
        for auth_user in [self.user_regular, self.user_admin]:
            self.authenticate(user=auth_user)
            for query_user in [self.user_regular, self.user_admin]:
                response = self.client.get(self.url(query_user.id))
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    # PATCH
    def test_update_user_details_while_not_authenticated(self):
        self.authenticate_with_invalid_token()
        response = self.client.patch(self.url(self.user_regular.id), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_details_with_user_not_found(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(999999), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_admin_details_while_being_regular_user(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(self.user_admin.id), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_regular_user_details_while_being_admin_user(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(self.url(self.user_regular.id), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_user_details_with_invalid_fields(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(self.user_regular.id), data={"email": "email_bad_format"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_details_with_non_existing_fields(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(
            self.url(self.user_regular.id),
            data={"field_doesnt_exists": "oii"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_self_details_with_valid_fields(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(self.user_regular.id), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_regular_user_tries_to_grant_themselves_admin_privilege(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(
            self.url(self.user_regular.id),
            data={"is_superuser": True}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_admin_user_tries_to_demote_themselves(self):
        self.authenticate(user=self.user_admin)
        response = self.client.patch(
            self.url(self.user_admin.id),
            data={"is_superuser": False}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_user_permission_while_being_admin_user(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(self.url(self.user_regular.id), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_regular_user_permission_while_being_admin_user(self):
        self.authenticate(self.user_admin)

        for is_superuser in [True, False]:
            response = self.client.patch(self.url(self.user_regular.id), data={"is_superuser": is_superuser})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    # DELETE
    def test_tries_to_delete_user_while_not_authenticated(self):
        self.authenticate_with_invalid_token()
        response = self.client.delete(self.url(self.user_regular.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_user_with_user_not_found(self):
        self.authenticate(user=self.user_regular)
        response = self.client.delete(self.url(999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_tries_to_delete_themselves(self):
        for auth_user in [self.user_regular, self.user_admin]:
            self.authenticate(user=auth_user)
            response = self.client.delete(self.url(auth_user.id))
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_regular_user_while_being_admin_user(self):
        self.authenticate(self.user_admin)
        response = self.client.delete(self.url(self.user_regular.id), data=self.new_user_data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_other_admin_user_while_being_an_admin_user(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(self.url(self.user_regular.id), data={'is_superuser': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.delete(self.url(self.user_regular.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ChangePasswordViewTestCase(UserTestCase):
    def setUp(self):
        super().setUp()
        self.url = lambda x: reverse("usuarios:change_password", kwargs={"id": x})
        self.new_password = {
            "password1": "spider_man",
            "password2": "spider_man",
        }

    def test_change_self_password_while_not_logged_in(self):
        self.authenticate_with_invalid_token()
        response = self.client.post(self.url(self.user_regular.id), data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_self_password_while_not_authenticated(self):
        response = self.client.patch(self.url(self.user_regular.id), data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_user_not_found(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(122131), data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_other_user_password_while_being_regular_user(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(self.user_admin.id), data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_other_user_password_while_being_admin(self):
        self.authenticate(self.user_admin)
        response = self.client.patch(
            self.url(self.user_regular.id),
            data={
                "password1": self.new_password["password1"],
                "password2": self.new_password["password2"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_missing_fields(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(self.user_regular.id), data={"password1": "1s231321"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.patch(self.url(self.user_regular.id), data={"password2": "1s231321"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # not_identical

    def test_change_password_with_not_identical_passwords_fields(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(
            self.url(self.user_regular.id),
            data={
                "password1": self.new_password['password1'],
                "password2": self.new_password['password1'] + '!'
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_correct_request_to_change_password(self):
        self.authenticate(user=self.user_regular)
        response = self.client.patch(self.url(self.user_regular.id), data=self.new_password)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_with_reset_token(self):
        self.authenticate_with_reset_password_token(self.user_regular)
        response = self.client.patch(
            self.url(self.user_regular.id),
            data={
                "password1": self.new_password["password1"],
                "password2": self.new_password["password2"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
