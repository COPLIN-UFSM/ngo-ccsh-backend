from despesas.filters import (
    FinalidadeFilterSet,
    GrupoFinalidadeFilterSet,
    NaturezaFinalidadeFilterSet,
)
from despesas.models import Finalidade, GrupoFinalidade, NaturezaFinalidade
from despesas.serializers import (
    FinalidadeSerializer,
    GrupoFinalidadeSerializer,
    NaturezaFinalidadeSerializer,
)
from despesas.views.ativoUtil import AtivoListDefaultMixin
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet


class NaturezaFinalidadeViewSet(AtivoListDefaultMixin, ModelViewSet):
    queryset = NaturezaFinalidade.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]

    ordering_fields = ["id_natureza_finalidade", "natureza_finalidade"]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    serializer_class = NaturezaFinalidadeSerializer
    filterset_class = NaturezaFinalidadeFilterSet


class GrupoFinalidadeViewSet(AtivoListDefaultMixin, ModelViewSet):
    queryset = GrupoFinalidade.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]
    ordering_fields = ["id_grupo_finalidade", "grupo_finalidade"]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    serializer_class = GrupoFinalidadeSerializer
    filterset_class = GrupoFinalidadeFilterSet


class FinalidadeViewSet(AtivoListDefaultMixin, ModelViewSet):
    queryset = (
        Finalidade.objects.all()
        .select_related("natureza_finalidade", "grupo_finalidade")
        .prefetch_related("tipodocumentoparafinalidade_set")
    )
    http_method_names = ["get", "post", "patch", "delete"]
    ordering_fields = ["id_finalidade", "finalidade"]
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    serializer_class = FinalidadeSerializer
    filterset_class = FinalidadeFilterSet
