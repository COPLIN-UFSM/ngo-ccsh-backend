from decimal import Decimal

from despesas import saldos
from despesas.serializers_saldos import (
    CentroComSaldoSerializer,
)
from drf_spectacular.utils import extend_schema
from entidades.filters import CentroSaldoFilterSet
from entidades.models import Centro
from rest_framework import serializers, viewsets


class SaldoQuerySerializer(serializers.Serializer):
    ano_fiscal = serializers.IntegerField(min_value=1, max_value=32767)
    saldo_minimo = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        min_value=Decimal("0"),
    )


class _SaldoViewSetMixin:
    @extend_schema(parameters=[SaldoQuerySerializer])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def _saldo_query_data(self):
        if not hasattr(self, "_validated_saldo_query_data"):
            query = SaldoQuerySerializer(data=self.request.query_params)
            query.is_valid(raise_exception=True)
            self._validated_saldo_query_data = query.validated_data
        return self._validated_saldo_query_data

    def get_serializer_context(self):
        context = super().get_serializer_context()
        query_data = self._saldo_query_data()
        context["ano_fiscal"] = query_data["ano_fiscal"]
        context["saldo_minimo"] = query_data.get("saldo_minimo")
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        query_data = self._saldo_query_data()
        saldo_minimo = query_data.get("saldo_minimo")
        if saldo_minimo is None:
            return queryset

        return self._filtrar_por_saldo_minimo(
            queryset, query_data["ano_fiscal"], saldo_minimo
        )

    def _filtrar_por_saldo_minimo(self, queryset, ano_fiscal, saldo_minimo):
        raise NotImplementedError


class CentroSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Centro.objects.all().order_by("id_centro_interno")
    serializer_class = CentroComSaldoSerializer
    filterset_class = CentroSaldoFilterSet

    def _filtrar_por_saldo_minimo(self, queryset, ano_fiscal, saldo_minimo):
        return saldos.filtrar_centros_por_saldo_minimo(
            queryset, ano_fiscal, saldo_minimo
        )
