from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# from usuarios.models import Usuario
from despesas.models import Transacao
from despesas.tests.tests_empenhos import SetupTestAPI


class TransacoesTestAPI(APITestCase, SetupTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_finalidade()
        self.create_basic_data()
        self.url = reverse("despesas:transacoes-list")
        self.data = {
           
        }

    def test_create_transaction_with_fields_missing(self):
        self.authentication(self.user_data_normal)
        data = {
            "finalidade": self.finalidade.pk,
            "empenho": self.empenho.pk,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            # "montante": 1.1,
            "eh_credito": True
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_transaction_with_negative_montante_in_empenho(self):
        self.authentication(self.user_data_normal)
        data = {
            "finalidade": self.finalidade.pk,
            "empenho": self.empenho.pk,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            "montante": 1000,
            "eh_credito": False
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_transaction(self):
        self.authentication(self.user_data_normal)
        data = {
            "finalidade": self.finalidade.pk,
            "empenho": self.empenho.pk,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            "montante": 1000,
            "eh_credito": True,
            "unidade_executora": self.subunidade.pk
        }
        response = self.client.post(self.url, data=data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_transaction_with_positive_montante_in_empenho(self):
        self.authentication(self.user_data_normal)
        data = {
            "finalidade": self.finalidade.pk,
            "empenho": self.empenho.pk,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            "montante": 1000,
            "eh_credito": True,
            "unidade_executora": self.subunidade.pk
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, 201)

        response = self.client.post(self.url, data={
            "finalidade": self.finalidade.pk,
            "empenho": self.empenho.pk,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            "eh_credito": False, 
            "montante": 900,
            "unidade_executora": self.subunidade.pk

        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_create_transacao_invalid_empenho(self):
        self.authentication(self.user_data_adm)
        data = {
            "finalidade": self.finalidade.pk,
            "empenho": 9999,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            "montante": 1000,
            "eh_credito": True
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_transacao(self):
        transacao = Transacao.objects.create(
            finalidade=self.finalidade,
            empenho=self.empenho,
            usuario=self.user_normal,
            status="PAGO",
            descricao="Blá blá blá.........",
            montante=1000,
            eh_credito=True,
            subunidade_executora=self.subunidade
        )
        url_del = reverse(
            "despesas:transacoes-detail", kwargs={"pk": transacao.id_transacao}
        )

        self.authentication(self.user_data_adm)
        response = self.client.delete(url_del)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Transacao.objects.filter(pk=transacao.id_transacao).exists()
        )

    def test_create_transacao_with_inactive_empenho(self):
        self.empenho.ativo = False
        self.empenho.save()
        self.authentication(self.user_data_adm)

        data = {
            "finalidade": self.finalidade.id_finalidade,
            "empenho": self.empenho.id_empenho,
            "usuario": self.user_normal.id,
            "status": "PAGO",
            "descricao": "Blá blá blá.........",
            "montante": 1000,
            "eh_credito": True,
            "unidade_executora": self.subunidade.id_subunidade
        }

        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_transaction_unauthenticated(self):
        data = {
            "finalidade": self.finalidade.pk,
            "empenho": self.empenho.pk,
            "usuario": self.user_normal.pk,
            "status": "PAGO",
            "descricao": "Sem auth",
            "montante": 100,
            "eh_credito": True,
            "unidade_executora": self.subunidade.pk
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_transaction_insufficient_funds(self):
        self.authentication(self.user_data_normal)
        # Primeiro, criamos um crédito pequeno de R$ 500
        Transacao.objects.create(
            finalidade=self.finalidade,
            empenho=self.empenho,
            usuario=self.user_normal,
            status="PAGO",
            descricao="Crédito",
            montante=500,
            eh_credito=True,
            subunidade_executora=self.subunidade
        )

        # Agora, tentamos fazer uma despesa de R$ 600 (maior que o saldo de R$ 500)
        data = {
            "finalidade": self.finalidade.id_finalidade,
            "empenho": self.empenho.id_empenho,
            "usuario": self.user_normal.id,
            "status": "PAGO",
            "descricao": "Despesa sem saldo suficiente",
            "montante": 600,
            "eh_credito": False,
            "unidade_executora": self.subunidade.id_subunidade
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("montante", response.data)

    def test_create_transaction_with_nested_documents(self):
        self.authentication(self.user_data_normal)
        data = {
            "finalidade": self.finalidade.id_finalidade,
            "empenho": self.empenho.id_empenho,
            "usuario": self.user_normal.id,
            "status": "PAGO",
            "descricao": "Transação com documentos",
            "montante": 500,
            "eh_credito": True,
            "unidade_executora": self.subunidade.id_subunidade,
            "documentos": [
                {
                    "id_tipo_documento": self.tipo_doc.id_tipo_documento,
                    "documento": "NF-12345",
                    "descricao": "Nota fiscal de teste"
                }
            ]
        }
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar se a transação e o documento aninhado foram criados no banco
        transacao_id = response.data["id_transacao"]
        self.assertTrue(Transacao.objects.filter(pk=transacao_id).exists())
        transacao = Transacao.objects.get(pk=transacao_id)
        self.assertEqual(transacao.documentos.count(), 1)
        self.assertEqual(transacao.documentos.first().documento, "NF-12345")

    def test_update_transaction_and_documents(self):
        self.authentication(self.user_data_adm)
        # Cria uma transação inicial com um documento
        transacao = Transacao.objects.create(
            finalidade=self.finalidade,
            empenho=self.empenho,
            usuario=self.user_normal,
            status="PENDENTE",
            descricao="Transação inicial",
            montante=300,
            eh_credito=True,
            subunidade_executora=self.subunidade
        )
        from despesas.models import Documento
        Documento.objects.create(
            tipo_documento=self.tipo_doc,
            documento="NF-OLD",
            transacao=transacao,
            descricao="Documento antigo"
        )

        url_update = reverse(
            "despesas:transacoes-detail", kwargs={"pk": transacao.id_transacao}
        )

        # Atualizar a transação alterando a descrição e substituindo os documentos
        data = {
            "finalidade": self.finalidade.id_finalidade,
            "empenho": self.empenho.id_empenho,
            "usuario": self.user_normal.id,
            "status": "PAGO",
            "descricao": "Transação atualizada",
            "montante": 300,
            "eh_credito": True,
            "unidade_executora": self.subunidade.id_subunidade,
            "documentos": [
                {
                    "id_tipo_documento": self.tipo_doc.id_tipo_documento,
                    "documento": "NF-NEW",
                    "descricao": "Novo documento"
                }
            ]
        }
        response = self.client.put(url_update, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        transacao.refresh_from_db()
        self.assertEqual(transacao.status, "PAGO")
        self.assertEqual(transacao.descricao, "Transação atualizada")
        self.assertEqual(transacao.documentos.count(), 1)
        self.assertEqual(transacao.documentos.first().documento, "NF-NEW")
