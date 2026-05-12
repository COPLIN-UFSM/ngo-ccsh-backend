from django.shortcuts import render
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from partial_payments.models import *
from partial_payments.serializers import *
from utils import response
from django.db.models import F

# Create your views here.

# Empenho Ok
# Single Empenho OK - Pode deletar se não tem nenhuma transação filho, pq assim não afeta nada... -> Só será utilizado em algum tipo de erro de criação, poderia ser resolvido tbm apenas dando update.
from rest_framework.response import Response
from rest_framework import status


class TransacoesByEmpenho(APIView):
    def get(self, request, pk):
        try:
            empenho = EmpenhoPagamentoParcial.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrado.")
            transacoes = TransacaoPagamentoParcial.objects.filter(empenho_pai=empenho)
            serializer = TransacaoPagamentoParcialSerializer(transacoes, many=True)

            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return response.error_server(e)


class EmpenhoMontante(APIView):
    def get(self, request, pk):
        try:
            empenho = EmpenhoPagamentoParcial.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrado.")

            montante_total = empenho.montante
            return Response(
                data={"data": {"montante_total": montante_total}},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return response.error_server(e)


class EmpenhoView(APIView):
    def get(self, request):
        try:
            empenhos = EmpenhoPagamentoParcial.objects.all()
            serializer = EmpenhoPagamentoParcialSerializer(empenhos, many=True)
            return response.success_data(serializer.data)
        except Exception as e:
            return response.error_server(e)

    def post(self, request):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            serializer = EmpenhoPagamentoParcialSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer)

            serializer.save()
            return response.created("Empenho adicionado com sucesso.")
        except Exception as e:
            return response.error_server(e)


class SingleEmpenhoView(APIView):
    def get(self, request, pk):
        try:
            empenho = EmpenhoPagamentoParcial.objects.get(pk=pk)
            serializer = EmpenhoPagamentoParcialSerializer(empenho)
            return response.success_data(serializer.data)
        except ObjectDoesNotExist:
            return response.not_found("Empenho não encontrado.")
        except Exception as e:
            return response.error_server(e)

    def put(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            empenho = EmpenhoPagamentoParcial.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrado.")

            serializer = EmpenhoPagamentoParcialSerializer(
                instance=empenho, data=request.data
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Empenho atualizado com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            empenho = EmpenhoPagamentoParcial.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrada.")

            related_transacoes = TransacaoPagamentoParcial.objects.filter(
                empenho_pai=pk
            )
            if len(related_transacoes) > 0:
                return response.bad_request(
                    f"Não é possível remover um empenho que tenha filhos"
                )

            empenho.delete()
            return response.success_no_content()

        except Exception as e:
            return response.error_server()


class TipoDocumentoPagamentoParcialView(APIView):

    def get(self, request):
        tipos_transacoes = TipoDocumentoPagamentoParcial.objects.all()
        serializer = TipoDocumentoPagamentoParcialSerializer(
            tipos_transacoes, many=True
        )
        return response.success_data(serializer.data)

    def post(self, request):
        if not request.user.is_superuser:
            return response.not_admin_user()
        try:
            serializer = TipoDocumentoPagamentoParcialSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.created("Tipo de Documento adicionado com sucesso.")
        except:
            return response.error_server()


class SingleTipoDocumentoPagamentoParcialView(APIView):

    def get(self, request, pk):
        try:
            tipo_documento = TipoDocumentoPagamentoParcial.objects.filter(pk=pk).first()
            if not tipo_documento:
                return response.not_found("Tipo de Documento não encontrado")
            serializer = TipoDocumentoPagamentoParcialSerializer(tipo_documento)
            return response.success_data(serializer.data)
        except:
            return response.error_server()

    def put(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            tipo_documento = TipoDocumentoPagamentoParcial.objects.filter(pk=pk).first()
            if not tipo_documento:
                return response.not_found("Tipo de Documento não encontrado.")

            serializer = TipoDocumentoPagamentoParcialSerializer(
                instance=tipo_documento, data=request.data
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Tipo de Documento alterado com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            tipo_documento = TipoDocumentoPagamentoParcial.objects.filter(pk=pk).first()
            if not tipo_documento:
                return response.not_found("Tipo de Documento não encontrado.")

            tipo_documento.ativo = False
            tipo_documento.save()

            return response.success("Tipo de Documento desativado com sucesso.")

        except Exception as e:
            return response.error_server()


class TransacaoPagamentoParcialView(APIView):

    def get(self, request):
        try:
            transacoes = TransacaoPagamentoParcial.objects.all()
            serializer = TransacaoPagamentoParcialSerializer(transacoes, many=True)
            return response.success_data(serializer.data)
        except:
            return response.error_server()

    def post(self, request):
        if not request.user.is_superuser:
            return response.not_admin_user()
        try:
            data = request.data

            serializer = TransacaoPagamentoParcialSerializer(data=data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.created("Transação adicionada com sucesso.")
        except Exception as e:
            return response.error_server(e)


class SingleTransacaoPagamentoParcialView(APIView):

    def get(self, request, pk):
        try:
            transacao = TransacaoPagamentoParcial.objects.filter(pk=pk).first()
            if not transacao:
                return response.not_found("Transação não encontrada.")
            serializer = TransacaoPagamentoParcialSerializer(transacao)
            return response.success_data(serializer.data)
        except:
            return response.error_server()

    def put(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            transacao = TransacaoPagamentoParcial.objects.filter(pk=pk).first()
            if not transacao:
                return response.not_found("Transação não encontrada.")

            serializer = TransacaoPagamentoParcialSerializer(
                instance=transacao, data=request.data
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)

            serializer.save()
            return response.success(f"Transação alterada com sucesso.")

        except Exception as e:
            return response.error_server(e)

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            transacao = TransacaoPagamentoParcial.objects.filter(pk=pk).first()
            if not transacao:
                return response.not_found("Transação não encontrada.")

            transacao.delete()

            return response.success_no_content()

        except Exception as e:
            return response.error_server()


# Empenho
# Documento

# Transacao - A própria regra.
# Tipo Documento - Documento com seu valor
# Tipo Transaco - Crédito ou débito.
# Empenho - Empenho inicial
