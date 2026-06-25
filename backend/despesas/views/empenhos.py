from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from utils import response
from despesas.serializers import *
from utils.pagination import PaginationWithSize


class EmpenhoView(APIView):
    def get(self, request):
        try:
            queryset = Empenho.objects.all()
            paginator = PaginationWithSize()

            page = paginator.paginate_queryset(queryset, request, view=self)
            serializer = EmpenhoSerializer(queryset, many=True)

            if page is not None:
                return paginator.get_paginated_response(serializer.data)

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

            empenho.ativo = False
            empenho.save()

            return response.success_no_content()

        except Exception:
            return response.error_server()
