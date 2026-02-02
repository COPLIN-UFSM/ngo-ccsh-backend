from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from .models import Transacoes
from django.db.models import Avg, Count, Min, Sum

def home(request):
    return Response(
        {"detail": "Por enquanto ta tudo tranquilo."}, status=status.HTTP_200_OK
    )


def allTransacoesView(request):
    transacoes = Transacoes.objects.values('subunidade_executora__subunidade').annotate(total_montante=Sum('montante'))
    
