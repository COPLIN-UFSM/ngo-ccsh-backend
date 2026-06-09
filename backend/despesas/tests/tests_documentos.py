from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from despesas.tests import DespesasTestAPI
from despesas.models import TipoDocumento, Documento, Transacao


class TipoDocumentoViewSetTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:tipos_documentos-list")
        self.tipo_doc = TipoDocumento.objects.create(tipo_documento="Nota Fiscal")

    def test_get_tipos_documento_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tipo_documento(self):
        self.authentication(self.user_data_normal)
        data = {"tipo_documento": "Fatura"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tipo_documento_bad_request(self):
        self.authentication(self.user_data_normal)
        data = {}  # Missing tipo_documento
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_create_duplicate_tipo_documento(self):
        self.authentication(self.user_data_adm)
        response = self.client.post(self.url, data={"tipo_documento": "Nota Fiscal"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DocumentoViewSetTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_finalidade()
        self.create_basic_data()
        self.url_list = reverse("despesas:documentos-list")
        self.tipo_doc = TipoDocumento.objects.create(tipo_documento="Recibo")
        self.transacao = Transacao.objects.create(empenho=self.empenho, usuario=self.user_normal, montante=100.00, subunidade_executora=self.subunidade)
        self.documento = Documento.objects.create(tipo_documento=self.tipo_doc, transacao=self.transacao, descricao="Recibo 1")


    def test_get_documentos_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_documento(self):
        self.authentication(self.user_data_normal)
        data = {"tipo_documento": self.tipo_doc.pk, "transacao": self.transacao.pk, "documento": "7FDSFSDJ", "descricao": "Recibo 2"}
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_documento_bad_request(self):
        self.authentication(self.user_data_normal)
        data = {
            "transacao": self.transacao.pk,
            "descricao": "Recibo 2",
        }
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
