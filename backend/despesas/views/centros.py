from rest_framework import serializers, viewsets

from despesas.serializers_saldos import (
    CentroComSaldoSerializer,
    UnidadeComSaldoSerializer,
)
from entidades.models import Centro, Unidade


class SaldoQuerySerializer(serializers.Serializer):
    ano_fiscal = serializers.IntegerField(min_value=1, max_value=32767)


class _SaldoViewSetMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        query = SaldoQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        context["ano_fiscal"] = query.validated_data["ano_fiscal"]
        return context


class CentroSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Centro.objects.all().order_by("id_centro_interno")
    serializer_class = CentroComSaldoSerializer


class UnidadeSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Unidade.objects.all().select_related(
        "centro", "tipo_unidade", "situacao_unidade"
    ).order_by("id_unidade_interna")
    serializer_class = UnidadeComSaldoSerializer
