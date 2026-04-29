from django.test import TestCase
from ..models import Usuario


class CreateUser(TestCase):
    def test_create_user(self):
        data = {
            "username": "leandro",
            "password": "lindoelegal",
            "email": "leandronascimento@gmail.com",
        }
        user = Usuario.objects.create_user(**data)

        self.assertEqual(user.username, data["username"])
        self.assertEqual(user.email, data["email"])
        self.assertNotEqual(user.password, data["password"])
        self.assertFalse(user.is_superuser)

    def test_create_super_user(self):
        data = {
            "username": "leandro",
            "password": "lindoelegal",
            "email": "leandronascimento@gmail.com",
        }
        user = Usuario.objects.create_superuser(**data)

        self.assertEqual(user.username, data["username"])
        self.assertEqual(user.email, data["email"])
        self.assertNotEqual(user.password, data["password"])
        self.assertTrue(user.is_superuser)
        
