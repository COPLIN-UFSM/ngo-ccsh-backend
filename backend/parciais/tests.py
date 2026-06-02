from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from usuarios.models import Usuario
from despesas.models import TipoDocumento, Transacao, Empenho, Finalidade, NaturezaFinalidade, TipoFinalidade


class PartialPaymentsTestAPI:
    """
    Mixin para auxiliar na criação de dados de teste e autenticação.
    """

    def create_test_users(self):
        self.user_admin = Usuario.objects.create_superuser(username="admin_test", email="admin_test@gmail.com", password="adminpass")
        self.user_normal = Usuario.objects.create_user(username="user_test", email="user_test@gmail.com", password="userpass")
        self.user_data_adm = {
            "username": self.user_admin.username,
            "password": "adminpass",
        }
        self.user_data_normal = {
            "username": self.user_normal.username,
            "password": "userpass",
        }

    def authentication(self, data):
        url_auth = reverse("autenticacao:login")
        response = self.client.post(url_auth, data=data)
        token = response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def create_finalidade(self):
        self.tipo_finalidade = TipoFinalidade.objects.create(tipo_finalidade="Bolsas")
        self.natureza_finalidade = NaturezaFinalidade.objects.create(natureza_finalidade="Custeio")
        self.finalidade = Finalidade.objects.create(
            tipo_finalidade=self.tipo_finalidade, natureza_finalidade=self.natureza_finalidade, finalidade="Bolsa 2A"
        )

    def create_basic_data(self):
        self.empenho = Empenho.objects.create(empenho="2024NE0001", descricao="Empenho de Teste", ativo=True, finalidade=self.finalidade)

        self.tipo_doc = TipoDocumento.objects.create(tipo_documento="Nota Fiscal", ativo=True)


