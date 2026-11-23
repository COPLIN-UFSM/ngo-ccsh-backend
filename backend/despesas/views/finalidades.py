from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet

from despesas.filters import (
    FinalidadeFilterSet,
    GrupoFinalidadeFilterSet,
    NaturezaFilterSet,
)
from despesas.models import Finalidade, GrupoFinalidade, Natureza
from despesas.serializers import (
    FinalidadeSerializer,
    GrupoFinalidadeSerializer,
    NaturezaSerializer,
)
from despesas.views.ativoUtil import AtivoListDefaultMixin


class NaturezaViewSet(AtivoListDefaultMixin, ModelViewSet):
    queryset = Natureza.objects.all().order_by("id_natureza")
    serializer_class = NaturezaSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = NaturezaFilterSet
    ordering_fields = ["id_natureza", "nome"]


class GrupoFinalidadeViewSet(AtivoListDefaultMixin, ModelViewSet):
    queryset = GrupoFinalidade.objects.all().order_by("id_grupo_finalidade")
    serializer_class = GrupoFinalidadeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = GrupoFinalidadeFilterSet
    ordering_fields = ["id_grupo_finalidade", "nome"]


class FinalidadeViewSet(AtivoListDefaultMixin, ModelViewSet):
    queryset = (
        Finalidade.objects.select_related("natureza", "grupo")
        .prefetch_related("tipodocumentoparafinalidade_set__tipo_documento")
        .order_by("id_finalidade")
    )
    serializer_class = FinalidadeSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = FinalidadeFilterSet
    ordering_fields = ["id_finalidade", "nome"]
