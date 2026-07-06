from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from despesas.models import Transacao, StatusTransacao
from despesas.serializers import TransacaoSerializer, StatusTransacaoSerializer


class TransacoesViewSet(viewsets.ModelViewSet):
    queryset = Transacao.objects.all()
    serializer_class = TransacaoSerializer

    def get_permissions(self):
        return [IsAuthenticated()]


class StatusTransacaoViewSet(viewsets.ModelViewSet):
    queryset = StatusTransacao.objects.all()
    serializer_class = StatusTransacaoSerializer

    def get_permissions(self):
        return [IsAuthenticated()]
