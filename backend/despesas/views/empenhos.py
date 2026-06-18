from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils import response

from despesas.serializers import *


class TransacoesByEmpenho(APIView):
    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]
        try:
            empenho = Empenho.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrado.")

            transacoes = Transacao.objects.filter(empenho=empenho)
            serializer = TransacaoSerializer(transacoes, many=True)

            return Response(
                data=serializer.data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return response.error_server(e)


class EmpenhoView(APIView):
    def get(self, request):
        try:
            empenhos = Empenho.objects.all()
            serializer = EmpenhoSerializer(empenhos, many=True)
            return response.success_data(serializer.data)
        except Exception as e:
            return response.error_server(e)

    def post(self, request):

        try:
            serializer = EmpenhoSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer)

            serializer.save()
            return response.created("Empenho adicionado com sucesso.")
        except Exception as e:
            return response.error_server(e)


class SingleEmpenhoView(APIView):
    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            empenho = Empenho.objects.get(pk=pk)
            serializer = EmpenhoSerializer(empenho)
            return response.success_data(serializer.data)
        except ObjectDoesNotExist:
            return response.not_found("Empenho não encontrado.")
        except Exception as e:
            return response.error_server(e)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            empenho = Empenho.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrado.")

            serializer = EmpenhoSerializer(instance=empenho, data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Empenho atualizado com sucesso.")

        except Exception as e:
            return response.error_server(e)

    # Nesse caso pode deletar mesmo, pois aqui o empenho não tem nenhum filho e pode ser recriado posteriormente.
    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            empenho = Empenho.objects.filter(pk=pk).first()
            if not empenho:
                return response.not_found("Empenho não encontrada.")

            related_transacoes = Transacao.objects.filter(empenho=pk)
            if len(related_transacoes) > 0:
                return response.bad_request(f"Não é possível remover um empenho que tenha filhos")

            empenho.delete()
            return response.success_no_content()

        except Exception as e:
            return response.error_server()
