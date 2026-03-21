from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status

from transactions.serializers import FinalidadesSerializer
from .models import Transacoes
from django.db.models import Avg, Count, Min, Sum
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated


def home(request):
    return Response(
        {"detail": "Por enquanto ta tudo tranquilo."}, status=status.HTTP_200_OK
    )


def allTransacoesView(request):
    transacoes = Transacoes.objects.values("subunidade_executora__subunidade").annotate(
        total_montante=Sum("montante")
    )


class FinalidadesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"detail": "Apenas administradores podem adicionar finalidades"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        serializer = FinalidadesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(
            {"detail": "Finalidade adicionada com sucesso."}, status=status.HTTP_200_OK
        )
