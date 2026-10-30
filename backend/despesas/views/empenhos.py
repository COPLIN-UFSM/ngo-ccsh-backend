from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter

from despesas.filters import EmpenhoFilterSet
from despesas.models import Empenho
from despesas.serializers import EmpenhoSerializer
from despesas.views.ativoUtil import AtivoListDefaultMixin


class EmpenhoViewSet(AtivoListDefaultMixin, viewsets.ModelViewSet):
    queryset = Empenho.objects.select_related(
        "centro", "natureza", "finalidade", "empenho_origem"
    )
    serializer_class = EmpenhoSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = EmpenhoFilterSet
    ordering_fields = ["id_empenho", "numero_empenho", "ano_fiscal"]
    ordering = ["-ano_fiscal", "numero_empenho"]
    http_method_names = ["get", "post", "patch", "delete"]
