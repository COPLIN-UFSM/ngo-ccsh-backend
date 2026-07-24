from rest_framework.test import APITestCase

from entidades.models import Cargo, Pessoa, Servidor
from usuarios.models import Usuario


class BaseServidorTestCase(APITestCase):
    """
    Classe que fornece pessoas e servidores pré-criados para uso em outros testes.
    """
    @classmethod
    def setUpTestData(cls):
        cls.cargo_professor = Cargo.objects.create(
            cargo="Professor"
        )
        cls.pessoa_ativa = Pessoa.objects.create(
            nome_pessoa="Loki",
            cpf="00000000000",
            rg="00000000000"
        )
        cls.pessoa_inativa = Pessoa.objects.create(
            nome_pessoa="Odin",
            cpf="00000000001",
            rg="00000000001"
        )
        cls.pessoa_outra = Pessoa.objects.create(
            nome_pessoa="Thor",
            cpf="00000000002",
            rg="00000000002"
        )
        cls.pessoa_nao_servidora = Pessoa.objects.create(
            nome_pessoa="Valkyria",
            cpf="00000000003",
            rg="00000000003"
        )
        cls.pessoa_superusuaria = Pessoa.objects.create(
            nome_pessoa="Baldur",
            cpf="00000000004",
            rg="00000000004"
        )
        cls.servidor_ativo = Servidor.objects.create(
            pessoa=cls.pessoa_ativa,
            matricula="00000000000",
            cargo=cls.cargo_professor,
            ativo=True
        )
        cls.servidor_inativo = Servidor.objects.create(
            pessoa=cls.pessoa_inativa,
            matricula="00000000001",
            cargo=cls.cargo_professor,
            ativo=True
        )

        cls.servidor_outro = Servidor.objects.create(
            pessoa=cls.pessoa_outra,
            matricula="00000000002",
            cargo=cls.cargo_professor,
            ativo=True
        )
        cls.servidor_superusuario = Servidor.objects.create(
            pessoa=cls.pessoa_superusuaria,
            matricula="00000000004",
            cargo=cls.cargo_professor,
            ativo=True
        )
        cls.usuario_ativo_raw_password = "1234"
        cls.usuario_inativo_raw_password = "1234"
        cls.usuario_super_raw_password = "1234"


from django.urls import reverse

class BaseAuthenticatedUserTestCase(BaseServidorTestCase):
    """
    Classe que fornece usuários pré-criados para uso em outros testes.
    """
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.usuario_ativo = Usuario.objects.create_user(
            cpf=cls.servidor_ativo.pessoa.cpf,
            email="loki@example.com",
            password="1234",
            is_active=True,
        )
        cls.usuario_inativo = Usuario.objects.create_user(
            cpf=cls.servidor_inativo.pessoa.cpf,
            email="odin@example.com",
            password="1234",
            is_active=False,
        )
        cls.servidor_inativo.ativo=False

        cls.usuario_outro = Usuario.objects.create_user(
            cpf=cls.servidor_outro.pessoa.cpf,
            email="thor@example.com",
            password="1234",
            is_active=True,
        )
        cls.superusuario = Usuario.objects.create_superuser(
            cpf=cls.servidor_superusuario.pessoa.cpf,
            email="baldur@example.com",
            password="1234",
            is_active=True,
            is_superuser=True
        )

        # Raw passwords for use in tests
        cls.usuario_ativo_raw_password = "1234"
        cls.usuario_inativo_raw_password = "1234"
        cls.usuario_super_raw_password = "1234"

        # Common user credential dicts for tests
        cls.user_data_adm = {"cpf": cls.usuario_ativo.cpf, "password": cls.usuario_ativo_raw_password}
        cls.user_data_normal = {"cpf": cls.usuario_outro.cpf, "password": cls.usuario_ativo_raw_password}

    def authentication(self, data):
        """Authenticate the test client using the project's login endpoint and set JWT Authorization header."""
        url_auth = reverse("autenticacao:login")
        response = self.client.post(url_auth, data=data)
        # In case login failed, raise to surface the issue during tests
        self.assertEqual(200, response.status_code)
        token = response.data.get("token")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
