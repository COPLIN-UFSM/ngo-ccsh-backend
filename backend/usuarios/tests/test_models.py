# from django.test import TestCase
#
# from entidades.models import Cargo, Pessoa, Servidor
# from ngo_ccsh.tests.mixins import BaseServidorTestCase
# from ..models import Usuario
#
#
# class CreateTestUsers(BaseServidorTestCase):
#     def test_create_user_with_active_employee(self):
#         self.usuario_ativo = Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="loki@gmail.com",
#             password=self.usuario_ativo_raw_password,
#             is_active=True,
#         )
#         self.assertTrue(self.usuario_ativo.is_active)
#
#     def test_create_user_valid_cpf_format_with_mask(self):
#         user = Usuario.objects.create_user(
#             cpf="000.000.000-00",
#             email="masked_cpf@gmail.com",
#             password="secure_password",
#         )
#         self.assertEqual(user.cpf, "00000000000")
#
#     def test_create_user_valid_email(self):
#         user = Usuario.objects.create_user(
#             cpf=self.servidor_outro.pessoa.cpf,
#             email="validemail@example.com",
#             password="secure_password",
#         )
#         self.assertEqual(user.email, "validemail@example.com")
#
#     def test_create_user_valid_password(self):
#         user = Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="password_test@gmail.com",
#             password="MySecurePassword123!",
#         )
#         self.assertTrue(user.check_password("MySecurePassword123!"))
#
#     def test_create_user_valid_is_active_true(self):
#         user = Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="active_test@gmail.com",
#             password="password",
#             is_active=True,
#         )
#         self.assertTrue(user.is_active)
#
#     def test_create_user_valid_is_active_false(self):
#         user = Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="inactive_test@gmail.com",
#             password="password",
#             is_active=False,
#         )
#         self.assertFalse(user.is_active)
#
#     def test_create_user_missing_cpf(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf="",
#                 email="nocpf@gmail.com",
#                 password="password",
#             )
#         self.assertIn("cpf", str(context.exception).lower())
#
#     def test_create_user_missing_email(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf=self.servidor_ativo.pessoa.cpf,
#                 email="",
#                 password="password",
#             )
#         self.assertIn("e-mail", str(context.exception).lower())
#
#     def test_create_user_none_cpf(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf=None,
#                 email="nonecpf@gmail.com",
#                 password="password",
#             )
#         self.assertIn("cpf", str(context.exception).lower())
#
#     def test_create_user_none_email(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf=self.servidor_ativo.pessoa.cpf,
#                 email=None,
#                 password="password",
#             )
#         self.assertIn("e-mail", str(context.exception).lower())
#
#     def test_create_user_nonexistent_cpf(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf="99999999999",
#                 email="nonexistent@gmail.com",
#                 password="password",
#             )
#         self.assertIn("não existe", str(context.exception).lower())
#
#     def test_create_user_with_inactive_employee(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf=self.servidor_inativo.pessoa.cpf,
#                 email="odin@gmail.com",
#                 password=self.usuario_inativo_raw_password,
#                 is_active=True,
#             )
#         self.assertIn("servidores ativos", str(context.exception).lower())
#
#     def test_create_user_with_non_employee_person(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf=self.pessoa_nao_servidora.cpf,
#                 email="valkyria@gmail.com",
#                 password="1234",
#                 is_active=True,
#             )
#         self.assertIn("servidores ativos", str(context.exception).lower())
#
#     def test_create_user_duplicate_cpf(self):
#         Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="first@gmail.com",
#             password="password",
#         )
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_user(
#                 cpf=self.servidor_ativo.pessoa.cpf,
#                 email="second@gmail.com",
#                 password="password",
#             )
#         self.assertIn("já existe", str(context.exception).lower())
#
#     def test_create_user_invalid_email_format(self):
#         user = Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="invalidemail",
#             password="password",
#         )
#         self.assertEqual(user.email, "invalidemail")
#
#     def test_create_user_duplicate_email(self):
#         Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="duplicate@gmail.com",
#             password="password",
#         )
#         with self.assertRaises(Exception):
#             Usuario.objects.create_user(
#                 cpf=self.servidor_outro.pessoa.cpf,
#                 email="duplicate@gmail.com",
#                 password="password",
#             )
#
#     def test_create_user_with_none_password(self):
#         user = Usuario.objects.create_user(
#             cpf=self.servidor_ativo.pessoa.cpf,
#             email="nopassword@gmail.com",
#             password=None,
#         )
#         self.assertFalse(user.check_password(None))
#
#
# class CreateSuperServidorTest(BaseServidorTestCase):
#
#     # Valid superuser creation tests
#     def test_create_superuser_with_valid_fields(self):
#         superuser = Usuario.objects.create_superuser(
#             cpf=self.servidor_superusuario.pessoa.cpf,
#             email="admin@gmail.com",
#             password="superpassword",
#         )
#         self.assertTrue(superuser.is_superuser)
#         self.assertTrue(superuser.is_active)
#
#     def test_create_superuser_has_is_superuser_true(self):
#         superuser = Usuario.objects.create_superuser(
#             cpf=self.servidor_superusuario.pessoa.cpf,
#             email="super@gmail.com",
#             password="password",
#         )
#         self.assertTrue(superuser.is_superuser)
#
#     def test_create_superuser_valid_email(self):
#         superuser = Usuario.objects.create_superuser(
#             cpf=self.servidor_superusuario.pessoa.cpf,
#             email="superadmin@example.com",
#             password="password",
#         )
#         self.assertEqual(superuser.email, "superadmin@example.com")
#
#     def test_create_superuser_valid_password(self):
#         superuser = Usuario.objects.create_superuser(
#             cpf=self.servidor_superusuario.pessoa.cpf,
#             email="pwd@gmail.com",
#             password="SuperSecure123!",
#         )
#         self.assertTrue(superuser.check_password("SuperSecure123!"))
#
#     def test_create_superuser_valid_cpf_with_mask(self):
#         superuser = Usuario.objects.create_superuser(
#             cpf="000.000.000-04",
#             email="masked@gmail.com",
#             password="password",
#         )
#         self.assertEqual(superuser.cpf, "00000000004")
#
#     # Invalid superuser creation tests
#     def test_create_superuser_missing_cpf(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf="",
#                 email="nosuper@gmail.com",
#                 password="password",
#             )
#         self.assertIn("cpf", str(context.exception).lower())
#
#     def test_create_superuser_missing_email(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf=self.servidor_superusuario.pessoa.cpf,
#                 email="",
#                 password="password",
#             )
#         self.assertIn("e-mail", str(context.exception).lower())
#
#     def test_create_superuser_nonexistent_cpf(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf="99999999999",
#                 email="nonexistent@gmail.com",
#                 password="password",
#             )
#         self.assertIn("não existe", str(context.exception).lower())
#
#     def test_create_superuser_with_inactive_employee(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf=self.pessoa_inativa.cpf,
#                 email="inactive@gmail.com",
#                 password="password",
#             )
#         self.assertIn("servidores ativos", str(context.exception).lower())
#
#     def test_create_superuser_invalid_email_format(self):
#         superuser = Usuario.objects.create_superuser(
#             cpf=self.servidor_superusuario.pessoa.cpf,
#             email="invalidsuperemail",
#             password="password",
#         )
#         self.assertEqual(superuser.email, "invalidsuperemail")
#
#     def test_create_superuser_cannot_force_is_superuser_false(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf=self.servidor_superusuario.pessoa.cpf,
#                 email="super_false@gmail.com",
#                 password="password",
#                 is_superuser=False,
#             )
#         self.assertIn("is_superuser", str(context.exception).lower())
#
#     def test_create_superuser_none_cpf(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf=None,
#                 email="nonesuper@gmail.com",
#                 password="password",
#             )
#         self.assertIn("cpf", str(context.exception).lower())
#
#     def test_create_superuser_none_email(self):
#         with self.assertRaises(ValueError) as context:
#             Usuario.objects.create_superuser(
#                 cpf=self.servidor_superusuario.pessoa.cpf,
#                 email=None,
#                 password="password",
#             )
#         self.assertIn("e-mail", str(context.exception).lower())
