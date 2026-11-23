from decimal import Decimal

from despesas.serializers_saldos import (
    CentroComSaldoSerializer,
    UnidadeComSaldoSerializer,
)
from despesas import saldos
from despesas.models import Natureza
from entidades.models import Centro, Unidade
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
    def get_serializer_context(self):
        context = super().get_serializer_context()
        query = SaldoQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        context["ano_fiscal"] = query.validated_data["ano_fiscal"]
        context["saldo_minimo"] = query.validated_data.get("saldo_minimo")
        return context

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        query = SaldoQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        saldo_minimo = query.validated_data.get("saldo_minimo")
        if saldo_minimo is None:
            return queryset

        ano_fiscal = query.validated_data["ano_fiscal"]
        naturezas = Natureza.objects.filter(ativo=True).values_list("pk", flat=True)
        ids = [
            objeto.pk
            for objeto in queryset
            if self._tem_saldo_maior_que(
                objeto.pk,
                ano_fiscal,
                saldo_minimo,
                naturezas,
            )
        ]
        return queryset.filter(pk__in=ids)


class CentroSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Centro.objects.all().order_by("id_centro_interno")
    serializer_class = CentroComSaldoSerializer

    def _tem_saldo_maior_que(
        self,
        centro_id,
        ano_fiscal,
        saldo_minimo,
        naturezas,
    ):
        return any(
            saldos.total_centro(centro_id, ano_fiscal, natureza_id) > saldo_minimo
            for natureza_id in naturezas
        )


class UnidadeSaldoViewSet(_SaldoViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = (
        Unidade.objects.all()
        .select_related("centro", "tipo_unidade", "situacao_unidade")
        .order_by("id_unidade_interna")
    )
    serializer_class = UnidadeComSaldoSerializer

    def _tem_saldo_maior_que(
        self,
        unidade_id,
        ano_fiscal,
        saldo_minimo,
        naturezas,
    ):
        return any(
            saldos.saldo_unidade(unidade_id, ano_fiscal, natureza_id) > saldo_minimo
            for natureza_id in naturezas
        )
