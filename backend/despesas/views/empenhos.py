from rest_framework import viewsets, status
from despesas.models import Empenho
from despesas.serializers import EmpenhoSerializer

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from despesas.views.ativoUtil import AtivoListDefaultMixin


class EmpenhoViewSet(AtivoListDefaultMixin, viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]

    ordering_fields = ["id_transacao", "data_criacao"]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    serializer_class = EmpenhoSerializer
    filterset_fields = ["data_criacao"]
