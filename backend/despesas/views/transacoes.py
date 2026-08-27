from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from despesas.models import Transacao, StatusTransacao
from despesas.serializers import TransacaoSerializer, StatusTransacaoSerializer


class TransacoesViewSet(viewsets.ModelViewSet):
    queryset = Transacao.objects.all()
    serializer_class = TransacaoSerializer
    http_method_names = ['get', 'post', 'patch']


class StatusTransacaoViewSet(viewsets.ModelViewSet):
    queryset = StatusTransacao.objects.all()
    serializer_class = StatusTransacaoSerializer
    http_method_names = ['get']
