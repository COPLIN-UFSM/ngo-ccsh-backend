from math import e

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework import status

from transactions.serializers import *
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from utils import response


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    return Response(
        {"detail": "Por enquanto ta tudo tranquilo."}, status=status.HTTP_200_OK
    )

# Existem apenas dois tipo de Despesa: 'custeio' e 'capital', então não há necessidade de um CRUD.
class TipoDespesaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipos_despesa = TipoDespesa.objects.all()
        serializer = TipoDespesaSerializer(tipos_despesa, many=True)
        return Response(serializer.data)


class SubtipoFinalidadeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subtipos = CategoriaFinalidade.objects.all()
        serializer = CategoriaFinalidadeSerializer(subtipos, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_superuser:
            return response.not_admin_user()
        try:
            serializer = CategoriaFinalidadeSerializer(data=request.data)
            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Subtipo de Finalidade adicionado com sucesso.")

        except Exception as e:
            print(e)
            return response.error_server()


class SingleSubtipoFinalidadeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            data = CategoriaFinalidade.objects.filter(pk=pk).first()
            if not data:
                return response.not_found("Subtipo de Finalidade não encontrada.")

            serializer = CategoriaFinalidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return response.error_server()

    def patch(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            subtipo_finalidade = CategoriaFinalidade.objects.filter(pk=pk).first()
            if not subtipo_finalidade:
                return response.not_found("Subtipo de Finalidade não encontrada.")

            serializer = CategoriaFinalidadeSerializer(
                instance=subtipo_finalidade, data=request.data, partial=True
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Subtipo de Finalidade alterado com sucesso.")

        except Exception as e:
            return response.error_server()

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            subtipo_finalidade = CategoriaFinalidade.objects.filter(pk=pk).first()
            if not subtipo_finalidade:
                return response.not_found("Subtipo de Finalidade não encontrada.")

            finalidades = Finalidade.objects.filter(subtipo_finalidade=pk)
            if len(finalidades) > 0:
                return response.bad_request(
                    "Não é possível remover um subtipo que tenha filhos"
                )

            subtipo_finalidade.delete()

            return response.success("Finalidade deletada com sucesso.")

        except Exception as e:
            return response.error_server()


class SingleFinalidadeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            data = Finalidade.objects.filter(pk=pk).first()
            if not data:
                return response.not_found("Finalidade não encontrada.")
            serializer = FinalidadeSerializer(data)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return response.error_server()

    def patch(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            finalidade = Finalidade.objects.filter(pk=pk).first()
            if not finalidade:
                return response.not_found("Finalidade não encontrada.")

            serializer = FinalidadeSerializer(
                instance=finalidade, data=request.data, partial=True
            )

            if not serializer.is_valid():
                return response.serializer_errors(serializer)
            serializer.save()

            return response.success("Finalidade alterada com sucesso.")

        except Exception as e:
            return response.error_server()

    def delete(self, request, pk):
        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            finalidade = Finalidade.objects.filter(pk=pk).first()
            if not finalidade:
                return response.not_found("Finalidade não encontrada.")
            finalidade.delete()

            return response.success("Finalidade deletada com sucesso.")

        except Exception as e:
            return response.error_server()


class FinalidadesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Finalidade.objects.all()
        serializer = FinalidadeSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        if not request.user.is_superuser:
            return response.not_admin_user()

        try:
            serializer = FinalidadeSerializer(data=request.data)

            if not serializer.is_valid():
                return response.serializer_errors(serializer=serializer)

            serializer.save()
            return response.success("Finalidade criada com sucesso.")

        except:
            return response.error_server()