class EmpenhoViewTestCase(APITestCase, PartialPaymentsTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_finalidade()
        self.url = reverse("despesas:empenhos")
        self.new_empenho = {
            "empenho": "2024NE0002",
            "descricao": "Novo Empenho",
            "finalidade": self.finalidade.id_finalidade,
        }

    def test_get_all_empenhos_not_authenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_empenhos_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_empenho(self):
        self.authentication(self.user_data_normal)
        response = self.client.post(self.url, data=self.new_empenho)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SingleEmpenhoViewTestCase(APITestCase, PartialPaymentsTestAPI):
    def setUp(self):
        self.create_test_users()
        self.create_finalidade()
        self.create_basic_data()
        self.url = reverse("despesas:single_empenho", kwargs={"pk": self.empenho.id_empenho})

    def test_get_empenho_details(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["empenho"], "2024NE0001")

    def test_update_empenho(self):
        self.authentication(self.user_data_adm)
        data = {"empenho": "2024NE0001-MOD", "descricao": "Desc Modificada", "finalidade": self.finalidade.id_finalidade}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.empenho.refresh_from_db()
        self.assertEqual(self.empenho.empenho, "2024NE0001-MOD")

    # Erro ao criar transação -> Criar testes para Transação
    def test_delete_empenho_with_children(self):
        # Cria uma transação filha
        Transacao.objects.create(
            empenho=self.empenho,
            usuario=self.user_normal,
            montante=100.00,
        )
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        print(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Empenho.objects.filter(pk=self.empenho.id_empenho).exists())


# class TipoDocumentoViewTestCase(APITestCase, PartialPaymentsTestAPI):
#     def setUp(self):
#         self.create_test_users()
#         self.url = reverse("despesas:tipos_documentos")
#         self.new_tipo = {"tipo_documento": "Fatura", "ativo": True}

#     def test_get_all_tipos_authenticated(self):
#         self.authentication(self.user_data_normal)
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#     def test_create_tipo_documento(self):
#         self.authentication(self.user_data_adm)
#         response = self.client.post(self.url, data=self.new_tipo)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#     def test_create_duplicate_tipo_documento(self):
#         self.create_basic_data()  # Cria "Nota Fiscal"
#         self.authentication(self.user_data_adm)
#         response = self.client.post(self.url, data={"tipo_documento": "Nota Fiscal"})
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# class SingleTipoDocumentoViewTestCase(APITestCase, PartialPaymentsTestAPI):
#     def setUp(self):
#         self.create_test_users()
#         self.create_basic_data()
#         self.url = reverse(
#             "despesas:single_tipo_documento",
#             kwargs={"pk": self.tipo_doc.id_tipo_documento},
#         )

#     def test_update_tipo_documento(self):
#         self.authentication(self.user_data_adm)
#         response = self.client.put(self.url, data={"tipo_documento": "NF Atualizada"})
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.tipo_doc.refresh_from_db()
#         self.assertEqual(self.tipo_doc.tipo_documento, "NF Atualizada")

#     def test_delete_tipo_documento(self):
#         # A view de delete na verdade desativa o tipo de documento (ativo=False)
#         self.authentication(self.user_data_adm)
#         response = self.client.delete(self.url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.tipo_doc.refresh_from_db()
#         self.assertFalse(self.tipo_doc.ativo)


# class TransacaoPagamentoParcialTestCase(APITestCase, PartialPaymentsTestAPI):
#     def setUp(self):
#         self.create_test_users()
#         self.create_basic_data()
#         self.url = reverse("despesas:transacoes")

#     def test_create_transacao_and_calculate_montante(self):
#         self.authentication(self.user_data_adm)

#         # 1. Adiciona um crédito
#         data_credito = {
#             "empenho_pai": self.empenho.id_empenho,
#             "tipo_documento": self.tipo_doc.id_tipo_documento,
#             "eh_credito": True,
#             "documento": "NF-001",
#             "descricao": "Crédito inicial",
#             "montante": "1000.00",
#         }
#         response = self.client.post(self.url, data=data_credito)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#         # 2. Adiciona um débito
#         data_debito = {
#             "empenho_pai": self.empenho.id_empenho,
#             "tipo_documento": self.tipo_doc.id_tipo_documento,
#             "eh_credito": False,
#             "documento": "NF-002",
#             "descricao": "Débito parcial",
#             "montante": "400.00",
#         }
#         response = self.client.post(self.url, data=data_debito)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#         # 3. Verifica o montante total do empenho
#         url_montante = reverse(
#             "despesas:total_empenho", kwargs={"pk": self.empenho.id_empenho}
#         )
#         self.authentication(self.user_data_normal)
#         response = self.client.get(url_montante)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # 1000 - 400 = 600
#         self.assertEqual(float(response.data["data"]["montante_total"]), 600.00)

#     def test_create_transacao_invalid_empenho(self):
#         self.authentication(self.user_data_adm)
#         data = {
#             "empenho_pai": 99999,  # ID inexistente
#             "tipo_documento": self.tipo_doc.id_tipo_documento,
#             "documento": "ERR-001",
#             "descricao": "Erro",
#             "montante": "100.00",
#         }
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#     def test_delete_transacao(self):
#         transacao = TransacaoPagamentoParcial.objects.create(
#             empenho_pai=self.empenho,
#             tipo_documento=self.tipo_doc,
#             eh_credito=True,
#             documento="DOC-DEL",
#             descricao="Deletar",
#             montante=100.00,
#         )
#         url_del = reverse(
#             "despesas:single_transacao", kwargs={"pk": transacao.id_transacao}
#         )
#         self.authentication(self.user_data_adm)
#         response = self.client.delete(url_del)
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertFalse(
#             TransacaoPagamentoParcial.objects.filter(pk=transacao.id_transacao).exists()
#         )

#     def test_get_transacoes_by_empenho(self):
#         TransacaoPagamentoParcial.objects.create(
#             empenho_pai=self.empenho,
#             tipo_documento=self.tipo_doc,
#             eh_credito=True,
#             documento="DOC-LIST",
#             descricao="Lista",
#             montante=50.00,
#         )
#         url_list = reverse(
#             "despesas:transacoes_by_empenho",
#             kwargs={"pk": self.empenho.id_empenho},
#         )
#         self.authentication(self.user_data_normal)
#         response = self.client.get(url_list)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertGreaterEqual(len(response.data), 1)

#     def test_create_transacao_insufficient_funds(self):
#         self.authentication(self.user_data_adm)
#         # Tenta tirar mais do que tem (montante atual é 0)
#         data = {
#             "empenho_pai": self.empenho.id_empenho,
#             "tipo_documento": self.tipo_doc.id_tipo_documento,
#             "eh_credito": False,
#             "documento": "NF-FAIL",
#             "descricao": "Sem fundo",
#             "montante": "100.00",
#         }
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("montante", response.data)

#     def test_create_transacao_with_inactive_empenho(self):
#         self.empenho.ativo = False
#         self.empenho.save()
#         self.authentication(self.user_data_adm)
#         data = {
#             "empenho_pai": self.empenho.id_empenho,
#             "tipo_documento": self.tipo_doc.id_tipo_documento,
#             "eh_credito": True,
#             "documento": "NF-INATIVO",
#             "descricao": "Teste Inativo",
#             "montante": "100.00",
#         }
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("empenho_pai", response.data)

#     def test_create_transacao_with_inactive_tipo_documento(self):
#         self.tipo_doc.ativo = False
#         self.tipo_doc.save()
#         self.authentication(self.user_data_adm)
#         data = {
#             "empenho_pai": self.empenho.id_empenho,
#             "tipo_documento": self.tipo_doc.id_tipo_documento,
#             "eh_credito": True,
#             "documento": "NF-DOC-INATIVO",
#             "descricao": "Teste Doc Inativo",
#             "montante": "100.00",
#         }
#         response = self.client.post(self.url, data=data)
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("tipo_documento", response.data)

#     def test_dynamic_balance_after_deletion(self):
#         self.authentication(self.user_data_adm)
#         # 1. Crédito 1000 (Saldo: 1000)
#         t1 = TransacaoPagamentoParcial.objects.create(
#             empenho_pai=self.empenho,
#             tipo_documento=self.tipo_doc,
#             eh_credito=True,
#             documento="T1",
#             descricao="D1",
#             montante=1000,
#         )
#         # 2. Débito 300 (Saldo: 700)
#         t2 = TransacaoPagamentoParcial.objects.create(
#             empenho_pai=self.empenho,
#             tipo_documento=self.tipo_doc,
#             eh_credito=False,
#             documento="T2",
#             descricao="D2",
#             montante=300,
#         )
#         # 3. Débito 200 (Saldo: 500)
#         t3 = TransacaoPagamentoParcial.objects.create(
#             empenho_pai=self.empenho,
#             tipo_documento=self.tipo_doc,
#             eh_credito=False,
#             documento="T3",
#             descricao="D3",
#             montante=200,
#         )

#         # Verifica saldo inicial da T3
#         url_t3 = reverse("despesas:single_transacao", kwargs={"pk": t3.id_transacao})
#         response = self.client.get(url_t3)
#         self.assertEqual(float(response.data["data"]["saldo_no_momento"]), 500.00)

#         # Deleta a T2 (Débito de 300)
#         url_t2 = reverse("despesas:single_transacao", kwargs={"pk": t2.id_transacao})
#         self.client.delete(url_t2)

#         # Verifica saldo da T3 novamente - Deve ter subido para 800 (1000 - 200)
#         response = self.client.get(url_t3)
#         self.assertEqual(float(response.data["data"]["saldo_no_momento"]), 800.00)
