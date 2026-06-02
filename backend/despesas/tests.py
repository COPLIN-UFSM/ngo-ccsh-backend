from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from usuarios.models import Usuario
from despesas.models import (
    Beneficiario,
    TipoDocumento,
    Documento,
    Subunidade,
    NaturezaFinalidade,
    TipoFinalidade,
    Finalidade,
    Transacao,
)


class DespesasTestAPI:
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


class BeneficiarioViewSetTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url_list = reverse("despesas:beneficiario-list")
        self.beneficiario = Beneficiario.objects.create(nome_beneficiario="João Silva", cpf="12345678901")

    def test_get_beneficiarios_unauthenticated(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_beneficiarios_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_beneficiario(self):
        self.authentication(self.user_data_normal)
        data = {"nome_beneficiario": "Maria Souza", "cpf": "98765432100"}
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nome_beneficiario"], "Maria Souza")

    def test_create_beneficiario_bad_request(self):
        self.authentication(self.user_data_normal)
        data = {"cpf": "98765432100"}  # Missing nome_beneficiario
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_beneficiario(self):
        self.authentication(self.user_data_normal)
        url_detail = reverse("despesas:beneficiario-detail", kwargs={"pk": self.beneficiario.pk})
        data = {"nome_beneficiario": "João Silva Editado"}
        response = self.client.patch(url_detail, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nome_beneficiario"], "João Silva Editado")

    def test_delete_beneficiario(self):
        self.authentication(self.user_data_normal)
        url_detail = reverse("despesas:beneficiario-detail", kwargs={"pk": self.beneficiario.pk})
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TipoDocumentoViewSetTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url_list = reverse("despesas:tipos_documentos-list")
        self.tipo_doc = TipoDocumento.objects.create(tipo_documento="Nota Fiscal")

    def test_get_tipos_documento_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tipo_documento(self):
        self.authentication(self.user_data_normal)
        data = {"tipo_documento": "Fatura"}
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tipo_documento_bad_request(self):
        self.authentication(self.user_data_normal)
        data = {}  # Missing tipo_documento
        response = self.client.post(self.url_list, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DocumentoViewSetTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url_list = reverse("despesas:documentos-list")
        self.tipo_doc = TipoDocumento.objects.create(tipo_documento="Recibo")
        self.transacao = Transacao.objects.create(usuario=self.user_normal)
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


class SubunidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:subunidades")
        self.subunidade = Subunidade.objects.create(subunidade="Departamento A", grupo="DEPTO")

    def test_get_subunidades(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_subunidade_as_admin(self):
        self.authentication(self.user_data_adm)
        data = {"subunidade": "Curso X", "grupo": "CURSOS"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_subunidade_as_normal_user_fails(self):
        self.authentication(self.user_data_normal)
        data = {"subunidade": "Curso Y", "grupo": "CURSOS"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_subunidade_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"grupo": "CURSOS"}  # Missing subunidade
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleSubunidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.subunidade = Subunidade.objects.create(subunidade="Departamento B", grupo="DEPTO")
        self.url = reverse("despesas:single_subunidade", kwargs={"pk": self.subunidade.pk})

    def test_get_single_subunidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subunidade"], "Departamento B")

    def test_get_nonexistent_subunidade(self):
        self.authentication(self.user_data_adm)
        url = reverse("despesas:single_subunidade", kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_put_subunidade_as_admin(self):
        self.authentication(self.user_data_adm)
        data = {"subunidade": "Departamento B Editado", "grupo": "DEPTO"}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_subunidade_as_admin(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class NaturezaFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:tipos_despesas")

    def test_get_naturezas(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_natureza(self):
        self.authentication(self.user_data_adm)
        data = {"natureza_finalidade": "Material de Consumo"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_natureza_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleNaturezaFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Equipamentos")
        self.url = reverse("despesas:single_natureza_finalidade", kwargs={"pk": self.natureza.pk})

    def test_get_single_natureza(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_natureza(self):
        self.authentication(self.user_data_adm)
        data = {"natureza_finalidade": "Equipamentos de TI"}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_natureza(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_natureza_with_children(self):
        self.authentication(self.user_data_adm)
        tipo = TipoFinalidade.objects.create(tipo_finalidade="Tipo Teste 1")
        Finalidade.objects.create(
            natureza_finalidade=self.natureza,
            tipo_finalidade=tipo,
            modalidade="DESPESA",
            finalidade="Finalidade com filho",
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TipoFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:subtipo_finalidade")

    def test_get_tipos_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {"tipo_finalidade": "Pesquisa"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SingleTipoFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.tipo_finalidade = TipoFinalidade.objects.create(tipo_finalidade="Extensão")
        self.url = reverse("despesas:single_subtipo_finalidade", kwargs={"pk": self.tipo_finalidade.pk})

    def test_get_single_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {"tipo_finalidade": "Extensão e Cultura"}
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_tipo_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_tipo_finalidade_with_children(self):
        self.authentication(self.user_data_adm)
        natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Nat Teste")
        Finalidade.objects.create(
            natureza_finalidade=natureza,
            tipo_finalidade=self.tipo_finalidade,
            modalidade="DESPESA",
            finalidade="Finalidade com filho 2",
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FinalidadesViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.url = reverse("despesas:finalidades")
        self.natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Ensino")
        self.tipo = TipoFinalidade.objects.create(tipo_finalidade="Monitoria")

    def test_get_finalidades_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_finalidades_authenticated(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {
            "natureza_finalidade": self.natureza.pk,
            "tipo_finalidade": self.tipo.pk,
            "modalidade": "DESPESA",
            "finalidade": "Bolsa de Monitoria",
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_finalidade_bad_request(self):
        self.authentication(self.user_data_adm)
        data = {"modalidade": "DESPESA"}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SingleFinalidadeViewTestCase(APITestCase, DespesasTestAPI):
    def setUp(self):
        self.create_test_users()
        self.natureza = NaturezaFinalidade.objects.create(natureza_finalidade="Inovação")
        self.tipo = TipoFinalidade.objects.create(tipo_finalidade="Projeto")
        self.finalidade = Finalidade.objects.create(
            natureza_finalidade=self.natureza,
            tipo_finalidade=self.tipo,
            modalidade="DESPESA",
            finalidade="Projeto X",
        )
        self.url = reverse("despesas:single_finalidades", kwargs={"pk": self.finalidade.pk})

    def test_get_single_finalidade(self):
        self.authentication(self.user_data_normal)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_finalidade(self):
        self.authentication(self.user_data_adm)
        data = {
            "natureza_finalidade": self.natureza.pk,
            "tipo_finalidade": self.tipo.pk,
            "modalidade": "DESPESA",
            "finalidade": "Projeto X Editado",
        }
        response = self.client.put(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_finalidade(self):
        self.authentication(self.user_data_adm)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
