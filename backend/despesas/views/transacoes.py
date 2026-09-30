from rest_framework import viewsets
from rest_framework.exceptions import NotFound

from despesas.models import Transacao, StatusTransacao, VersaoTransacao
from despesas.serializers import TransacaoSerializer, StatusTransacaoSerializer, VersaoTransacaoSerializer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

class TransacoesViewSet(viewsets.ModelViewSet):
    queryset = Transacao.objects.all()
    http_method_names = ['get', 'post', 'patch']

    ordering_fields = ['id_transacao', 'data_criacao']
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    serializer_class = TransacaoSerializer
    filterset_fields = ['data_criacao']


class StatusTransacaoViewSet(viewsets.ModelViewSet):
    queryset = StatusTransacao.objects.all()
    serializer_class = StatusTransacaoSerializer
    http_method_names = ['get']

class VersoesTransacaoViewSet(viewsets.ModelViewSet):
    queryset = VersaoTransacao.objects.all()
    serializer_class = VersaoTransacaoSerializer
    http_method_names = ['get']
    filter_backends = (DjangoFilterBackend, OrderingFilter)

    ordering_fields = ['numero_versao', 'data_criacao']
    ordering=['-numero_versao']
    filterset_fields = ['numero_versao', 'data_criacao']

    def get_queryset(self):
        transacao_id = self.kwargs.get('transacao_pk')
        versao_transacao = VersaoTransacao.objects.filter(transacao=transacao_id)
        if not versao_transacao:
            raise NotFound(detail='Transação não encontrada')
        return versao_transacao