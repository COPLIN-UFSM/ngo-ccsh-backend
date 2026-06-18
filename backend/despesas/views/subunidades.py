from rest_framework.response import Response
from rest_framework import status

from despesas.serializers import *
from rest_framework.views import APIView
from utils import response
from utils.pagination import PaginationWithSize


class SubunidadeView(APIView):

    def get(self, request):
        try:
            queryset = Subunidade.objects.filter(ativo=True)

            paginator = PaginationWithSize()
            page = paginator.paginate_queryset(queryset, request, self)
            serializer = SubunidadeSerializer(queryset, many=True)
            print(serializer.data)
            if page is not None:
                return paginator.get_paginated_response(serializer.data)

            return response.success_data(serializer.data)

        except Exception as e:
            return response.error_server(e)

    def post(self, request):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            serializer = SubunidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()
            return response.success("Subunidade adicionada com sucesso.")
        except Exception as e:
            return response.error_server(e)


class SingleSubunidadeView(APIView):
    def get(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            data = Subunidade.objects.filter(pk=pk, ativo=True).first()
            if not data:
                return response.not_found("Subunidade não encontrada.")
            serializer = SubunidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return response.error_server(e)

    def put(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            subunidade = Subunidade.objects.filter(pk=pk).first()
            if not subunidade:
                return response.not_found("Subunidade não encontrada.")

            serializer = SubunidadeSerializer(instance=subunidade, data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Subunidade alterada com sucesso.")

        except Exception as e:
            return response.error_server()

    def delete(self, request, *args, **kwargs):
        pk = kwargs["pk"]

        try:
            subunidade = Subunidade.objects.filter(pk=pk, ativo=True).first()
            if not subunidade:
                return response.not_found("Subunidade não encontrada.")
            subunidade.delete()

            return response.success("Subunidade deletada com sucesso.")

        except Exception as e:
            return response.error_server()
