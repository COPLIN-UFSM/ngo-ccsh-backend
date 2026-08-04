from django.urls import reverse
from rest_framework import status

from entidades.models import Email
from ngo_ccsh.tests.mixins import BaseAuthenticatedUserTestCase


class EmailViewSetTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.url = reverse("entidades:emails-list")
        self.email = Email.objects.create(email="morfeu@olimpo.com", pessoa=self.pessoa_ativa)
        self.data = {"email": "apolo@olimpo.com", "pessoa": self.pessoa_ativa.pk}

    def test_get_emails(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, response.data["count"])
        self.assertEqual(self.email.email, response.data["data"][0]["email"])

    def test_create_email_without_logged_user(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)

    def test_create_email(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.data, format="json")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(self.data['email'], response.data["email"])

    def test_create_and_verify_person_email(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data=self.data, format="json")
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        url = reverse("entidades:pessoas-detail", kwargs={"pk": self.pessoa_ativa.pk})
        response_pessoa = self.client.get(url)
        response_emails = response_pessoa.data['emails']
        match = next((e for e in response_emails if e["id_email"] == self.email.pk), None)
        self.assertNotEqual(None, match)

    def test_create_email_not_correct(self):
        self.authentication(self.user_data_adm)
        data = {"email": "poseidon@", "pessoa": self.pessoa_ativa.pk}
        response = self.client.post(self.url, data=data)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn("email", self.data)

    def test_create_email_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"correio_eletronico": "poseidon@gmail.com"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleEmailViewTestCase(BaseAuthenticatedUserTestCase):
    def setUp(self):
        self.email = Email.objects.create(email="morfeu@olimpo.com", pessoa=self.pessoa_ativa)
        self.data = {"email": "apolo@olimpo.com", "pessoa": self.pessoa_ativa.pk}

        self.urlPrefix = "entidades:emails-detail"
        self.url = reverse(self.urlPrefix, kwargs={"pk": self.email.pk})

    def test_get_single_email(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual("morfeu@olimpo.com", response.data["email"])

    def test_get_nonexistent_email(self):
        self.authentication(self.user_data_adm)
        url = reverse(self.urlPrefix, kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_patch_email(self):
        self.authentication(self.user_data_adm)
        response = self.client.patch(self.url, data=self.data)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data['email'], response.data['email'] )

    def test_patch_email_without_effect(self):
        self.authentication(self.user_data_adm)
        data = {"unidade": "Departamento B Editado"}
        response = self.client.patch(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_email(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
